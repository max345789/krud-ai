from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.core.config import settings


@dataclass
class ChatGeneration:
    text: str
    command_proposals: list[dict[str, str]]
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int


SYSTEM_PROMPT = """
You are Krud AI, a terminal agent planner.
Return strict JSON with this shape:
{
  "text": "short user-facing reply",
  "command_proposals": [
    {
      "command": "shell command",
      "rationale": "why it helps",
      "risk": "low|medium|high"
    }
  ]
}

Rules:
- Never claim a command already ran.
- Prefer proposing inspection commands before write commands.
- Mark destructive commands as high risk.
- If no command is needed, return an empty list.
- Keep text concise and practical.
""".strip()


def generate_reply(message: str, history: list[dict[str, object]], cwd: str | None = None) -> ChatGeneration:
    if not settings.openai_api_key:
        return heuristic_reply(message)

    try:
        return call_openai_chat(message=message, history=history, cwd=cwd)
    except Exception:
        return heuristic_reply(message)


_RESPONSES_API_MODELS = {"codex-mini-latest", "o3", "o4-mini"}


def _is_responses_api(model: str) -> bool:
    return model in _RESPONSES_API_MODELS


def call_openai_chat(message: str, history: list[dict[str, object]], cwd: str | None = None) -> ChatGeneration:
    if _is_responses_api(settings.openai_model):
        return call_openai_responses(message=message, history=history, cwd=cwd)

    endpoint = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cwd:
        messages.append(
            {
                "role": "system",
                "content": f"Current working directory for the terminal context: {cwd}",
            }
        )

    for item in history[-8:]:
        role = str(item["role"])
        if role in {"user", "assistant"}:
            messages.append({"role": role, "content": str(item["content"])})

    messages.append({"role": "user", "content": message})

    response = httpx.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openai_model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=settings.openai_timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    usage = payload.get("usage", {})

    return ChatGeneration(
        text=str(parsed.get("text", "")).strip() or "I have a response ready.",
        command_proposals=normalize_command_proposals(parsed.get("command_proposals", [])),
        provider="openai",
        model=settings.openai_model,
        prompt_tokens=int(usage.get("prompt_tokens", 0)),
        completion_tokens=int(usage.get("completion_tokens", 0)),
    )


def call_openai_responses(message: str, history: list[dict[str, object]], cwd: str | None = None) -> ChatGeneration:
    """Call the OpenAI Responses API (used by codex-mini-latest, o3, o4-mini)."""
    endpoint = f"{settings.openai_base_url.rstrip('/')}/responses"

    system = SYSTEM_PROMPT
    if cwd:
        system += f"\n\nCurrent working directory: {cwd}"

    input_messages: list[dict[str, str]] = []
    for item in history[-8:]:
        role = str(item["role"])
        if role in {"user", "assistant"}:
            input_messages.append({"role": role, "content": str(item["content"])})
    input_messages.append({"role": "user", "content": message})

    response = httpx.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openai_model,
            "instructions": system,
            "input": input_messages,
            "text": {"format": {"type": "json_object"}},
        },
        timeout=settings.openai_timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["output"][0]["content"][0]["text"]
    parsed = json.loads(content)
    usage = payload.get("usage", {})

    return ChatGeneration(
        text=str(parsed.get("text", "")).strip() or "I have a response ready.",
        command_proposals=normalize_command_proposals(parsed.get("command_proposals", [])),
        provider="openai",
        model=settings.openai_model,
        prompt_tokens=int(usage.get("input_tokens", 0)),
        completion_tokens=int(usage.get("output_tokens", 0)),
    )


def heuristic_reply(message: str) -> ChatGeneration:
    lowered = message.lower()
    proposals: list[dict[str, str]] = []

    if "pwd" in lowered or "where am i" in lowered:
        proposals.append(
            {
                "command": "pwd",
                "rationale": "Show the current working directory before taking further action.",
                "risk": "low",
            }
        )
    if "list files" in lowered or "ls" in lowered or "show files" in lowered:
        proposals.append(
            {
                "command": "ls -la",
                "rationale": "Inspect the current directory contents.",
                "risk": "low",
            }
        )
    if "git status" in lowered:
        proposals.append(
            {
                "command": "git status --short --branch",
                "rationale": "Check repository state before making changes.",
                "risk": "low",
            }
        )
    if "delete" in lowered or "rm " in lowered:
        proposals.append(
            {
                "command": "printf 'Refusing to auto-propose destructive commands without more context.\\n'",
                "rationale": "Avoid destructive shell actions without clear scope.",
                "risk": "high",
            }
        )

    reply = (
        "I found one or more terminal actions that would help. Review the command proposals below and approve only the ones you want me to run."
        if proposals
        else "I can help from the terminal. Describe the task, and if local inspection is needed I will return explicit command proposals for approval."
    )

    return ChatGeneration(
        text=reply,
        command_proposals=proposals,
        provider="heuristic",
        model="rules",
        prompt_tokens=max(1, len(message) // 4),
        completion_tokens=max(1, len(reply) // 4),
    )


ORG_SYSTEM_PROMPT = """
You are Krud AI, a project hygiene assistant for indie developers.
Analyse the project snapshot and return strict JSON with this shape:
{
  "stack": "detected stack — e.g. Node.js, Python, Node.js + Python, Rust",
  "summary": "1-2 sentence description of what this project looks like and its current hygiene state",
  "actions": [
    {
      "action_type": "command" | "create_file" | "create_dir",
      "path": "relative path (required for create_file and create_dir, omit for command)",
      "content": "full file content as a string (required for create_file only)",
      "command": "shell command string (required for command only)",
      "rationale": "why this helps",
      "risk": "low|medium|high"
    }
  ]
}

Rules:
- Detect stack from hint filenames: package.json → Node.js, requirements.txt/pyproject.toml/setup.py → Python, Cargo.toml → Rust, go.mod → Go, pom.xml/build.gradle → Java
- If no .gitignore exists, propose creating one tailored to the detected stack (action_type: create_file, path: .gitignore). Include OS files, editor files, and stack-specific ignores.
- If no README.md exists, propose creating a minimal one with a project name placeholder and a short description section (action_type: create_file, path: README.md).
- Propose missing standard directories only if clearly absent and relevant to the stack (e.g. src/, tests/ for Python).
- Keep actions to the most impactful 3-6 items ordered by priority.
- Mark mv/rm of existing files as high risk. File creation and mkdir are low risk.
- If the project looks clean, say so in the summary and return fewer actions.
- Return only valid JSON — no markdown, no explanation outside the JSON object.
""".strip()


@dataclass
class OrgAnalysis:
    stack: str
    summary: str
    actions: list[dict[str, object]]


def generate_org_analysis(cwd: str, files: list[str], stack_hints: list[str]) -> OrgAnalysis:
    if not settings.openai_api_key:
        return _heuristic_org_analysis(files, stack_hints)

    try:
        return _call_org_analysis(cwd=cwd, files=files, stack_hints=stack_hints)
    except Exception:
        return _heuristic_org_analysis(files, stack_hints)


def _call_org_analysis(cwd: str, files: list[str], stack_hints: list[str]) -> OrgAnalysis:
    file_list = "\n".join(f"  {f}" for f in files[:100]) or "  (empty directory)"
    hint_list = ", ".join(stack_hints) if stack_hints else "none detected"

    user_message = (
        f"Project directory: {cwd}\n"
        f"Stack marker files found: {hint_list}\n"
        f"Top-level files and directories:\n{file_list}"
    )

    if _is_responses_api(settings.openai_model):
        endpoint = f"{settings.openai_base_url.rstrip('/')}/responses"
        response = httpx.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "instructions": ORG_SYSTEM_PROMPT,
                "input": [{"role": "user", "content": user_message}],
                "text": {"format": {"type": "json_object"}},
            },
            timeout=settings.openai_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["output"][0]["content"][0]["text"]
    else:
        endpoint = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        response = httpx.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "messages": [
                    {"role": "system", "content": ORG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=settings.openai_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]

    parsed = json.loads(content)
    return OrgAnalysis(
        stack=str(parsed.get("stack", "Unknown")).strip(),
        summary=str(parsed.get("summary", "")).strip(),
        actions=_normalize_org_actions(parsed.get("actions", [])),
    )


def _normalize_org_actions(items: object) -> list[dict[str, object]]:
    if not isinstance(items, list):
        return []
    valid_types = {"command", "create_file", "create_dir"}
    valid_risks = {"low", "medium", "high"}
    result: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        action_type = str(item.get("action_type", "")).strip()
        if action_type not in valid_types:
            continue
        risk = str(item.get("risk", "low")).strip().lower()
        if risk not in valid_risks:
            risk = "low"
        rationale = str(item.get("rationale", "")).strip()
        entry: dict[str, object] = {
            "action_type": action_type,
            "rationale": rationale or "Proposed by the model.",
            "risk": risk,
        }
        if action_type in {"create_file", "create_dir"}:
            entry["path"] = str(item.get("path", "")).strip()
        if action_type == "create_file":
            entry["content"] = str(item.get("content", "")).strip()
        if action_type == "command":
            entry["command"] = str(item.get("command", "")).strip()
        result.append(entry)
    return result


def _heuristic_org_analysis(files: list[str], stack_hints: list[str]) -> OrgAnalysis:
    has_gitignore = ".gitignore" in files
    has_readme = any(f.lower() in {"readme.md", "readme.txt", "readme"} for f in files)

    stack = "Unknown"
    if "package.json" in stack_hints and ("requirements.txt" in stack_hints or "pyproject.toml" in stack_hints):
        stack = "Node.js + Python"
    elif "package.json" in stack_hints:
        stack = "Node.js"
    elif "requirements.txt" in stack_hints or "pyproject.toml" in stack_hints:
        stack = "Python"
    elif "Cargo.toml" in stack_hints:
        stack = "Rust"

    actions: list[dict[str, object]] = []
    if not has_gitignore:
        actions.append({
            "action_type": "create_file",
            "path": ".gitignore",
            "content": "# Krud AI generated .gitignore\n.env\n.env.*\n*.log\nnode_modules/\n__pycache__/\n*.pyc\n.DS_Store\ndist/\nbuild/\n.venv/\ntarget/\n",
            "rationale": "No .gitignore found — this prevents accidental commits of secrets and build artifacts.",
            "risk": "low",
        })
    if not has_readme:
        actions.append({
            "action_type": "create_file",
            "path": "README.md",
            "content": "# Project Name\n\nA short description of this project.\n\n## Getting Started\n\n```bash\n# add your setup steps here\n```\n\n## Usage\n\n```bash\n# add usage examples here\n```\n",
            "rationale": "No README found — every project needs a front door.",
            "risk": "low",
        })

    summary = f"Detected stack: {stack}."
    if not actions:
        summary += " Project looks reasonably clean."
    else:
        summary += f" Found {len(actions)} quick hygiene improvement(s)."

    return OrgAnalysis(stack=stack, summary=summary, actions=actions)


def normalize_command_proposals(items: object) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []

    proposals: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        command = str(item.get("command", "")).strip()
        rationale = str(item.get("rationale", "")).strip()
        risk = str(item.get("risk", "low")).strip().lower()
        if not command or risk not in {"low", "medium", "high"}:
            continue
        proposals.append(
            {
                "command": command,
                "rationale": rationale or "Proposed by the model.",
                "risk": risk,
            }
        )
    return proposals

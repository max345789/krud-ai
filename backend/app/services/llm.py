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


def call_openai_chat(message: str, history: list[dict[str, object]], cwd: str | None = None) -> ChatGeneration:
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

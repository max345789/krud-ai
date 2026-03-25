from __future__ import annotations

from app.services.llm import ChatGeneration, generate_reply


def derive_session_title(title: str | None) -> str:
    if title and title.strip():
        return title.strip()
    return "New Krud Session"


def build_chat_reply(
    message: str,
    history: list[dict[str, object]],
    cwd: str | None = None,
) -> ChatGeneration:
    return generate_reply(message=message, history=history, cwd=cwd)

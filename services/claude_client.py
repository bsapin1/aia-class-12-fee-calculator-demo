from __future__ import annotations

import json
import os
from typing import Any

import streamlit as st

try:
    import anthropic
except ImportError:
    anthropic = None


def get_api_key() -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def is_claude_available() -> bool:
    return anthropic is not None and bool(get_api_key())


def get_client() -> anthropic.Anthropic:
    if anthropic is None:
        raise RuntimeError("anthropic package is not installed.")
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to .env or Streamlit secrets."
        )
    return anthropic.Anthropic(api_key=api_key)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def call_claude_json(system: str, user_prompt: str, model: str = "claude-sonnet-4-6") -> dict[str, Any]:
    client = get_client()
    response = client.messages.create(
        model=model,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text_blocks = [block.text for block in response.content if hasattr(block, "text")]
    if not text_blocks:
        raise RuntimeError("Claude returned an empty response.")
    return _extract_json("".join(text_blocks))


def call_claude_text(system: str, user_prompt: str, model: str = "claude-sonnet-4-6") -> str:
    client = get_client()
    response = client.messages.create(
        model=model,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text_blocks = [block.text for block in response.content if hasattr(block, "text")]
    return "".join(text_blocks).strip()

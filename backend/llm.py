"""OpenRouter LLM client. Reads OPENROUTER_API_KEY and AMENDA_MODEL from .env."""
import os
import json
import re
import httpx
from dotenv import load_dotenv

# .env lives at the amenda/ project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = os.getenv("AMENDA_MODEL", "anthropic/claude-sonnet-4.5")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMNotConfigured(Exception):
    pass


def chat(system: str, user: str, max_tokens: int = 4000) -> str:
    """One-shot chat completion. Raises LLMNotConfigured if no key."""
    if not API_KEY:
        raise LLMNotConfigured(
            "OPENROUTER_API_KEY missing. Create amenda/.env with "
            "OPENROUTER_API_KEY=sk-or-... and optionally AMENDA_MODEL=..."
        )
    resp = httpx.post(
        BASE_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def chat_json(system: str, user: str, max_tokens: int = 4000):
    """Chat completion parsed as JSON. Strips markdown fences if present."""
    text = chat(system, user, max_tokens)
    # tolerate ```json ... ``` fencing
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1)
    # tolerate leading prose before the first { or [
    start = min([i for i in (text.find("{"), text.find("[")) if i >= 0], default=0)
    return json.loads(text[start:])

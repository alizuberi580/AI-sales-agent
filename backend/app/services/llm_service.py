"""
LLM Service — uses Groq API (primary), falls back to deterministic templates.
Groq is free: https://console.groq.com
Set GROQ_API_KEY in backend/.env
"""
import os
import json
import re
import asyncio
from typing import Any

# ── Groq config (read from .env) ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Rate limit guard: Groq free tier = 30 req/min
# Semaphore limits concurrent calls so we don't hit 429s
_groq_semaphore = asyncio.Semaphore(5)


async def call_groq(prompt: str) -> str:
    """
    Call Groq API using their Python SDK (async-wrapped).
    Returns raw text response, or empty string on any failure.
    """
    if not GROQ_API_KEY:
        return ""

    try:
        from groq import Groq
    except ImportError:
        return ""

    async with _groq_semaphore:
        try:
            # Groq SDK is sync — run in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _sync_groq_call, prompt)
            return result
        except Exception:
            return ""


def _sync_groq_call(prompt: str) -> str:
    """Synchronous Groq call — runs in executor thread."""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise B2B sales AI assistant. Always respond with valid JSON only. No explanation, no markdown, just the raw JSON object or array."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""
    except Exception:
        return ""


def extract_json(text: str) -> Any:
    """Extract JSON from LLM output — handles code blocks and partial wrapping."""
    if not text:
        return None

    # Direct parse
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Strip markdown code block
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass

    # Find first { or [ and last } or ]
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        idx = text.find(start_char)
        if idx != -1:
            end_idx = text.rfind(end_char)
            if end_idx > idx:
                try:
                    return json.loads(text[idx:end_idx + 1])
                except Exception:
                    pass

    return None


async def llm_json(prompt: str, fallback: Any) -> Any:
    """
    Call Groq and parse JSON response.
    Returns fallback if Groq is not configured, call fails, or JSON is invalid.
    """
    raw = await call_groq(prompt)
    if raw:
        result = extract_json(raw)
        if result is not None:
            return result
    return fallback

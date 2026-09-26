import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root — works regardless of where uvicorn is launched from
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)

# NVIDIA Nemotron 550B — confirmed free & working on OpenRouter, very capable
MODEL_NAME = "nvidia/nemotron-3-ultra-550b-a55b:free"
_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Return a reusable OpenRouter client (OpenAI-compatible)."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is missing. Add it to your .env file.")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client


def _extract_json(raw: str) -> str:
    """Extract the first valid complete JSON object from a string."""
    raw = raw.strip()
    # Strip markdown code fences
    if raw.startswith("```"):
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break
    # Find the outermost {...} block
    start = raw.find("{")
    if start == -1:
        return raw
    depth = 0
    for i, ch in enumerate(raw[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    # Incomplete JSON — return what we have and let pydantic handle it
    return raw[start:]


def generate_text(prompt: str) -> str:
    """Send a plain text prompt and return the response."""
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


def generate_json(prompt: str, system_hint: str = "") -> str:
    """Send a prompt and get back a JSON string response."""
    client = get_client()
    system_msg = (
        "You are an expert technical interviewer AI. "
        "CRITICAL: Your entire response must be ONLY a valid JSON object. "
        "Do NOT include markdown, code fences (```), explanations, or any text outside the JSON. "
        "Start your response with { and end with }. Nothing else."
    )
    if system_hint:
        system_msg += f"\n\n{system_hint}"

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    raw = response.choices[0].message.content or "{}"
    return _extract_json(raw)

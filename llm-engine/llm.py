"""
Gemini API connection using the Google GenAI SDK.
"""
import os
from dotenv import load_dotenv
from google import genai

MODEL_NAME = "gemini-3.8-flash"
_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Return a reusable Gemini client or initialize one if not present."""
    global _client
    if _client is None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing or not set.")
        _client = genai.Client(api_key=api_key)
    return _client


def generate_text(prompt: str) -> str:
    """Send the prompt to Gemini and return the generated text."""
    client = get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text or ""

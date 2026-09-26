"""
Minimal test to verify the Gemini LLM connection.
"""
from pathlib import Path
from dotenv import load_dotenv
from llm import generate_text

# Load environment variables from .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    prompt = "Reply with exactly: LLM CONNECTION WORKING"
    response = generate_text(prompt)
    print(response)

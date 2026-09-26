"""
Minimal test to verify the Gemini LLM connection.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

engine_dir = Path(__file__).resolve().parent
workspace_dir = engine_dir.parent
for p in (str(engine_dir), str(workspace_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Load environment variables from .env
load_dotenv(dotenv_path=engine_dir / ".env")
load_dotenv(dotenv_path=workspace_dir / ".env")

try:
    from llm_engine.llm import generate_text
except ImportError:
    from llm import generate_text  # type: ignore

if __name__ == "__main__":
    prompt = "Reply with exactly: LLM CONNECTION WORKING"
    response = generate_text(prompt)
    print(response)

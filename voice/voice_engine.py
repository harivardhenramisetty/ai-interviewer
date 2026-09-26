from pathlib import Path

from dotenv import load_dotenv
from deepgram import DeepgramClient

from .config import VOICE_MODEL, VOICE_SETTINGS


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

client = DeepgramClient()


def speak(
    text: str,
    mode: str = "question",
    output_file: str = "output.mp3",
) -> str:
    """
    Convert interview text into speech using Deepgram.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    if mode not in VOICE_SETTINGS:
        raise ValueError(
            f"Unknown voice mode '{mode}'. "
            f"Available modes: {', '.join(VOICE_SETTINGS.keys())}"
        )

    settings = VOICE_SETTINGS[mode]

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = client.speak.v1.audio.generate(
        text=text,
        model=VOICE_MODEL,
        encoding="mp3",
        speed=settings["speed"],
    )

    with open(output_path, "wb") as audio_file:
        for chunk in response:
            audio_file.write(chunk)

    return str(output_path)
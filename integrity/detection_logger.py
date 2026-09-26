import json
from pathlib import Path
from datetime import datetime


LOG_FILE = (
    Path(__file__).resolve().parent
    / "detection_log.json"
)


def start_new_interview():
    """
    Clear the previous interview's integrity log
    and start a fresh one.
    """

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump([], file, indent=4)


def save_event(event):
    """
    Add an integrity event to the current interview log.
    """

    if LOG_FILE.exists():
        try:
            with open(
                LOG_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                events = json.load(file)

        except (
            json.JSONDecodeError,
            OSError,
        ):
            events = []

    else:
        events = []

    events.append(event)

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            events,
            file,
            indent=4,
        )


def create_event(
    event,
    face_count=None,
    duration=None,
    direction=None,
):
    """
    Create a structured integrity event.
    """

    record = {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "event": event,
    }

    if face_count is not None:
        record["face_count"] = face_count

    if duration is not None:
        record["duration_seconds"] = round(
            duration,
            2,
        )

    if direction is not None:
        record["direction"] = direction

    return record
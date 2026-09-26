from .voice_engine import speak


QUESTION_MODES = {
    "question": "question",
    "follow_up": "follow_up",
    "clarification": "clarification",
    "greeting": "greeting",
    "closing": "closing",
}


def speak_question(
    question: str,
    question_type: str = "question",
    output_file: str = "current_question.mp3",
) -> str:
    """
    Convert an LLM-generated interview question into speech.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if question_type not in QUESTION_MODES:
        raise ValueError(
            f"Unknown question type '{question_type}'. "
            f"Available types: {', '.join(QUESTION_MODES.keys())}"
        )

    mode = QUESTION_MODES[question_type]

    return speak(
        question.strip(),
        mode=mode,
        output_file=output_file,
    )
def speak_interview_question(
    question,
    output_file: str = "current_question.mp3",
) -> str:
    """
    Convert an LLM Question object into speech.

    Expects the Question object to contain:
    - question
    - question_type
    """

    voice_mode = "question"

    return speak_question(
        question=question.question,
        question_type=voice_mode,
        output_file=output_file,
    )

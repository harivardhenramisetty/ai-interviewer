from voice.voice_engine import speak


texts = {
    "greeting": "Welcome to the interview. It is nice to meet you.",
    "question": "Can you tell me about your most recent project?",
    "follow_up": "Could you explain that part of the project in a little more detail?",
    "clarification": "Could you clarify what you mean by that?",
    "closing": "Thank you for your time. That concludes the interview.",
}


for mode, text in texts.items():
    output_file = f"test_{mode}.mp3"

    speak(
        text,
        mode=mode,
        output_file=output_file,
    )

    print(f"{mode}: {output_file} generated")
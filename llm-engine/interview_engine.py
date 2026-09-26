"""
Candidate profile generation engine using Gemini structured output.
"""
from typing import Optional
from google import genai
from pydantic import ValidationError
from llm import get_client, MODEL_NAME
from models import CandidateProfile, Question
from prompts import PROMPT_GENERATE_PROFILE, PROMPT_GENERATE_QUESTION

def generate_candidate_profile(
    resume_text: str,
    target_role: str,
    job_description: str | None = None
) -> CandidateProfile:
    """Generate a structured candidate profile from a resume and target role."""
    client = get_client()
    
    job_desc_section = f"Job Description:\n{job_description}" if job_description else "Job Description: Not provided. Base analysis solely on the target role."
    
    prompt = PROMPT_GENERATE_PROFILE.format(
        target_role=target_role,
        job_description_section=job_desc_section,
        resume_text=resume_text
    )
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CandidateProfile,
            temperature=0.2, # Lower temperature for analytical extraction
        ),
    )
    
    if not response.text:
        raise ValueError("LLM returned an empty response.")
        
    try:
        return CandidateProfile.model_validate_json(response.text)
    except ValidationError as e:
        raise ValueError(f"Failed to parse LLM response into CandidateProfile: {e}")

def generate_next_question(
    candidate_profile: CandidateProfile,
    target_role: str,
    conversation_history: list[dict],
    current_topic: str | None = None
) -> Question:
    """Generate the next adaptive interview question."""
    client = get_client()
    
    # Format history for prompt
    history_text = "No previous questions."
    if conversation_history:
        history_text = "\n\n".join(
            f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}\nEvaluation: {item.get('evaluation', '')}"
            for item in conversation_history
        )
    
    topic_str = current_topic if current_topic else "Any relevant topic from the profile."
    
    prompt = PROMPT_GENERATE_QUESTION.format(
        target_role=target_role,
        current_topic=topic_str,
        candidate_profile=candidate_profile.model_dump_json(indent=2),
        conversation_history=history_text
    )
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Question,
            temperature=0.7, # slightly higher for varied questions
        ),
    )
    
    if not response.text:
        raise ValueError("LLM returned an empty response.")
        
    try:
        return Question.model_validate_json(response.text)
    except ValidationError as e:
        raise ValueError(f"Failed to parse LLM response into Question: {e}")

if __name__ == "__main__":
    print("Testing generate_candidate_profile...")
    sample_resume = (
        "Alice Smith\n"
        "Software Engineer with 4 years of experience building scalable backend systems. "
        "Proficient in Python, Django, and PostgreSQL. "
        "Led a team of 3 developers to migrate a legacy monolith to microservices. "
        "Familiar with Docker and AWS."
    )
    try:
        profile = generate_candidate_profile(
            resume_text=sample_resume,
            target_role="Senior Backend Python Developer",
            job_description=None
        )
        print("\nTest passed! Generated Profile:")
        print(profile.model_dump_json(indent=2))
        
        print("\nTesting generate_next_question...")
        fake_history = [
            {
                "question": "Can you explain your experience with Django?",
                "answer": "I have used Django for 4 years to build REST APIs.",
                "evaluation": "Good basic answer. Needs more depth on architecture."
            }
        ]
        next_q = generate_next_question(
            candidate_profile=profile,
            target_role="Senior Backend Python Developer",
            conversation_history=fake_history,
            current_topic="System Architecture"
        )
        print("\nTest passed! Generated Question:")
        print(next_q.model_dump_json(indent=2))
        
    except Exception as e:
        print(f"\nTest failed: {e}")

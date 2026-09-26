"""
Candidate profile generation engine using Gemini structured output.
"""
from typing import Optional
from google import genai
from pydantic import ValidationError
from llm import get_client, MODEL_NAME
from models import CandidateProfile, Question, AnswerEvaluation, InterviewTurn, InterviewSession, InterviewReport, QualitativeReport
from prompts import PROMPT_GENERATE_PROFILE, PROMPT_GENERATE_QUESTION, PROMPT_EVALUATE_ANSWER, PROMPT_GENERATE_REPORT

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

def evaluate_answer(
    candidate_profile: CandidateProfile,
    question: Question,
    candidate_answer: str,
    conversation_history: list[dict]
) -> AnswerEvaluation:
    """Evaluate a candidate's answer against a question."""
    client = get_client()
    
    # Format history for prompt
    history_text = "No previous questions."
    if conversation_history:
        history_text = "\n\n".join(
            f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}\nEvaluation: {item.get('evaluation', '')}"
            for item in conversation_history
        )
        
    prompt = PROMPT_EVALUATE_ANSWER.format(
        question=question.question,
        topic=question.topic,
        difficulty=question.difficulty,
        question_type=question.question_type,
        candidate_answer=candidate_answer,
        candidate_profile=candidate_profile.model_dump_json(indent=2),
        conversation_history=history_text
    )
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AnswerEvaluation,
            temperature=0.2, # Lower temperature for objective evaluation
        ),
    )
    
    if not response.text:
        raise ValueError("LLM returned an empty response.")
        
    try:
        return AnswerEvaluation.model_validate_json(response.text)
    except ValidationError as e:
        raise ValueError(f"Failed to parse LLM response into AnswerEvaluation: {e}")

def start_interview(
    candidate_profile: CandidateProfile,
    target_role: str,
    job_description: str | None = None,
    max_questions: int = 8
) -> InterviewSession:
    """Start a new interview session and generate the first question."""
    
    first_question = generate_next_question(
        candidate_profile=candidate_profile,
        target_role=target_role,
        conversation_history=[]
    )
    
    return InterviewSession(
        candidate_profile=candidate_profile,
        target_role=target_role,
        job_description=job_description,
        history=[],
        current_question=first_question,
        question_number=1,
        max_questions=max_questions,
        status="in_progress"
    )

def submit_answer(
    session: InterviewSession,
    answer: str
) -> InterviewSession:
    """Submit an answer to the current question and progress the interview state."""
    if session.status != "in_progress":
        raise ValueError(f"Cannot submit answer. Session status is '{session.status}'.")
    if not session.current_question:
        raise ValueError("Cannot submit answer. No current question.")

    # 1. Format history for evaluation and next generation
    formatted_history = []
    for turn in session.history:
        formatted_history.append({
            "question": turn.question.question,
            "answer": turn.answer or "",
            "evaluation": turn.evaluation.model_dump() if turn.evaluation else ""
        })

    # 2. Evaluate the candidate's answer
    evaluation = evaluate_answer(
        candidate_profile=session.candidate_profile,
        question=session.current_question,
        candidate_answer=answer,
        conversation_history=formatted_history
    )
    
    # 3. Create the completed turn and append to history
    new_turn = InterviewTurn(
        question=session.current_question,
        answer=answer,
        evaluation=evaluation
    )
    session.history.append(new_turn)

    # 4. Check if max questions reached
    if session.question_number >= session.max_questions:
        session.status = "completed"
        session.current_question = None
    else:
        # Generate the next question
        formatted_history.append({
            "question": new_turn.question.question,
            "answer": new_turn.answer or "",
            "evaluation": new_turn.evaluation.model_dump() if new_turn.evaluation else ""
        })
        
        next_question = generate_next_question(
            candidate_profile=session.candidate_profile,
            target_role=session.target_role,
            conversation_history=formatted_history
        )
        session.current_question = next_question
        session.question_number += 1

    return session

def calculate_interview_scores(session: InterviewSession) -> tuple[float, float, float, float]:
    """Calculate the overall, technical, depth, and clarity scores for an interview."""
    evals = [turn.evaluation for turn in session.history if turn.evaluation]
    if not evals:
        return 0.0, 0.0, 0.0, 0.0

    overall_score = round(sum(e.score for e in evals) / len(evals), 1)
    technical_score = round(sum(e.technical_accuracy for e in evals) / len(evals), 1)
    depth_score = round(sum(e.depth for e in evals) / len(evals), 1)
    clarity_score = round(sum(e.clarity for e in evals) / len(evals), 1)
    
    return overall_score, technical_score, depth_score, clarity_score

def generate_interview_report(session: InterviewSession) -> InterviewReport:
    """Generate the final evaluation report for a completed interview."""
    if session.status != "completed":
        raise ValueError("Interview is not completed.")
    if not session.history:
        raise ValueError("Interview history is empty.")

    overall_score, technical_score, depth_score, clarity_score = calculate_interview_scores(session)

    # Prepare transcript for Gemini
    transcript = []
    for turn in session.history:
        transcript.append(f"Q: {turn.question.question}\nA: {turn.answer or 'N/A'}\nEvaluation: {turn.evaluation.feedback if turn.evaluation else 'N/A'}")
    
    prompt = PROMPT_GENERATE_REPORT.format(
        candidate_profile=session.candidate_profile.model_dump_json(indent=2),
        interview_transcript="\n\n".join(transcript)
    )

    client = get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QualitativeReport,
            temperature=0.2, 
        ),
    )

    if not response.text:
        raise ValueError("LLM returned an empty response.")

    try:
        qualitative = QualitativeReport.model_validate_json(response.text)
    except ValidationError as e:
        raise ValueError(f"Failed to parse LLM response into QualitativeReport: {e}")

    return InterviewReport(
        overall_score=overall_score,
        technical_score=technical_score,
        depth_score=depth_score,
        clarity_score=clarity_score,
        strengths=qualitative.strengths,
        areas_for_improvement=qualitative.areas_for_improvement,
        topics_demonstrated=qualitative.topics_demonstrated,
        recommendations=qualitative.recommendations,
        summary=qualitative.summary
    )

if __name__ == "__main__":
    print("Testing End-to-End State Management...")
    
    fake_profile = CandidateProfile(
        candidate_summary="Fake candidate for testing state.",
        skills=["Python"],
        experience_level="Mid",
        strengths=["Testing"],
        potential_gaps=["None"],
        relevant_topics=["Python"]
    )
    
    print("\n--- Starting Interview (max_questions=2) ---")
    session = start_interview(
        candidate_profile=fake_profile,
        target_role="Tester",
        max_questions=2
    )
    
    print(f"Status: {session.status}")
    print(f"Question Number: {session.question_number}")
    print(f"History Length: {len(session.history)}")
    print(f"Current Question: {session.current_question.question if session.current_question else 'None'}")
    
    print("\n--- Submitting First Answer ---")
    session = submit_answer(session, "This is my first fake answer.")
    print(f"Status: {session.status}")
    print(f"Question Number: {session.question_number}")
    print(f"History Length: {len(session.history)}")
    print(f"Current Question: {session.current_question.question if session.current_question else 'None'}")
    
    print("\n--- Submitting Second Answer ---")
    session = submit_answer(session, "This is my second fake answer.")
    print(f"Status: {session.status}")
    print(f"Question Number: {session.question_number}")
    print(f"History Length: {len(session.history)}")
    print(f"Current Question: {session.current_question.question if session.current_question else 'None'}")

    print("\n--- Testing Score Calculation Unit Test ---")
    # Fake session without calling LLM
    fake_session = InterviewSession(
        candidate_profile=fake_profile,
        target_role="Tester",
        job_description=None,
        history=[
            InterviewTurn(
                question=Question(question="Q1", topic="T1", difficulty="easy", question_type="technical", reason=""),
                answer="A1",
                evaluation=AnswerEvaluation(score=8, technical_accuracy=9, depth=7, clarity=8, strengths=[], weaknesses=[], feedback="", recommended_action="move_on")
            ),
            InterviewTurn(
                question=Question(question="Q2", topic="T2", difficulty="medium", question_type="technical", reason=""),
                answer="A2",
                evaluation=AnswerEvaluation(score=6, technical_accuracy=7, depth=5, clarity=7, strengths=[], weaknesses=[], feedback="", recommended_action="follow_up")
            )
        ],
        current_question=None,
        question_number=2,
        max_questions=2,
        status="completed"
    )
    
    overall, tech, depth, clarity = calculate_interview_scores(fake_session)
    print(f"Calculated Scores:")
    print(f"Overall: {overall} (Expected: 7.0)")
    print(f"Technical: {tech} (Expected: 8.0)")
    print(f"Depth: {depth} (Expected: 6.0)")
    print(f"Clarity: {clarity} (Expected: 7.5)")

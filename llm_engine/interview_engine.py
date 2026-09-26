"""
Interview engine using OpenRouter (Gemini 2.0 Flash / Llama 3.3 70B) for structured AI calls.
"""
import sys
import json
from pathlib import Path
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

engine_dir = Path(__file__).resolve().parent
workspace_dir = engine_dir.parent
for p in (str(engine_dir), str(workspace_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from llm_engine.llm import generate_json, MODEL_NAME, _extract_json
    from llm_engine.models import CandidateProfile, Question, AnswerEvaluation, InterviewTurn, InterviewSession, InterviewReport, QualitativeReport
    from llm_engine.prompts import PROMPT_GENERATE_PROFILE, PROMPT_GENERATE_QUESTION, PROMPT_EVALUATE_ANSWER, PROMPT_GENERATE_REPORT
except (ImportError, ValueError):
    from .llm import generate_json, MODEL_NAME, _extract_json  # type: ignore
    from .models import CandidateProfile, Question, AnswerEvaluation, InterviewTurn, InterviewSession, InterviewReport, QualitativeReport  # type: ignore
    from .prompts import PROMPT_GENERATE_PROFILE, PROMPT_GENERATE_QUESTION, PROMPT_EVALUATE_ANSWER, PROMPT_GENERATE_REPORT  # type: ignore

T = TypeVar("T", bound=BaseModel)


def call_llm_structured(prompt: str, schema: Type[T]) -> T:
    """Call OpenRouter and parse response into the given Pydantic model."""
    raw = generate_json(prompt)
    raw = _extract_json(raw)
    try:
        return schema.model_validate_json(raw)
    except (ValidationError, ValueError, Exception):
        try:
            data = json.loads(raw)
            # Coerce recommended_action to a valid literal if the LLM invented one
            if "recommended_action" in data:
                valid = {"follow_up", "move_on", "increase_difficulty"}
                if data["recommended_action"] not in valid:
                    data["recommended_action"] = "move_on"
            # Strip unknown extra fields Pydantic doesn't know about
            known_fields = set(schema.model_fields.keys())
            data = {k: v for k, v in data.items() if k in known_fields}
            return schema.model_validate(data)
        except Exception:
            raise ValueError(f"LLM returned unparseable JSON for {schema.__name__}: {raw[:300]}")


def generate_candidate_profile(
    resume_text: str,
    target_role: str,
    job_description: str | None = None
) -> CandidateProfile:
    """Generate a structured candidate profile from a resume and target role."""
    job_desc_section = f"Job Description:\n{job_description}" if job_description else "Job Description: Not provided. Base analysis solely on the target role."
    
    prompt = PROMPT_GENERATE_PROFILE.format(
        target_role=target_role,
        job_description_section=job_desc_section,
        resume_text=resume_text
    )
    
    return call_llm_structured(prompt, CandidateProfile)


def generate_next_question(
    candidate_profile: CandidateProfile,
    target_role: str,
    conversation_history: list[dict],
    current_topic: str | None = None
) -> Question:
    """Generate the next adaptive interview question."""
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
    
    return call_llm_structured(prompt, Question)


def evaluate_answer(
    candidate_profile: CandidateProfile,
    question: Question,
    candidate_answer: str,
    conversation_history: list[dict]
) -> AnswerEvaluation:
    """Evaluate a candidate's answer against a question."""

    stripped = candidate_answer.strip() if candidate_answer else ""
    words = stripped.split()

    # --- Pre-LLM hard rejection (never waste an API call on these) ---
    NON_ANSWERS = {
        "no", "yes", "maybe", "idk", "i don't know", "i dont know",
        "dunno", "na", "n/a", "skip", "nothing", "none", "not sure",
        "no idea", "don't know", "dont know", "nope", "yep", "yeah",
        "ok", "okay", "sure", "fine", "whatever", "pass", "next",
        "i don't know the answer", "i dont know the answer",
    }

    is_trivially_empty = not stripped
    is_trivially_short = len(words) <= 3
    is_non_answer = stripped.lower() in NON_ANSWERS or stripped.lower().rstrip('.!?') in NON_ANSWERS

    if is_trivially_empty or is_non_answer or is_trivially_short:
        return AnswerEvaluation(
            is_relevant=False,
            score=0,
            technical_accuracy=0,
            depth=0,
            clarity=0,
            strengths=[],
            weaknesses=["Answer does not address the question."],
            feedback=(
                f"The response '{stripped}' does not answer the question. "
                "Please provide a detailed technical explanation."
            ),
            recommended_action="move_on"
        )

    history_text = "No previous questions."

    if conversation_history:
        history_text = "\n\n".join(
            f"Q: {item.get('question', '')}\n"
            f"A: {item.get('answer', '')}\n"
            f"Evaluation: {item.get('evaluation', '')}"
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

    evaluation = call_llm_structured(prompt, AnswerEvaluation)

    # HARD RELEVANCE GATE.
    # Never allow an irrelevant answer to receive a positive score.
    if not evaluation.is_relevant:
        evaluation.score = 0
        evaluation.technical_accuracy = 0
        evaluation.depth = 0
        evaluation.clarity = 0

        if not evaluation.weaknesses:
            evaluation.weaknesses = []

        if "Answer does not address the question." not in evaluation.weaknesses:
            evaluation.weaknesses.append(
                "Answer does not address the question."
            )

        evaluation.feedback = (
            "The answer did not address the question asked."
        )

        evaluation.recommended_action = "move_on"

    # Keep all scores safely inside 0-10.
    evaluation.score = max(0, min(10, evaluation.score))
    evaluation.technical_accuracy = max(
        0, min(10, evaluation.technical_accuracy)
    )
    evaluation.depth = max(
        0, min(10, evaluation.depth)
    )
    evaluation.clarity = max(
        0, min(10, evaluation.clarity)
    )

    return evaluation

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

    qualitative = call_llm_structured(prompt, QualitativeReport)

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

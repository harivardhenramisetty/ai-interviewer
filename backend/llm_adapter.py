from llm_engine.interview_engine import (
    generate_candidate_profile,
    generate_next_question as llm_generate_next_question,
    evaluate_answer as llm_evaluate_answer,
    generate_interview_report
)
from llm_engine.models import CandidateProfile, Question, AnswerEvaluation, InterviewTurn, InterviewSession

def _map_profile_to_engine(profile_dict: dict) -> CandidateProfile:
    """
    Safely map a profile dictionary to the LLM engine's CandidateProfile.
    Handles both native engine fields and legacy backend fields without fabricating data.
    """
    if "candidate_summary" in profile_dict:
        # Native engine fields are present
        return CandidateProfile.model_validate(profile_dict)
    
    # Legacy backend fields only
    name = profile_dict.get("name", "Unknown")
    education = ", ".join(profile_dict.get("education", []))
    experience = ", ".join(profile_dict.get("experience", []))
    
    summary_parts = [f"Candidate: {name}"]
    if education:
        summary_parts.append(f"Education: {education}")
    if experience:
        summary_parts.append(f"Experience: {experience}")
        
    candidate_summary = ". ".join(summary_parts)
    skills = profile_dict.get("skills", [])
    projects = profile_dict.get("projects", [])
    
    # Do not invent strengths/gaps. Topics are based on explicit information.
    relevant_topics = list(set(skills + projects))
    
    return CandidateProfile(
        candidate_summary=candidate_summary,
        skills=skills,
        experience_level="unknown",
        strengths=[],
        potential_gaps=[],
        relevant_topics=relevant_topics
    )


def _map_difficulty_to_int(diff_str: str) -> int:
    """Map string difficulty ('easy', 'medium', 'hard') to integer (1, 3, 5)."""
    diff = str(diff_str).lower()
    if diff == "easy": return 1
    if diff == "hard": return 5
    return 3


def analyze_resume(resume_text: str, target_role: str, job_description: str | None = None) -> dict:
    """Call the LLM engine to analyze the resume and return a hybrid dictionary."""
    profile = generate_candidate_profile(resume_text, target_role, job_description)
    
    return {
        # Backend expected fields
        "name": "Unknown Candidate",
        "education": [],
        "skills": profile.skills,
        "projects": [],
        "experience": [],
        "certifications": [],
        
        # LLM Engine fields preserved
        "candidate_summary": profile.candidate_summary,
        "experience_level": profile.experience_level,
        "strengths": profile.strengths,
        "potential_gaps": profile.potential_gaps,
        "relevant_topics": profile.relevant_topics
    }


def generate_question(profile_dict: dict, target_role: str, history: list) -> dict:
    """Generate the next adaptive question based on the profile and history."""
    profile = _map_profile_to_engine(profile_dict)
    
    # Format history as expected by generate_next_question
    formatted_history = []
    for turn in history:
        eval_data = turn.get("evaluation", "")
        formatted_history.append({
            "question": turn.get("question", ""),
            "answer": turn.get("answer", ""),
            "evaluation": eval_data
        })
        
    question = llm_generate_next_question(profile, target_role, formatted_history)
    q_dict = question.model_dump()
    
    # Map the string difficulty to the integer format expected by the DB
    q_dict["difficulty"] = _map_difficulty_to_int(q_dict.get("difficulty", "medium"))
    return q_dict


def evaluate_answer(
    profile_dict: dict,
    target_role: str,
    question_text: str,
    answer: str,
    topic: str = "General",
    difficulty: int = 3,
    question_type: str = "technical"
) -> dict:

    profile = _map_profile_to_engine(profile_dict)
    from typing import Literal, cast
    diff_str: Literal["easy", "medium", "hard"] = "medium"
    if difficulty <= 2:
        diff_str = "easy"
    elif difficulty >= 4:
        diff_str = "hard"

    valid_qtypes = {"technical", "behavioral", "situational", "project"}
    q_type_str = question_type if question_type in valid_qtypes else "technical"
    valid_type = cast(Literal["technical", "behavioral", "situational", "project"], q_type_str)

    question = Question(
        question=question_text,
        topic=topic,
        difficulty=diff_str,
        question_type=valid_type,
        reason=""
    )

    evaluation = llm_evaluate_answer(
        candidate_profile=profile,
        question=question,
        candidate_answer=answer,
        conversation_history=[]
    )

    return evaluation.model_dump()


def generate_final_report(profile_dict: dict, target_role: str, history: list) -> dict:
    """Reconstruct the session and generate the final report."""
    profile = _map_profile_to_engine(profile_dict)
    
    turns = []
    for turn in history:
        # DB provides integer difficulty, we map it back to string safely 
        # (though report generation doesn't heavily depend on the exact difficulty string)
        diff_val = turn.get("difficulty", 3)
        diff_str = "medium"
        if isinstance(diff_val, int):
            if diff_val <= 2: diff_str = "easy"
            elif diff_val >= 4: diff_str = "hard"
            
        q = Question(
            question=turn.get("question", ""),
            topic=turn.get("topic", ""),
            difficulty=diff_str,
            question_type="technical",
            reason=""
        )
        
        eval_dict = turn.get("evaluation")
        if isinstance(eval_dict, dict):
            rec_action = eval_dict.get("recommended_action", "move_on")
            if rec_action not in ("follow_up", "move_on", "increase_difficulty"):
                rec_action = "move_on"
            evaluation = AnswerEvaluation(
                is_relevant=bool(eval_dict.get("is_relevant", True)),
                score=float(eval_dict.get("score", 5)),
                technical_accuracy=float(eval_dict.get("technical_accuracy", 5)),
                depth=float(eval_dict.get("depth", 5)),
                clarity=float(eval_dict.get("clarity", 5)),
                strengths=eval_dict.get("strengths", [])
                    if isinstance(eval_dict.get("strengths"), list) else [],
                weaknesses=eval_dict.get("weaknesses", [])
                    if isinstance(eval_dict.get("weaknesses"), list) else [],
                feedback=str(eval_dict.get("feedback", "")),
                recommended_action=rec_action
            )
        else:
            evaluation = None
            
        turns.append(InterviewTurn(
            question=q,
            answer=turn.get("answer", ""),
            evaluation=evaluation
        ))
        
    session = InterviewSession(
        candidate_profile=profile,
        target_role=target_role,
        job_description=None,
        history=turns,
        current_question=None,
        question_number=len(turns) + 1,
        max_questions=len(turns),
        status="completed"
    )
    
    report = generate_interview_report(session)
    
    # Map llm_engine output to main.py expected format
    return {
        "overall_score": report.overall_score,
        "strengths": report.strengths,
        "gaps": report.areas_for_improvement,
        "recommendation": "\n".join(report.recommendations),
        "summary": report.summary
    }

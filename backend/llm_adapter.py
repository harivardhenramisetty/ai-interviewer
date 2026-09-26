import sys
import os

# Add llm_engine to python path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "llm_engine"))

from interview_engine import (
    generate_candidate_profile,
    generate_next_question as llm_generate_next_question,
    evaluate_answer as llm_evaluate_answer,
    generate_interview_report
)
from models import CandidateProfile, Question, AnswerEvaluation, InterviewTurn, InterviewSession

def analyze_resume(resume_text: str, target_role: str, job_description: str | None = None) -> dict:
    profile = generate_candidate_profile(resume_text, target_role, job_description)
    profile_dict = profile.model_dump()
    # Add 'name' because main.py expects it for the DB update
    profile_dict["name"] = "Unknown Candidate" 
    return profile_dict

def generate_question(profile_dict: dict, target_role: str, history: list) -> dict:
    profile = CandidateProfile.model_validate(profile_dict)
    
    # Format history as expected by generate_next_question
    formatted_history = []
    for turn in history:
        # main.py provides evaluation as a dict, we need just feedback or the full dict
        eval_data = turn.get("evaluation", "")
        formatted_history.append({
            "question": turn.get("question", ""),
            "answer": turn.get("answer", ""),
            "evaluation": eval_data
        })
        
    question = llm_generate_next_question(profile, target_role, formatted_history)
    return question.model_dump()

def evaluate_answer(profile_dict: dict, target_role: str, question_text: str, answer: str) -> dict:
    profile = CandidateProfile.model_validate(profile_dict)
    
    # Create a dummy Question object since we only have the question text from main.py
    question = Question(
        question=question_text,
        topic="General",
        difficulty="medium",
        question_type="technical",
        reason=""
    )
    
    evaluation = llm_evaluate_answer(
        candidate_profile=profile,
        question=question,
        candidate_answer=answer,
        conversation_history=[]  # main.py doesn't pass history for evaluation
    )
    return evaluation.model_dump()

def generate_final_report(profile_dict: dict, target_role: str, history: list) -> dict:
    profile = CandidateProfile.model_validate(profile_dict)
    
    # Reconstruct history into InterviewTurn objects
    turns = []
    for turn in history:
        # Reconstruct Question
        q = Question(
            question=turn.get("question", ""),
            topic=turn.get("topic", ""),
            difficulty=str(turn.get("difficulty", "medium")),
            question_type="technical",
            reason=""
        )
        
        # Reconstruct AnswerEvaluation
        eval_dict = turn.get("evaluation")
        if isinstance(eval_dict, dict):
            # Map main.py evaluation format to llm_engine AnswerEvaluation if needed
            evaluation = AnswerEvaluation(
                score=eval_dict.get("score", 5),
                technical_accuracy=eval_dict.get("technical_accuracy", 5),
                depth=eval_dict.get("depth", 5),
                clarity=eval_dict.get("clarity", 5),
                strengths=eval_dict.get("strengths", []),
                weaknesses=eval_dict.get("weaknesses", []),
                feedback=eval_dict.get("feedback", ""),
                recommended_action=eval_dict.get("recommended_action", "move_on")
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
    report_dict = report.model_dump()
    
    # Map llm_engine output to main.py expected format
    return {
        "overall_score": report.overall_score,
        "strengths": report.strengths,
        "gaps": report.areas_for_improvement, # areas_for_improvement -> gaps
        "recommendation": "\n".join(report.recommendations), # list -> string
        "summary": report.summary
    }

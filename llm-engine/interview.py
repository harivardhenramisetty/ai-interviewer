"""
Logic for managing the interview state.
"""
from .schemas import InterviewState, CandidateProfile, Question, EvaluationResult
from llm import call_llm_structured
from prompts import PROMPT_GENERATE_PROFILE, PROMPT_GENERATE_QUESTION

def initialize_interview(resume_text: str, target_role: str) -> InterviewState:
    """Generate candidate profile and prepare the initial interview state."""
    # TODO: call LLM to generate CandidateProfile from resume
    profile = CandidateProfile(name="Placeholder", key_skills=[], experience_level="Mid")
    
    state = InterviewState(
        profile=profile,
        questions_asked=[],
        answers_received=[],
        evaluations=[]
    )
    # Generate first question
    return generate_next_question(state)

def generate_next_question(state: InterviewState, last_eval: EvaluationResult = None) -> InterviewState:
    """Determine and generate the next question (adaptive or from plan)."""
    # TODO: Use last_eval to decide if a follow-up is needed, else generate next main question.
    # Update state.current_question
    return state

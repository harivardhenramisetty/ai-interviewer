"""
Entry point for the LLM Engine.
Exposes functions that the FastAPI backend will call.
"""

from .schemas import CandidateProfile, InterviewState, EvaluationResult, InterviewReport
from interview import initialize_interview, generate_next_question
from evaluator import evaluate_answer
from report import generate_final_report

class LLMEngine:
    def __init__(self):
        pass

    def start_interview(self, resume_text: str, target_role: str) -> InterviewState:
        """Initialize candidate profile and interview state."""
        return initialize_interview(resume_text, target_role)

    def process_answer(self, state: InterviewState, answer: str) -> tuple[EvaluationResult, InterviewState]:
        """Evaluate answer and generate adaptive follow-up or next main question."""
        eval_result = evaluate_answer(state, answer)
        state = generate_next_question(state, eval_result)
        return eval_result, state

    def conclude_interview(self, state: InterviewState) -> InterviewReport:
        """Generate final interview report."""
        return generate_final_report(state)

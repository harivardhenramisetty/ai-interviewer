"""
Logic for evaluating candidate answers.
"""
from .schemas import InterviewState, EvaluationResult
from llm import call_llm_structured
from prompts import PROMPT_EVALUATE_ANSWER

def evaluate_answer(state: InterviewState, answer: str) -> EvaluationResult:
    """Evaluate the candidate's answer against the current question."""
    question = state.current_question
    # TODO: Call LLM to evaluate the answer
    # Update state history
    state.answers_received.append(answer)
    
    # Mock result
    result = EvaluationResult(score=8, feedback="Good answer.", follow_up_needed=False)
    state.evaluations.append(result)
    
    return result

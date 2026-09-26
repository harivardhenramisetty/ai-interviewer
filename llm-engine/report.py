"""
Logic for generating the final report.
"""
from .schemas import InterviewState, InterviewReport
from llm import call_llm_structured
from prompts import PROMPT_GENERATE_REPORT

def generate_final_report(state: InterviewState) -> InterviewReport:
    """Compile the entire interview state into a final report."""
    # TODO: Pass the full history to the LLM to summarize
    
    # Mock report
    return InterviewReport(
        overall_score=85,
        summary="Strong candidate...",
        strengths=["Python", "Communication"],
        areas_for_improvement=["System Design"]
    )

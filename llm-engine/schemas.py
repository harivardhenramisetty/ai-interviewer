"""
Pydantic schemas for structured inputs and outputs.
"""
from pydantic import BaseModel
from typing import List, Optional

class CandidateProfile(BaseModel):
    name: str
    key_skills: List[str]
    experience_level: str

class Question(BaseModel):
    text: str
    expected_concepts: List[str]

class EvaluationResult(BaseModel):
    score: int
    feedback: str
    follow_up_needed: bool

class InterviewState(BaseModel):
    profile: CandidateProfile
    questions_asked: List[Question]
    answers_received: List[str]
    evaluations: List[EvaluationResult]
    current_question: Optional[Question] = None

class InterviewReport(BaseModel):
    overall_score: int
    summary: str
    strengths: List[str]
    areas_for_improvement: List[str]

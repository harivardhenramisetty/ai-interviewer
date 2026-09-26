from pydantic import BaseModel
from typing import Literal

class CandidateProfile(BaseModel):
    candidate_summary: str
    skills: list[str]
    experience_level: str
    strengths: list[str]
    potential_gaps: list[str]
    relevant_topics: list[str]

class Question(BaseModel):
    question: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    question_type: Literal["technical", "behavioral", "situational", "project"]
    reason: str

class AnswerEvaluation(BaseModel):
    score: int
    technical_accuracy: int
    depth: int
    clarity: int
    strengths: list[str]
    weaknesses: list[str]
    feedback: str
    recommended_action: Literal["follow_up", "move_on", "increase_difficulty"]

class InterviewTurn(BaseModel):
    question: Question
    answer: str | None
    evaluation: AnswerEvaluation | None

class InterviewSession(BaseModel):
    candidate_profile: CandidateProfile
    target_role: str
    job_description: str | None
    history: list[InterviewTurn]
    current_question: Question | None
    question_number: int
    max_questions: int
    status: Literal["not_started", "in_progress", "completed"]

class QualitativeReport(BaseModel):
    strengths: list[str]
    areas_for_improvement: list[str]
    topics_demonstrated: list[str]
    recommendations: list[str]
    summary: str

class InterviewReport(BaseModel):
    overall_score: float
    technical_score: float
    depth_score: float
    clarity_score: float
    strengths: list[str]
    areas_for_improvement: list[str]
    topics_demonstrated: list[str]
    recommendations: list[str]
    summary: str

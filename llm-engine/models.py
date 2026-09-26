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

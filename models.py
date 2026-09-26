from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class CandidateProfile(BaseModel):
    name: str = Field(description="Name of the candidate")
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    experience_summary: str = Field(description="Summary of work experience")
    education_summary: str = Field(description="Summary of education")

class InterviewPlan(BaseModel):
    core_topics: List[str] = Field(default_factory=list, description="Core topics to cover in the interview")
    first_question: str = Field(description="The first question to ask the candidate")

class InitialSetup(BaseModel):
    profile: CandidateProfile = Field(description="Extracted candidate profile")
    plan: InterviewPlan = Field(description="Generated interview plan")

class ActionEnum(str, Enum):
    FOLLOW_UP = "FOLLOW_UP"
    NEW_TOPIC = "NEW_TOPIC"
    CLARIFY = "CLARIFY"
    FINISH = "FINISH"

class AdaptiveDecision(BaseModel):
    assessment: str = Field(description="Assessment of the candidate's previous answer")
    strengths: List[str] = Field(default_factory=list, description="Strengths demonstrated in the answer")
    weaknesses: List[str] = Field(default_factory=list, description="Weaknesses or gaps in the answer")
    topics_to_probe: List[str] = Field(default_factory=list, description="Topics that need further probing")
    next_action: ActionEnum = Field(description="Next action to take in the interview")
    next_question: str = Field(description="The actual next question to ask the candidate")
    reason: str = Field(description="Reasoning for the next question and action")

class FinalReport(BaseModel):
    technical_skills_evaluation: str = Field(description="Evaluation of technical skills")
    problem_solving_evaluation: str = Field(description="Evaluation of problem solving abilities")
    communication_evaluation: str = Field(description="Evaluation of communication skills")
    overall_strengths: List[str] = Field(default_factory=list, description="Overall strengths of the candidate")
    overall_weaknesses: List[str] = Field(default_factory=list, description="Overall weaknesses or gaps")
    role_alignment: str = Field(description="How well the candidate aligns with the target role")
    hire_recommendation: str = Field(description="Final recommendation (e.g., Strong Hire, Hire, No Hire)")
    summary: str = Field(description="Executive summary of the interview")

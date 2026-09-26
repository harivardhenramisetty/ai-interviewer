import os
import time
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    raise RuntimeError("Set a real GEMINI_API_KEY in your .env file.")

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-3.7-flash"


from typing import Any, Type, TypeVar
T = TypeVar("T", bound=BaseModel)

def generate_with_retry(contents: str, schema: Type[T], temperature: float, attempts: int = 3) -> Any:
    models_to_try = [MODEL, "gemini-2.5-flash", "gemini-1.5-flash"]
    for attempt in range(attempts):
        model_name = models_to_try[attempt % len(models_to_try)]
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                    "temperature": temperature,
                },
            )
        except Exception as e:
            text = str(e).upper()
            transient = any(x in text for x in (
                "503", "UNAVAILABLE", "HIGH DEMAND",
                "OVERLOADED", "429", "RESOURCE_EXHAUSTED"
            ))
            if not transient or attempt == attempts - 1:
                raise
            time.sleep(1.5 * (attempt + 1))


class CandidateProfile(BaseModel):
    name: str = "Unknown"
    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class InterviewQuestion(BaseModel):
    question: str
    topic: str
    difficulty: int = Field(ge=1, le=5)


class AnswerEvaluation(BaseModel):
    score: float = Field(ge=0, le=10)
    technical_accuracy: float = Field(ge=0, le=10)
    communication: float = Field(ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    analysis: str


class FinalReport(BaseModel):
    overall_score: float = Field(ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommendation: str
    summary: str


def _extract_parsed(response: Any, schema: Type[T]) -> dict[str, Any]:
    if response is not None:
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump()
            if isinstance(parsed, dict):
                return parsed
        text = getattr(response, "text", None)
        if text:
            return schema.model_validate_json(text).model_dump()
    raise ValueError("Empty response from AI model")


def analyze_resume(resume_text: str, target_role: str):
    prompt = f"""
You are an expert technical recruiter.

Extract the candidate information from the resume below.
Do not invent information. If something is not present, return an empty list.

Target role: {target_role}

Resume:
{resume_text}
"""

    response = generate_with_retry(prompt, CandidateProfile, 0.1)
    return _extract_parsed(response, CandidateProfile)


def generate_question(profile: dict, target_role: str, interview_history: list):
    prompt = f"""
You are conducting a realistic technical interview.

Target role:
{target_role}

Candidate profile:
{profile}

Previous interview history:
{interview_history}

Ask exactly ONE question.

Rules:
- Use the candidate's actual skills/projects.
- Do not repeat a previous question.
- Adapt difficulty based on previous answers.
- Prefer meaningful technical follow-ups over generic questions.
- If the candidate demonstrated strong understanding, go deeper.
- If the candidate struggled, test the missing concept with a simpler question.
- Do not ask about information not present in the profile unless it is a reasonable
  foundational question for the target role.
"""

    response = generate_with_retry(prompt, InterviewQuestion, 0.5)
    return _extract_parsed(response, InterviewQuestion)


def evaluate_answer(profile: dict, target_role: str, question: str, answer: str):
    prompt = f"""
You are an expert technical interviewer evaluating a candidate.

Target role:
{target_role}

Candidate profile:
{profile}

Question:
{question}

Candidate answer:
{answer}

Evaluate the answer based on correctness, depth, relevance and communication.

Do not reward length by itself.
Do not assume knowledge that the candidate did not demonstrate.
Identify concrete missing concepts.
Return a fair evaluation from 0 to 10.
"""

    response = generate_with_retry(prompt, AnswerEvaluation, 0.2)
    return _extract_parsed(response, AnswerEvaluation)


def generate_final_report(profile: dict, target_role: str, interview_history: list):
    prompt = f"""
You are a senior technical interviewer preparing a final interview report.

Target role:
{target_role}

Candidate profile:
{profile}

Complete interview:
{interview_history}

Summarize the candidate based ONLY on evidence from the interview.
Mention strengths, technical gaps, and an overall summary.
Do not invent qualifications.

The recommendation should be descriptive, such as:
"Proceed to another technical round", "Needs further assessment",
or "Strong evidence for the role".
"""

    response = generate_with_retry(prompt, FinalReport, 0.2)
    return _extract_parsed(response, FinalReport)

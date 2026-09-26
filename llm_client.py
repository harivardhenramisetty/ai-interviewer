import os
import json
import time
import google.generativeai as genai
from pydantic import ValidationError
from models import CandidateProfile, InterviewPlan, InitialSetup, AdaptiveDecision, FinalReport
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash"

def get_model():
    return genai.GenerativeModel(MODEL_NAME)

def initialize_interview_setup(resume_text: str, target_role: str, retries: int = 2) -> InitialSetup:
    """Consolidated LLM call for profile extraction and plan generation (latency optimization)"""
    model = get_model()
    prompt = f"""
    You are an expert technical interviewer.
    Task: Extract the candidate profile from the provided resume AND generate an interview plan based on the target role.
    Target Role: {target_role}
    
    Resume Text:
    {resume_text}
    """
    
    for attempt in range(retries):
        try:
            start_time = time.time()
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=InitialSetup
                )
            )
            print(f"[LLM CALL] initialize_interview_setup took {time.time() - start_time:.2f}s")
            return InitialSetup.model_validate_json(response.text)
        except ValidationError as e:
            print(f"[LLM ERROR] Validation error on setup, attempt {attempt+1}/{retries}: {e}")
            if attempt == retries - 1:
                raise e
        except Exception as e:
            print(f"[LLM ERROR] Unknown error on setup, attempt {attempt+1}/{retries}: {e}")
            if attempt == retries - 1:
                raise e

def evaluate_answer_and_decide(
    profile: CandidateProfile, 
    target_role: str, 
    interview_history: list, 
    latest_question: str, 
    latest_answer: str,
    retries: int = 2
) -> AdaptiveDecision:
    model = get_model()
    history_str = json.dumps(interview_history, indent=2)
    prompt = f"""
    You are an expert technical interviewer evaluating a candidate for the role of {target_role}.
    Candidate Profile: {profile.model_dump_json(indent=2)}
    
    Interview History so far:
    {history_str}
    
    Latest Question asked: {latest_question}
    Candidate's Answer: {latest_answer}
    
    Evaluate the candidate's answer and decide what to do next. 
    You can choose to FOLLOW_UP (dig deeper into their answer), CLARIFY (ask for clarification on something they said), NEW_TOPIC (move to a new topic from the plan), or FINISH (end the interview if enough signal is gathered).
    Generate the next question based on your decision. If FINISH, the next question can just be a polite closing statement.
    """
    
    for attempt in range(retries):
        try:
            start_time = time.time()
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=AdaptiveDecision
                )
            )
            print(f"[LLM CALL] evaluate_answer_and_decide took {time.time() - start_time:.2f}s")
            # The JSON from Gemini might be missing lists, but pydantic default_factory will safely fill them
            # Let's decode and re-encode to allow Pydantic to do its magic safely, or just validate_json
            parsed_json = json.loads(response.text)
            
            # Additional safety fallback: force missing lists to [] before validation
            for field in ['strengths', 'weaknesses', 'topics_to_probe']:
                if field not in parsed_json or parsed_json.get(field) is None:
                    parsed_json[field] = []
                    
            return AdaptiveDecision.model_validate(parsed_json)
        except ValidationError as e:
            print(f"[LLM ERROR] Validation error on evaluate, attempt {attempt+1}/{retries}: {e}")
            if attempt == retries - 1:
                raise e
        except Exception as e:
            print(f"[LLM ERROR] Unknown error on evaluate, attempt {attempt+1}/{retries}: {e}")
            if attempt == retries - 1:
                raise e

def generate_final_report(profile: CandidateProfile, target_role: str, interview_history: list, retries: int = 2) -> FinalReport:
    model = get_model()
    history_str = json.dumps(interview_history, indent=2)
    prompt = f"""
    You are an expert technical interviewer. The interview for the role of {target_role} has concluded.
    Candidate Profile: {profile.model_dump_json(indent=2)}
    
    Full Interview Transcript:
    {history_str}
    
    Based on the transcript and profile, generate a comprehensive final evaluation report.
    """
    
    for attempt in range(retries):
        try:
            start_time = time.time()
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=FinalReport
                )
            )
            print(f"[LLM CALL] generate_final_report took {time.time() - start_time:.2f}s")
            
            parsed_json = json.loads(response.text)
            for field in ['overall_strengths', 'overall_weaknesses']:
                if field not in parsed_json or parsed_json.get(field) is None:
                    parsed_json[field] = []
            
            return FinalReport.model_validate(parsed_json)
        except Exception as e:
            print(f"[LLM ERROR] Error generating report, attempt {attempt+1}/{retries}: {e}")
            if attempt == retries - 1:
                raise e

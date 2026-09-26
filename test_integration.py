import os
import fitz
from dotenv import load_dotenv
from backend.main import extract_pdf_text
from llm_engine.interview_engine import generate_candidate_profile, start_interview, submit_answer

def run_test():
    print("Loading env...")
    load_dotenv()
    
    # Verify key is present without printing it
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("ERROR: GEMINI_API_KEY is not set.")
        return
    
    # 1. Create a dummy PDF resume
    print("Creating dummy PDF...")
    pdf_path = "test_resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Alice Smith\nMachine Learning Engineer\nSkills: Python, TensorFlow, PyTorch, Streamlit\nExperience: 3 years building AI applications at DataInc.")
    doc.save(pdf_path)
    
    # 2. Simulate Upload & Extract
    print("Extracting text from PDF...")
    resume_text = extract_pdf_text(pdf_path)
    
    # 3. Initialize Interview Engine
    print("Initializing Interview Engine (this will call Gemini)...")
    target_role = "Senior AI Developer"
    profile = generate_candidate_profile(resume_text=resume_text, target_role=target_role)
    session = start_interview(candidate_profile=profile, target_role=target_role, max_questions=3)
    
    print("\n--- FIRST QUESTION ---")
    print(session.current_question.question if session.current_question else "None")
    
    # 4. Process Answer
    print("\nProcessing Answer...")
    answer = "I built a recommendation system using PyTorch and deployed it with Streamlit. It was quite challenging but successful."
    session = submit_answer(session, answer)
    
    print("\n--- LAST EVALUATION ---")
    if session.history and session.history[-1].evaluation:
        print(session.history[-1].evaluation.model_dump_json(indent=2))
    
    print("\n--- NEXT QUESTION ---")
    print(session.current_question.question if session.current_question else "Interview finished")

if __name__ == "__main__":
    run_test()


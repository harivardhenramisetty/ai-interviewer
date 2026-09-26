import os
import fitz
from dotenv import load_dotenv
from resume_parser import extract_text_from_pdf
from interview_engine import InterviewEngine

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
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    resume_text = extract_text_from_pdf(pdf_bytes)
    
    # 3. Initialize Interview Engine
    print("Initializing Interview Engine (this will call Gemini)...")
    target_role = "Senior AI Developer"
    engine = InterviewEngine(target_role=target_role, resume_text=resume_text)
    engine.initialize_interview()
    
    print("\n--- FIRST QUESTION ---")
    print(engine.current_question)
    
    # 4. Process Answer
    print("\nProcessing Answer...")
    answer = "I built a recommendation system using PyTorch and deployed it with Streamlit. It was quite challenging but successful."
    decision = engine.process_answer(answer)
    
    print("\n--- DECISION ---")
    print(decision.model_dump_json(indent=2))
    
    print("\n--- NEXT QUESTION ---")
    print(engine.current_question)

if __name__ == "__main__":
    run_test()

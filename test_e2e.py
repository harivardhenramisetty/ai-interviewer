import time
import requests
from fpdf import FPDF

API_URL = "http://127.0.0.1:8000"

def create_resume():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, text="Jane Doe", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(200, 10, text="Software Engineer with 4 years experience in Python and FastAPI.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(200, 10, text="Skills: Python, SQL, REST APIs, Microservices", new_x="LMARGIN", new_y="NEXT")
    pdf.output("test_resume.pdf")

def check_status(response, endpoint, expected=200):
    if response.status_code != expected:
        print(f"FAIL: {endpoint} returned {response.status_code}")
        print(response.text)
        return False
    return True

def run_tests():
    # 1. Root & Health
    if not check_status(requests.get(f"{API_URL}/"), "GET /"): return "FAIL at Root"
    if not check_status(requests.get(f"{API_URL}/health"), "GET /health"): return "FAIL at Health"
    
    print("PASS: Backend started and healthy")

    # 2. Upload Resume
    create_resume()
    with open("test_resume.pdf", "rb") as f:
        resp = requests.post(f"{API_URL}/upload-resume", files={"file": f})
    if not check_status(resp, "POST /upload-resume"): return "FAIL at upload"
    
    data = resp.json()
    candidate_id = data.get("candidate_id")
    print(f"PASS: Upload resume (candidate_id: {candidate_id})")

    # 3. Parse Resume
    req = {"candidate_id": candidate_id, "target_role": "Backend Developer"}
    try:
        resp = requests.post(f"{API_URL}/parse-resume", json=req)
        if not check_status(resp, "POST /parse-resume"): return "FAIL at parse"
        profile = resp.json().get("profile", {})
        print("PASS: Parse resume (Generated Profile)")
    except Exception as e:
        # Catch 503 from Gemini if quota exceeded
        print(f"Gemini API Error during parse-resume: {e}")
        return "FAIL due to Gemini Rate Limit"
        
    # 4. Start Interview
    req = {"candidate_id": candidate_id, "target_role": "Backend Developer"}
    try:
        resp = requests.post(f"{API_URL}/start-interview", json=req)
        if not check_status(resp, "POST /start-interview"): return "FAIL at start interview"
        data = resp.json()
        interview_id = data.get("interview_id")
        q1_id = data.get("question_id")
        q1_text = data.get("question")
        print(f"PASS: Start Interview. Q1: {q1_text}")
    except Exception as e:
        print(f"Gemini API Error during start-interview: {e}")
        return "FAIL due to Gemini Rate Limit"

    # 5. Submit Answer
    req = {
        "interview_id": interview_id,
        "question_id": q1_id,
        "answer": "I have extensive experience building scalable APIs in Python using FastAPI."
    }
    try:
        resp = requests.post(f"{API_URL}/submit-answer", json=req)
        if not check_status(resp, "POST /submit-answer"): return "FAIL at submit answer"
        data = resp.json()
        print(f"PASS: Submit Answer. Score: {data.get('score')}")
    except Exception as e:
        print(f"Gemini API Error during submit-answer: {e}")
        return "FAIL due to Gemini Rate Limit"

    # 6. Next Question
    try:
        resp = requests.post(f"{API_URL}/next-question/{interview_id}")
        if not check_status(resp, "POST /next-question"): return "FAIL at next question"
        data = resp.json()
        q2_id = data.get("question_id")
        q2_text = data.get("question")
        print(f"PASS: Next Question. Q2: {q2_text}")
    except Exception as e:
        print(f"Gemini API Error during next-question: {e}")
        return "FAIL due to Gemini Rate Limit"

    # 7. Submit Answer 2
    req = {
        "interview_id": interview_id,
        "question_id": q2_id,
        "answer": "To secure APIs, I use JWTs for stateless authentication and role-based access control."
    }
    try:
        resp = requests.post(f"{API_URL}/submit-answer", json=req)
        if not check_status(resp, "POST /submit-answer 2"): return "FAIL at submit answer 2"
        data = resp.json()
        print(f"PASS: Submit Answer 2. Score: {data.get('score')}")
    except Exception as e:
        print(f"Gemini API Error during submit-answer 2: {e}")
        return "FAIL due to Gemini Rate Limit"
        
    # 8. Finish Interview
    try:
        resp = requests.post(f"{API_URL}/finish-interview/{interview_id}")
        if not check_status(resp, "POST /finish-interview"): return "FAIL at finish interview"
        data = resp.json()
        print(f"PASS: Finish Interview. Overall Score: {data.get('overall_score')}")
        print(f"Strengths: {data.get('strengths')}")
        print(f"Gaps: {data.get('gaps')}")
    except Exception as e:
        print(f"Gemini API Error during finish-interview: {e}")
        return "FAIL due to Gemini Rate Limit"

    return "ALL TESTS PASSED!"

if __name__ == "__main__":
    time.sleep(2)  # Wait for uvicorn to be ready
    result = run_tests()
    print(f"\nFinal Result: {result}")

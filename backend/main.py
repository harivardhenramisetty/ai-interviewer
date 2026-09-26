from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import fitz
import sqlite3
import json
import os
import uuid
from datetime import datetime
from backend.llm_adapter import analyze_resume, generate_question, evaluate_answer, generate_final_report

app = FastAPI(
    title="AI Interview Bot API",
    description="AI-powered adaptive interview platform",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
DB_FILE = "interview.db"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            name TEXT,
            resume_text TEXT,
            profile TEXT,
            target_role TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id TEXT PRIMARY KEY,
            candidate_id TEXT,
            target_role TEXT,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY(candidate_id) REFERENCES candidates(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            interview_id TEXT,
            question_number INTEGER,
            question TEXT,
            topic TEXT,
            difficulty INTEGER,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id TEXT PRIMARY KEY,
            question_id TEXT,
            interview_id TEXT,
            answer TEXT,
            score REAL,
            analysis TEXT,
            FOREIGN KEY(question_id) REFERENCES questions(id),
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS integrity_events (
            id TEXT PRIMARY KEY,
            interview_id TEXT,
            event_type TEXT,
            confidence REAL,
            timestamp TEXT,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


def call_ai(function, *args):
    try:
        return function(*args)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service temporarily unavailable: {str(e)}"
        )


# =========================================================
# MODELS
# =========================================================

class CandidateProfile(BaseModel):
    name: str = "Unknown"
    education: list[str] = []
    skills: list[str] = []
    projects: list[str] = []
    experience: list[str] = []
    certifications: list[str] = []


class ParseResumeRequest(BaseModel):
    candidate_id: str
    target_role: str


class StartInterviewRequest(BaseModel):
    candidate_id: str
    target_role: str


class SubmitAnswerRequest(BaseModel):
    interview_id: str
    question_id: str
    answer: str


class IntegrityEventRequest(BaseModel):
    interview_id: str
    event_type: str
    confidence: float = 0.0


# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def extract_pdf_text(file_path):
    try:
        doc = fitz.open(file_path)

        text = ""

        for page in doc:
            text += page.get_text()

        doc.close()

        return text.strip()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF extraction failed: {str(e)}"
        )


def generate_basic_profile(text):
    """
    Temporary profile extraction.

    Later replace this with an LLM call.
    """

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    skills = []

    possible_skills = [
        "Python",
        "C",
        "C++",
        "Java",
        "JavaScript",
        "SQL",
        "HTML",
        "CSS",
        "React",
        "FastAPI",
        "Flask",
        "Machine Learning",
        "Deep Learning",
        "TensorFlow",
        "PyTorch",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "OpenCV",
        "MediaPipe"
    ]

    text_lower = text.lower()

    for skill in possible_skills:
        if skill.lower() in text_lower:
            skills.append(skill)

    profile = {
        "name": lines[0] if lines else "Unknown",
        "education": [],
        "skills": skills,
        "projects": [],
        "experience": [],
        "certifications": []
    }

    return profile


# =========================================================
# BASIC API
# =========================================================

@app.get("/")
def home():
    return {
        "message": "AI Interview Bot API is running",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AI Interview Bot"
    }


# =========================================================
# RESUME UPLOAD
# =========================================================

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are supported"
        )

    candidate_id = str(uuid.uuid4())

    filename = f"{candidate_id}.pdf"

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    contents = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    text = extract_pdf_text(file_path)

    profile = generate_basic_profile(text)

    conn = get_db()

    conn.execute("""
        INSERT INTO candidates
        (id, name, resume_text, profile, target_role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        profile["name"],
        text,
        json.dumps(profile),
        "",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "candidate_id": candidate_id,
        "filename": file.filename,
        "extracted_text": text,
        "profile": profile
    }


# =========================================================
# GET CANDIDATE
# =========================================================

@app.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: str):

    conn = get_db()

    candidate = conn.execute("""
        SELECT *
        FROM candidates
        WHERE id = ?
    """, (candidate_id,)).fetchone()

    conn.close()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    return {
        "id": candidate["id"],
        "name": candidate["name"],
        "resume_text": candidate["resume_text"],
        "profile": json.loads(candidate["profile"]),
        "target_role": candidate["target_role"],
        "created_at": candidate["created_at"]
    }


# =========================================================
# PARSE / UPDATE PROFILE
# =========================================================

@app.post("/parse-resume")
def parse_resume(request: ParseResumeRequest):

    conn = get_db()

    candidate = conn.execute("""
        SELECT *
        FROM candidates
        WHERE id = ?
    """, (request.candidate_id,)).fetchone()

    conn.close()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    profile = call_ai(analyze_resume, candidate["resume_text"], request.target_role)

    conn = get_db()

    conn.execute("""
        UPDATE candidates
        SET name = ?, profile = ?, target_role = ?
        WHERE id = ?
    """, (
        profile["name"],
        json.dumps(profile),
        request.target_role,
        request.candidate_id
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "candidate_id": request.candidate_id,
        "target_role": request.target_role,
        "profile": profile
    }


# =========================================================
# START INTERVIEW
# =========================================================

@app.post("/start-interview")
def start_interview(request: StartInterviewRequest):

    conn = get_db()

    candidate = conn.execute("""
        SELECT *
        FROM candidates
        WHERE id = ?
    """, (request.candidate_id,)).fetchone()

    if not candidate:
        conn.close()
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview_id = str(uuid.uuid4())
    profile = json.loads(candidate["profile"])
    conn.close()

    question_data = call_ai(generate_question, profile, request.target_role, [])

    conn = get_db()

    conn.execute("""
        UPDATE candidates
        SET target_role = ?
        WHERE id = ?
    """, (request.target_role, request.candidate_id))

    conn.execute("""
        INSERT INTO interviews
        (id, candidate_id, target_role, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        interview_id,
        request.candidate_id,
        request.target_role,
        "active",
        datetime.now().isoformat()
    ))

    conn.commit()

    question_id = str(uuid.uuid4())

    conn = get_db()
    conn.execute("""
        INSERT INTO questions
        (id, interview_id, question_number, question, topic, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        question_id,
        interview_id,
        1,
        question_data["question"],
        question_data["topic"],
        question_data["difficulty"]
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "interview_id": interview_id,
        "question_id": question_id,
        "question_number": 1,
        "question": question_data["question"],
        "topic": question_data["topic"],
        "difficulty": question_data["difficulty"]
    }


# =========================================================
# GET INTERVIEW
# =========================================================

@app.get("/interview/{interview_id}")
def get_interview(interview_id: str):

    conn = get_db()

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE id = ?
    """, (interview_id,)).fetchone()

    if not interview:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )

    questions = conn.execute("""
        SELECT *
        FROM questions
        WHERE interview_id = ?
        ORDER BY question_number
    """, (interview_id,)).fetchall()

    answers = conn.execute("""
        SELECT *
        FROM answers
        WHERE interview_id = ?
    """, (interview_id,)).fetchall()

    conn.close()

    return {
        "interview": dict(interview),
        "questions": [dict(q) for q in questions],
        "answers": [dict(a) for a in answers]
    }


# =========================================================
# SUBMIT ANSWER
# =========================================================

@app.post("/submit-answer")
def submit_answer(request: SubmitAnswerRequest):

    conn = get_db()

    question = conn.execute("""
        SELECT *
        FROM questions
        WHERE id = ?
    """, (request.question_id,)).fetchone()

    if not question:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found")

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE id = ?
    """, (request.interview_id,)).fetchone()

    if not interview:
        conn.close()
        raise HTTPException(status_code=404, detail="Interview not found")

    if question["interview_id"] != request.interview_id:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Question does not belong to this interview"
        )

    if not request.answer.strip():
        conn.close()
        raise HTTPException(status_code=400, detail="Answer cannot be empty")

    candidate = conn.execute("""
        SELECT *
        FROM candidates
        WHERE id = ?
    """, (interview["candidate_id"],)).fetchone()

    conn.close()

    profile = json.loads(candidate["profile"])

    evaluation = call_ai(evaluate_answer, profile, interview["target_role"], question["question"], request.answer)

    answer_id = str(uuid.uuid4())

    conn = get_db()
    conn.execute("""
        INSERT INTO answers
        (id, question_id, interview_id, answer, score, analysis)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        answer_id,
        request.question_id,
        request.interview_id,
        request.answer,
        evaluation["score"],
        json.dumps(evaluation)
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "answer_id": answer_id,
        **evaluation,
        "message": "Answer recorded successfully"
    }


# =========================================================
# GENERATE NEXT QUESTION
# =========================================================

@app.post("/next-question/{interview_id}")
def next_question(interview_id: str):

    conn = get_db()

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE id = ?
    """, (interview_id,)).fetchone()

    if not interview:
        conn.close()
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview["status"] != "active":
        conn.close()
        raise HTTPException(status_code=400, detail="Interview is not active")

    questions = conn.execute("""
        SELECT *
        FROM questions
        WHERE interview_id = ?
        ORDER BY question_number
    """, (interview_id,)).fetchall()

    answers = conn.execute("""
        SELECT *
        FROM answers
        WHERE interview_id = ?
        ORDER BY rowid
    """, (interview_id,)).fetchall()

    candidate = conn.execute("""
        SELECT *
        FROM candidates
        WHERE id = ?
    """, (interview["candidate_id"],)).fetchone()

    conn.close()

    next_number = len(questions) + 1

    if next_number > 6:
        return {
            "success": True,
            "finished": True,
            "message": "Interview has reached the maximum number of questions."
        }

    history = []

    for i, q in enumerate(questions):
        item = {
            "question": q["question"],
            "topic": q["topic"],
            "difficulty": q["difficulty"]
        }

        if i < len(answers):
            item["answer"] = answers[i]["answer"]
            try:
                item["evaluation"] = json.loads(answers[i]["analysis"])
            except Exception:
                item["evaluation"] = answers[i]["analysis"]

        history.append(item)

    profile = json.loads(candidate["profile"])

    question_data = call_ai(generate_question, profile, interview["target_role"], history)

    question_id = str(uuid.uuid4())

    conn = get_db()
    conn.execute("""
        INSERT INTO questions
        (id, interview_id, question_number, question, topic, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        question_id,
        interview_id,
        next_number,
        question_data["question"],
        question_data["topic"],
        question_data["difficulty"]
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "finished": False,
        "question_id": question_id,
        "question_number": next_number,
        "question": question_data["question"],
        "topic": question_data["topic"],
        "difficulty": question_data["difficulty"]
    }


# =========================================================
# INTEGRITY MONITORING
# =========================================================

@app.post("/integrity-event")
def integrity_event(request: IntegrityEventRequest):

    event_id = str(uuid.uuid4())

    conn = get_db()

    conn.execute("""
        INSERT INTO integrity_events
        (id, interview_id, event_type, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        event_id,
        request.interview_id,
        request.event_type,
        request.confidence,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "event_id": event_id,
        "event_type": request.event_type,
        "confidence": request.confidence
    }


# =========================================================
# FINISH INTERVIEW
# =========================================================

@app.post("/finish-interview/{interview_id}")
def finish_interview(interview_id: str):

    conn = get_db()

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE id = ?
    """, (interview_id,)).fetchone()

    if not interview:
        conn.close()
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview["status"] == "completed":
        conn.close()
        raise HTTPException(status_code=400, detail="Interview is already completed")

    answers = conn.execute("""
        SELECT *
        FROM answers
        WHERE interview_id = ?
        ORDER BY rowid
    """, (interview_id,)).fetchall()

    questions = conn.execute("""
        SELECT *
        FROM questions
        WHERE interview_id = ?
        ORDER BY question_number
    """, (interview_id,)).fetchall()

    candidate = conn.execute("""
        SELECT *
        FROM candidates
        WHERE id = ?
    """, (interview["candidate_id"],)).fetchone()

    integrity_events = conn.execute("""
        SELECT *
        FROM integrity_events
        WHERE interview_id = ?
    """, (interview_id,)).fetchall()

    history = []

    for i, q in enumerate(questions):
        item = {
            "question": q["question"],
            "topic": q["topic"],
            "difficulty": q["difficulty"]
        }

        if i < len(answers):
            item["answer"] = answers[i]["answer"]
            try:
                item["evaluation"] = json.loads(answers[i]["analysis"])
            except Exception:
                item["evaluation"] = answers[i]["analysis"]

        history.append(item)

    profile = json.loads(candidate["profile"])

    report = call_ai(generate_final_report, profile, interview["target_role"], history)

    conn.execute("""
        UPDATE interviews
        SET status = ?
        WHERE id = ?
    """, ("completed", interview_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "interview_id": interview_id,
        "status": "completed",
        "overall_score": report["overall_score"],
        "questions_answered": len(answers),
        "integrity_events": len(integrity_events),
        "strengths": report["strengths"],
        "gaps": report["gaps"],
        "recommendation": report["recommendation"],
        "summary": report["summary"]
    }


# =========================================================
# RUNNING INSTRUCTIONS
# =========================================================

# Run:
#
# uvicorn main:app --reload
#
# Swagger:
#
# http://127.0.0.1:8000/docs
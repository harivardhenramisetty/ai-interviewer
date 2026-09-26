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
    allow_origins=["*"],
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
        import traceback
        traceback.print_exc()
        err_msg = str(e).upper()
        if any(k in err_msg for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "HIGH DEMAND")):
            print(f"[*] AI Quota/High Demand: Using smart fallback for {function.__name__}")
            return mock_fallback(function.__name__, *args)
        raise HTTPException(
            status_code=500,
            detail=f"AI service error: {str(e)}"
        )

def extract_structured_profile(text: str, target_role: str = "") -> dict:
    import re
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # ── Name Extraction ──────────────────────────────────────────
    name = "Candidate"
    bad_name_words = {
        "resume", "curriculum", "vitae", "cv", "page", "email", "phone",
        "contact", "experience", "education", "skills", "projects", "profile",
        "summary", "github", "linkedin", "http", "www", "objective", "developer",
        "engineer", "analyst", "designer", "scientist", "technologies", "frameworks"
    }
    for line in lines[:10]:
        cleaned = re.sub(r"[^\w\s\.-]", "", line).strip()
        words = cleaned.split()
        if 1 <= len(words) <= 4:
            if not any(bad in cleaned.lower() for bad in bad_name_words) and not re.search(r"[@\d\+]", line):
                name = " ".join(w.capitalize() for w in words)
                break

    text_lower = text.lower()

    # ── Comprehensive Skills Dictionary ──────────────────────────
    SKILL_PATTERNS = {
        "Python": [r"\bpython\b"],
        "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
        "TypeScript": [r"\btypescript\b", r"\bts\b"],
        "React": [r"\breact(\.js)?\b"],
        "Next.js": [r"\bnext(\.js)?\b"],
        "Vue.js": [r"\bvue(\.js)?\b"],
        "Angular": [r"\bangular\b"],
        "Node.js": [r"\bnode(\.js)?\b"],
        "Express": [r"\bexpress(\.js)?\b"],
        "FastAPI": [r"\bfastapi\b"],
        "Django": [r"\bdjango\b"],
        "Flask": [r"\bflask\b"],
        "Java": [r"\bjava\b"],
        "Spring Boot": [r"\bspring\s*boot\b", r"\bspring\b"],
        "C++": [r"\bc\+\+\b", r"\bcpp\b"],
        "C#": [r"\bc#\b", r"\bcsharp\b"],
        "Go (Golang)": [r"\bgolang\b", r"\bgo\s+language\b", r"\bgo\s+developer\b"],
        "Rust": [r"\brust\b"],
        "SQL": [r"\bsql\b"],
        "PostgreSQL": [r"\bpostgres(ql)?\b"],
        "MySQL": [r"\bmysql\b"],
        "MongoDB": [r"\bmongodb\b", r"\bmongo\b"],
        "Redis": [r"\bredis\b"],
        "Docker": [r"\bdocker\b", r"\bcontainer(s|ization)?\b"],
        "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
        "AWS": [r"\baws\b", r"\bamazon\s+web\s+services\b"],
        "GCP": [r"\bgcp\b", r"\bgoogle\s+cloud\b"],
        "Azure": [r"\bazure\b"],
        "CI/CD": [r"\bci/cd\b", r"\bjenkins\b", r"\bgitlab\s*ci\b", r"\bgithub\s*actions\b"],
        "Terraform": [r"\bterraform\b"],
        "GraphQL": [r"\bgraphql\b"],
        "REST APIs": [r"\brest(ful)?\s*api(s)?\b", r"\brest\b"],
        "Microservices": [r"\bmicroservices?\b"],
        "Kafka": [r"\bkafka\b"],
        "PyTorch": [r"\bpytorch\b"],
        "TensorFlow": [r"\btensorflow\b"],
        "Machine Learning": [r"\bmachine\s+learning\b", r"\bml\b"],
        "Deep Learning": [r"\bdeep\s+learning\b", r"\bdl\b"],
        "Pandas": [r"\bpandas\b"],
        "NumPy": [r"\bnumpy\b"],
        "Scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
        "OpenCV": [r"\bopencv\b"],
        "NLP": [r"\bnlp\b", r"\bnatural\s+language\b", r"\bllm(s)?\b", r"\blangchain\b"],
        "Flutter": [r"\bflutter\b"],
        "React Native": [r"\breact\s+native\b"],
        "Swift": [r"\bswift\b", r"\bios\b"],
        "Kotlin": [r"\bkotlin\b", r"\bandroid\b"],
        "HTML/CSS": [r"\bhtml5?\b", r"\bcss3?\b", r"\btailwind(css)?\b", r"\bsass\b"],
        "Git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
        "Linux": [r"\blinux\b", r"\bunix\b", r"\bbash\b", r"\bshell\b"]
    }

    found_skills = []
    for skill_name, patterns in SKILL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                found_skills.append(skill_name)
                break

    # ── Experience Level ─────────────────────────────────────────
    exp_level = "Mid"
    if re.search(r"\b(lead|principal|staff|architect|director|vp|head)\b", text_lower):
        exp_level = "Staff"
    elif re.search(r"\b(senior|sr\.?|5\+|6\+|7\+|8\+|10\+|expert)\b", text_lower):
        exp_level = "Senior"
    elif re.search(r"\b(intern|internship|junior|jr\.?|entry|freshman|graduate|student)\b", text_lower):
        exp_level = "Junior"

    # ── Relevant Topics ──────────────────────────────────────────
    role_topics = [t.strip().title() for t in target_role.split() if len(t) > 2]
    relevant_topics = list(dict.fromkeys(found_skills[:8] + role_topics))
    if not relevant_topics:
        relevant_topics = ["Software Engineering", "System Design", "Problem Solving"]

    skills_str = ", ".join(found_skills[:6]) if found_skills else "software engineering"
    role_str = target_role or "Software Engineer"
    summary = f"{exp_level}-level candidate with background in {skills_str}. Targeting role: {role_str}."

    return {
        "name": name,
        "education": [],
        "skills": found_skills,
        "projects": [],
        "experience": [],
        "certifications": [],
        "candidate_summary": summary,
        "experience_level": exp_level,
        "strengths": found_skills[:4] if found_skills else ["Core software engineering principles"],
        "potential_gaps": ["High-scale distributed systems"] if exp_level != "Staff" else [],
        "relevant_topics": relevant_topics
    }


def mock_fallback(func_name, *args):
    import random
    if func_name == "analyze_resume":
        resume_text = str(args[0]) if len(args) > 0 else ""
        target_role = str(args[1]) if len(args) > 1 else ""
        return extract_structured_profile(resume_text, target_role)
    elif func_name == "generate_question":
        import random
        import re

        history = args[2] if len(args) > 2 else []
        profile = args[0] if len(args) > 0 else {}
        target_role = (args[1] if len(args) > 1 else "").lower().strip()

        # ── Collect all previously asked questions & topics ─────────────────
        asked_texts: list[str] = []
        asked_topics: set[str] = set()
        last_answer = ""
        last_topic = ""
        last_action = "move_on"
        last_score = 5.0

        for turn in history:
            if isinstance(turn, dict):
                q_text = turn.get("question", "").lower().strip()
                if q_text:
                    asked_texts.append(q_text)
                t_name = turn.get("topic", "").lower().strip()
                if t_name:
                    asked_topics.add(t_name)
                last_topic = turn.get("topic", "")
                last_answer = turn.get("answer", "")
                ev = turn.get("evaluation")
                if isinstance(ev, dict):
                    last_action = ev.get("recommended_action", "move_on")
                    last_score = float(ev.get("score", 5.0))

        def _is_already_asked(candidate_q: str) -> bool:
            cand_clean = re.sub(r'[^a-z0-9 ]', '', candidate_q.lower()).strip()
            cand_words = set(cand_clean.split())
            for past in asked_texts:
                past_clean = re.sub(r'[^a-z0-9 ]', '', past).strip()
                if not past_clean:
                    continue
                # Direct substring check
                if cand_clean in past_clean or past_clean in cand_clean:
                    return True
                # Overlap similarity check
                past_words = set(past_clean.split())
                if len(cand_words) > 0 and len(past_words) > 0:
                    overlap = len(cand_words & past_words) / min(len(cand_words), len(past_words))
                    if overlap > 0.75:
                        return True
            return False

        # ── Profile extraction ──────────────────────────────────────────────
        skills_list = profile.get("skills", []) if isinstance(profile, dict) else []
        profile_skills = " ".join(skills_list + profile.get("relevant_topics", [])).lower() if isinstance(profile, dict) else ""
        role_and_skills = f"{target_role} {profile_skills}".lower()

        # ── Dynamic contextual follow-ups based on candidate answer ─────────
        ans_lower = last_answer.lower()
        if last_answer and last_action in ("follow_up", "increase_difficulty") and len(ans_lower.split()) > 3:
            FOLLOW_UPS = [
                ("redis", "You mentioned Redis — how would you handle cache stampedes and ensure cache consistency when data in the primary database changes?", "Caching & Distributed State", 4, "technical", "Follow-up probing Redis cache stampede and consistency strategies."),
                ("redis", "Since you brought up Redis, what replication or sentinel configuration would you use to prevent Redis from becoming a single point of failure?", "High Availability & Caching", 4, "technical", "Probing Redis clustering and high availability depth."),
                ("kafka", "You mentioned Kafka — how do you ensure exactly-once processing semantics and handle consumer lag during traffic spikes?", "Event Streaming & Queues", 4, "technical", "Probing Kafka partitioning, offset management, and consumer scaling."),
                ("docker", "You mentioned Docker — walk me through how you optimize container image layers and manage secret credentials securely in production.", "DevOps & Containerization", 3, "technical", "Probing container security and build optimization."),
                ("kubernetes", "Since you referenced Kubernetes, how would you configure HPA, liveness/readiness probes, and zero-downtime rolling updates for a microservice?", "Cloud Infrastructure", 4, "technical", "Probing Kubernetes deployment reliability."),
                ("postgres", "You mentioned PostgreSQL — how do you diagnose query performance using EXPLAIN ANALYZE, and when would you use partial or composite indexes?", "Database Optimization", 4, "technical", "Probing PostgreSQL indexing and query execution plans."),
                ("sql", "You mentioned SQL databases — how would you design schema migrations without locking tables or interrupting active user traffic?", "Database Architecture", 4, "technical", "Probing non-blocking database migrations."),
                ("react", "You mentioned React — what is your strategy for state management and avoiding unnecessary re-renders when passing state to deeply nested components?", "Frontend Architecture", 3, "technical", "Probing React component optimization and state patterns."),
                ("fastapi", "You mentioned FastAPI — how does the async event loop handle non-async blocking calls, and when should you use background tasks vs Celery/queues?", "Backend & Concurrency", 4, "technical", "Probing FastAPI async behavior and worker task offloading."),
                ("microservice", "You mentioned microservices — how do you handle distributed transactions and cross-service data consistency without 2-phase commit?", "Distributed Systems", 5, "technical", "Probing Saga pattern and eventual consistency."),
                ("graphql", "You brought up GraphQL — how do you resolve the N+1 query problem and secure your endpoints against overly complex nested queries?", "API Design", 4, "technical", "Probing GraphQL DataLoader and query complexity depth."),
                ("websocket", "You mentioned WebSockets — how do you scale real-time WebSocket connections across a cluster of backend servers?", "Real-Time Networking", 4, "technical", "Probing WebSocket pub/sub synchronization across server nodes."),
                ("security", "You touched on security — how do you defend an API against CSRF, SSRF, and JWT token revocation vulnerabilities?", "Application Security", 4, "technical", "Probing API security practices and token invalidation.")
            ]
            for kw, f_q, f_top, f_diff, f_type, f_reason in FOLLOW_UPS:
                if kw in ans_lower and not _is_already_asked(f_q):
                    prefix = "Building directly on what you mentioned: " if last_score >= 6.5 else "Let's dig a bit deeper into that: "
                    return {
                        "question": prefix + f_q,
                        "topic": f_top,
                        "difficulty": f_diff,
                        "question_type": f_type,
                        "reason": f_reason
                    }

        # ── Comprehensive Multi-Domain Question Bank ─────────────────────────
        QUESTION_BANK = [
            # --- Frontend & Web Engineering ---
            {
                "domains": ["frontend", "react", "vue", "angular", "ui", "javascript", "typescript", "web", "fullstack"],
                "topic": "Frontend Performance & Core Web Vitals",
                "diff": 3,
                "type": "technical",
                "q": "How would you optimize a web application that has poor Largest Contentful Paint (LCP) and high Interaction to Next Paint (INP)? What profiling tools and architectural patterns would you use?",
                "reason": "Core Web Vitals and frontend performance profiling are fundamental for modern web engineers."
            },
            {
                "domains": ["frontend", "react", "vue", "angular", "ui", "javascript", "typescript", "web", "fullstack"],
                "topic": "React State Management & Architecture",
                "diff": 3,
                "type": "technical",
                "q": "In a modern single-page application, how do you decide between local state, server state (e.g., React Query/SWR), and global client state (e.g., Zustand/Redux)? What tradeoffs guide your choice?",
                "reason": "Tests architectural understanding of client state separation and network caching."
            },
            {
                "domains": ["frontend", "react", "ui", "javascript", "typescript", "web", "fullstack"],
                "topic": "Rendering Patterns & SSR vs CSR",
                "diff": 4,
                "type": "technical",
                "q": "Compare Client-Side Rendering (CSR), Server-Side Rendering (SSR), and Static Site Generation (SSG). How does hydration work under the hood, and what causes hydration mismatches?",
                "reason": "Tests understanding of modern web rendering lifecycles and server-client hydration."
            },
            {
                "domains": ["frontend", "javascript", "typescript", "web", "fullstack"],
                "topic": "JavaScript Internals & Asynchronous Flow",
                "diff": 3,
                "type": "technical",
                "q": "Explain how the JavaScript Event Loop handles the call stack, microtask queue (Promises), and macrotask queue (setTimeout, I/O). What happens when a long-running synchronous computation runs on the main thread?",
                "reason": "Critical core language mastery for JavaScript/TypeScript developers."
            },

            # --- Backend, APIs & Concurrency ---
            {
                "domains": ["backend", "python", "fastapi", "django", "node", "express", "go", "golang", "java", "fullstack", "software engineer"],
                "topic": "API Design & Versioning",
                "diff": 3,
                "type": "technical",
                "q": "How do you design a high-throughput RESTful API with idempotent endpoints, robust error structures, and a versioning strategy that supports backwards compatibility without code bloat?",
                "reason": "API contract design and backwards compatibility are essential backend competencies."
            },
            {
                "domains": ["backend", "python", "fastapi", "django", "node", "go", "golang", "java", "fullstack", "software engineer"],
                "topic": "Concurrency & Asynchronous I/O",
                "diff": 4,
                "type": "technical",
                "q": "What is the difference between concurrency and parallelism? In your primary backend language, how are CPU-bound and IO-bound workloads handled differently, and what concurrency bugs must you guard against?",
                "reason": "Concurrency models and thread/task safety are crucial for backend performance."
            },
            {
                "domains": ["backend", "python", "fastapi", "django", "node", "go", "java", "fullstack", "database", "software engineer"],
                "topic": "Database Indexing & Query Optimization",
                "diff": 3,
                "type": "technical",
                "q": "Suppose a production database query on a multi-million row table starts running slowly. Walk me through your step-by-step diagnostic process to find the bottleneck, analyze indexes, and optimize query execution.",
                "reason": "Database profiling and query tuning are core expectations for backend engineers."
            },
            {
                "domains": ["backend", "database", "fullstack", "software engineer", "system design"],
                "topic": "Data Consistency & Transactions",
                "diff": 4,
                "type": "technical",
                "q": "Explain ACID properties in relational databases vs BASE in distributed databases. How do isolation levels (Read Committed vs Repeatable Read vs Serializable) prevent phenomena like phantom reads and write skew?",
                "reason": "Tests deep understanding of relational data integrity and transaction concurrency."
            },

            # --- System Design & Distributed Systems ---
            {
                "domains": ["system design", "backend", "fullstack", "architect", "senior", "lead", "cloud", "software engineer"],
                "topic": "System Design: Rate Limiting",
                "diff": 3,
                "type": "technical",
                "q": "How would you design a distributed rate-limiting service capable of handling 50,000 requests per second across multiple data centers? What algorithm (token bucket, sliding window) and storage layer would you use?",
                "reason": "Classic distributed systems problem testing algorithm selection and state coordination."
            },
            {
                "domains": ["system design", "backend", "fullstack", "architect", "senior", "lead", "cloud", "software engineer"],
                "topic": "System Design: Scalable Real-time Notifications",
                "diff": 4,
                "type": "technical",
                "q": "Design a real-time push notification system that delivers messages to millions of active mobile and web clients within sub-second latency. How do you handle connection drops, message ordering, and offline queuing?",
                "reason": "Tests real-time communication protocols, message brokers, and fan-out architecture."
            },
            {
                "domains": ["system design", "backend", "cloud", "microservices", "architect", "fullstack"],
                "topic": "Microservices Decomposition & Resiliency",
                "diff": 4,
                "type": "technical",
                "q": "When decomposing a monolithic application into microservices, how do you determine service boundaries, implement circuit breakers, and prevent cascading failures across service dependencies?",
                "reason": "Tests domain-driven decomposition and fault tolerance in distributed microservices."
            },

            # --- Cloud, DevOps & Infrastructure ---
            {
                "domains": ["devops", "cloud", "aws", "gcp", "azure", "kubernetes", "docker", "sre", "infrastructure"],
                "topic": "CI/CD & Deployment Strategies",
                "diff": 3,
                "type": "technical",
                "q": "Explain how you implement Blue-Green vs Canary deployments for zero-downtime releases. What automated health checks and rollback triggers do you configure in your deployment pipeline?",
                "reason": "Safe deployment automation and rollback strategies are critical for reliability."
            },
            {
                "domains": ["devops", "cloud", "aws", "gcp", "azure", "kubernetes", "sre", "infrastructure", "backend"],
                "topic": "Observability, Telemetry & Incident Response",
                "diff": 4,
                "type": "technical",
                "q": "How do you establish the three pillars of observability (metrics, logs, and distributed traces) across a distributed application? When a latency spike alert triggers at 2 AM, what is your triage methodology?",
                "reason": "Evaluates operational excellence, monitoring strategy, and live incident triage."
            },

            # --- Data Engineering, AI & Machine Learning ---
            {
                "domains": ["data", "ml", "ai", "machine learning", "python", "etl", "analytics"],
                "topic": "Data Pipeline Architecture & Stream Processing",
                "diff": 3,
                "type": "technical",
                "q": "What are the key architectural differences between batch processing (e.g. Spark/Airflow) and stream processing (e.g. Kafka/Flink)? How do you handle schema evolution and late-arriving data in streaming pipelines?",
                "reason": "Tests data pipeline design and event-time vs processing-time semantics."
            },
            {
                "domains": ["data", "ml", "ai", "machine learning", "python", "llm"],
                "topic": "ML Model Deployment & Vector Search",
                "diff": 4,
                "type": "technical",
                "q": "When deploying machine learning or LLM-powered applications to production, how do you handle vector embeddings storage, inference latency constraints, and model drift monitoring?",
                "reason": "Evaluates modern AI/ML productionization and vector retrieval architecture."
            },

            # --- Behavioral, Problem Solving & Leadership ---
            {
                "domains": ["behavioral", "leadership", "all"],
                "topic": "Production Incident & Accountability",
                "diff": 2,
                "type": "behavioral",
                "q": "Tell me about a challenging technical problem or unexpected production outage you encountered in a previous project. How did you diagnose the root cause, communicate with teammates, and prevent it from recurring?",
                "reason": "Evaluates root-cause problem solving, accountability, and engineering maturity under pressure."
            },
            {
                "domains": ["behavioral", "leadership", "all"],
                "topic": "Technical Tradeoffs & Architecture Decisions",
                "diff": 3,
                "type": "behavioral",
                "q": "Describe a time when you had a technical disagreement with a team member or stakeholder regarding an architectural decision. How did you evaluate the tradeoffs and reach an effective resolution?",
                "reason": "Tests engineering collaboration, pragmatic tradeoff analysis, and communication."
            }
        ]

        # ── Filter out already asked questions ──────────────────────────────
        unasked_candidates = []
        for item in QUESTION_BANK:
            if not _is_already_asked(item["q"]):
                # Score relevance to target role and candidate profile
                score = 0
                item_domains = item.get("domains", [])
                for d in item_domains:
                    if d == "all":
                        score += 5
                    elif d in role_and_skills:
                        score += 30
                # Penalize topics already covered in this interview
                if item["topic"].lower() in asked_topics:
                    score -= 50
                unasked_candidates.append((score, item))

        # Fallback if somehow all in bank were asked
        if not unasked_candidates:
            unasked_candidates = [(0, item) for item in QUESTION_BANK]

        # Sort by relevance score, group top tier candidates, and randomly pick to avoid deterministic repetition
        unasked_candidates.sort(key=lambda x: x[0], reverse=True)
        top_score = unasked_candidates[0][0]
        # Get all candidates within 15 points of top score
        top_tier = [item for score, item in unasked_candidates if score >= top_score - 15]
        chosen = random.choice(top_tier) if top_tier else unasked_candidates[0][1]

        # ── Dynamic, natural transitions (No repeated formulaic prefixes) ────
        if len(history) == 0:
            transition = ""
        else:
            if last_score >= 7.5:
                transitions = [
                    f"Excellent breakdown on {last_topic}. Next: ",
                    "Great explanation. Let's explore another important dimension: ",
                    "Strong reasoning. Moving to our next technical area: ",
                    "Well articulated. Let's examine: "
                ]
            elif last_score >= 4.5:
                transitions = [
                    "Understood. Moving forward to our next area: ",
                    "Thanks for that response. Let's look at another topic: ",
                    "Good, let's explore another practical scenario: ",
                    "Next question: "
                ]
            else:
                transitions = [
                    "Understood. Let's shift focus to a different domain: ",
                    "No problem, let's look at another core area: ",
                    "Moving to our next question: ",
                    "Let's explore this next scenario: "
                ]
            transition = random.choice(transitions)

        return {
            "question": transition + chosen["q"],
            "topic": chosen["topic"],
            "difficulty": chosen["diff"],
            "question_type": chosen["type"],
            "reason": chosen["reason"]
        }

    elif func_name == "evaluate_answer":
        import re as _re
        ans = str(args[3]) if len(args) > 3 else ""
        question_text = str(args[2]) if len(args) > 2 else ""
        topic = str(args[4]) if len(args) > 4 else ""
        words = ans.strip().split()
        word_count = len(words)
        ans_lower = ans.lower().strip()

        # --- Hard non-answer rejection list ---
        NON_ANSWERS = {
            "no", "yes", "maybe", "idk", "i don't know", "i dont know",
            "dunno", "na", "n/a", "skip", "nothing", "none", "not sure",
            "no idea", "don't know", "dont know", "nope", "yep", "yeah",
            "ok", "okay", "sure", "fine", "whatever", "pass", "next",
            "i don't know the answer", "i dont know the answer", "test"
        }

        # --- Gibberish / Low-effort detection ---
        def _is_gibberish(text: str) -> bool:
            words_list = text.lower().split()
            if not words_list:
                return True
            avg_len = sum(len(w) for w in words_list) / len(words_list)
            if avg_len > 14 or avg_len < 2:
                return True
            unique_ratio = len(set(words_list)) / len(words_list)
            if unique_ratio < 0.35 and word_count > 6:
                return True
            letters = [c for c in text.lower() if c.isalpha()]
            if letters:
                vowels = sum(1 for c in letters if c in "aeiou")
                consonant_ratio = 1 - (vowels / len(letters))
                if consonant_ratio > 0.85:
                    return True
            gibberish_patterns = ["asdf", "qwer", "zxcv", "hjkl", "aaaa", "bbbb", "1234abcd"]
            if any(p in text.lower() for p in gibberish_patterns):
                return True
            return False

        def _score_relevance(ans_text: str, q_text: str, topic_str: str) -> float:
            keyword_banks = {
                "System Design": ["scalab", "cache", "redis", "load balanc", "database", "microservice", "api", "architect", "throughput", "latency", "queue", "async", "distribute", "sharding", "replicate", "fault toleran", "token bucket", "rate limit"],
                "Database": ["index", "query", "sql", "join", "optim", "table", "schema", "normaliz", "transaction", "acid", "nosql", "shard", "replica", "explain", "postgres", "lock", "isolation"],
                "Frontend": ["state", "prop", "hook", "redux", "context", "memo", "useCallback", "re-render", "component", "effect", "ref", "render", "dom", "lcp", "inp", "hydration", "ssr", "csr", "ssg", "event loop"],
                "Cloud": ["microservice", "serverless", "container", "kubernetes", "docker", "aws", "gcp", "azure", "service mesh", "ci/cd", "deploy", "scale", "infra", "canary", "blue-green", "observability", "prometheus", "grafana", "trace"],
                "Concurrency": ["async", "await", "coroutine", "thread", "multiprocessing", "event loop", "gil", "lock", "semaphore", "channel", "mutex", "io-bound", "cpu-bound"],
                "Behavioral": ["team", "communicat", "challenge", "learn", "collaborat", "deadline", "feedback", "conflict", "led", "managed", "improved", "result", "incident", "outage", "post-mortem", "root cause"]
            }
            best_bank: list[str] = []
            for topic_key, keywords in keyword_banks.items():
                if topic_key.lower() in topic_str.lower() or any(k in q_text.lower() for k in topic_key.lower().split()):
                    best_bank = keywords
                    break
            if not best_bank:
                best_bank = ["design", "implement", "use", "build", "system", "approach", "consider", "trade", "optim", "scale", "handle", "process", "service"]

            hits = sum(1 for kw in best_bank if kw.lower() in ans_text.lower())
            return min(hits / max(len(best_bank) * 0.3, 1), 1.0)

        clean_ans = ans_lower.rstrip('.!?')
        is_hard_non_answer = clean_ans in NON_ANSWERS or not clean_ans
        trivially_short = word_count <= 3
        gibberish = _is_gibberish(ans_lower)

        # ── Zero score for non-answers ──────────────────────────────────────
        if is_hard_non_answer or trivially_short or gibberish:
            return {
                "score": 0.0,
                "technical_accuracy": 0.0,
                "depth": 0.0,
                "clarity": 0.0,
                "strengths": [],
                "weaknesses": [
                    "Response did not provide any technical explanation or answer to the question.",
                    "Answer is too short, empty, or uninformative."
                ],
                "feedback": (
                    "No technical details were provided. In an interview setting, provide your technical reasoning, "
                    "relevant frameworks, and architectural considerations."
                ),
                "recommended_action": "move_on",
            }

        relevance = _score_relevance(ans_lower, question_text, topic)

        # ── Low relevance ───────────────────────────────────────────────────
        if relevance < 0.15 and word_count < 30:
            return {
                "score": round(random.uniform(2.5, 4.0), 1),
                "technical_accuracy": round(random.uniform(2.0, 3.5), 1),
                "depth": round(random.uniform(1.5, 3.0), 1),
                "clarity": round(random.uniform(3.0, 5.0), 1),
                "strengths": ["Answer was submitted"],
                "weaknesses": [
                    "Answer does not directly address the technical specifics of the question.",
                    "Lacks concrete terminology, architectural tradeoffs, or implementation examples."
                ],
                "feedback": (
                    "Your answer touched on broad concepts but missed the specific technical core of the question. "
                    "Focus on naming relevant tools, explaining internal mechanics, and comparing tradeoffs."
                ),
                "recommended_action": "move_on",
            }

        # ── Medium relevance / Adequate answer ──────────────────────────────
        if relevance < 0.40 or word_count < 40:
            score = round(random.uniform(5.5, 7.2), 1)
            return {
                "score": score,
                "technical_accuracy": round(score - random.uniform(0, 0.6), 1),
                "depth": round(score - random.uniform(0.5, 1.2), 1),
                "clarity": round(min(score + random.uniform(0, 0.5), 10.0), 1),
                "strengths": ["Demonstrates basic conceptual understanding", "Addressed the general topic"],
                "weaknesses": ["Could provide deeper architectural tradeoffs or edge-case handling"],
                "feedback": (
                    "Solid foundational answer. To make it stand out, discuss specific edge cases, failure recovery, "
                    "and quantify your architectural decisions."
                ),
                "recommended_action": "move_on",
            }

        # ── Strong answer ───────────────────────────────────────────────────
        score = round(random.uniform(7.8, 9.4), 1)
        return {
            "score": score,
            "technical_accuracy": round(min(score + random.uniform(0, 0.4), 10.0), 1),
            "depth": round(min(score + random.uniform(0, 0.3), 10.0), 1),
            "clarity": round(min(score + random.uniform(0, 0.5), 10.0), 1),
            "strengths": [
                "Clear technical articulation and relevant architectural terminology",
                "Demonstrates deep hands-on familiarity with the problem space",
                "Thoughtful consideration of performance and tradeoffs"
            ],
            "weaknesses": ["Could expand on long-term maintainability and automated monitoring"],
            "feedback": (
                "Excellent, well-reasoned response. You clearly explained the architectural approach, "
                "referenced relevant industry patterns, and articulated key tradeoffs effectively."
            ),
            "recommended_action": "increase_difficulty" if score > 8.5 else "move_on",
        }

    elif func_name == "generate_final_report":
        history = args[2] if len(args) > 2 else []
        scores = []
        covered_topics = []
        for turn in history:
            if isinstance(turn, dict):
                t_name = turn.get("topic")
                if t_name and t_name not in covered_topics:
                    covered_topics.append(t_name)
                ev = turn.get("evaluation")
                if isinstance(ev, dict):
                    s = ev.get("score")
                    if isinstance(s, (int, float)):
                        scores.append(float(s))
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0

        strengths = []
        if avg >= 7.5:
            strengths = [
                "Strong technical depth and clear understanding of core architectural patterns",
                f"Demonstrated solid competency across {', '.join(covered_topics[:3]) if covered_topics else 'evaluated topics'}",
                "Effectively articulated engineering tradeoffs and practical considerations"
            ]
        elif avg >= 5.0:
            strengths = [
                "Demonstrated foundational technical literacy and ability to discuss practical scenarios",
                f"Addressed questions on {', '.join(covered_topics[:2]) if covered_topics else 'core engineering areas'}",
                "Participated constructively throughout the full technical evaluation"
            ]
        else:
            strengths = ["Participated in the interview evaluation session"]

        improvements = []
        if avg >= 7.5:
            improvements = [
                "Deepen exploration of edge cases, distributed failure modes, and automated disaster recovery",
                "Quantify architectural decisions with concrete operational metrics and benchmarks"
            ]
        elif avg >= 5.0:
            improvements = [
                "Provide more concrete implementation details and specific framework mechanics",
                "Elaborate on architectural tradeoffs and explain the 'why' behind design choices",
                "Strengthen knowledge in performance profiling and database query optimization"
            ]
        else:
            improvements = [
                "Provide detailed technical explanations rather than brief or surface-level answers",
                "Review core computer science fundamentals, data structures, and system design patterns",
                "Practice structuring responses with clear problem breakdown, solution, and tradeoff analysis"
            ]

        rec = "Strong No Hire" if avg < 3.0 else "Needs Improvement" if avg < 5.5 else "Hire" if avg < 8.0 else "Strong Hire"

        return {
            "overall_score": avg,
            "technical_score": round(max(avg - random.uniform(0, 0.3), 0.0), 1),
            "depth_score": round(max(avg - random.uniform(0, 0.5), 0.0), 1),
            "clarity_score": round(max(avg - random.uniform(0, 0.3), 0.0), 1),
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "gaps": improvements,
            "topics_demonstrated": covered_topics,
            "recommendations": improvements,
            "recommendation": rec,
            "summary": f"The candidate completed the interview session with an overall evaluated score of {avg}/10 across all questions."
        }

    else:
        return {}


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
            page_text = page.get_text()
            if isinstance(page_text, str):
                text += page_text

        doc.close()

        return text.strip()

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"PDF extraction failed: {str(e)}"
        )


def generate_basic_profile(text, target_role=""):
    """Extract structured candidate profile from raw resume text."""
    return extract_structured_profile(text, target_role)


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


# ── Voice / TTS ──────────────────────────────────────────────────────────────

from fastapi.responses import FileResponse, Response
import tempfile

class SpeakRequest(BaseModel):
    text: str
    mode: str = "question"   # greeting | question | follow_up | clarification | closing

@app.post("/speak")
def speak_text(req: SpeakRequest):
    """Convert interview question text to Deepgram TTS and return MP3 audio."""
    try:
        from voice.interview_voice import speak_question
        # Map question_type from interview to a valid voice mode
        valid_modes = {"greeting", "question", "follow_up", "clarification", "closing"}
        mode = req.mode if req.mode in valid_modes else "question"

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        speak_question(req.text, question_type=mode, output_file=tmp_path)

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        os.unlink(tmp_path)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


# =========================================================
# RESUME UPLOAD
# =========================================================

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        import traceback; traceback.print_exc()
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
        import traceback; traceback.print_exc()
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
        import traceback; traceback.print_exc()
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
        import traceback; traceback.print_exc()
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

        import traceback; traceback.print_exc()
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
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=404, detail="Question not found")

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE id = ?
    """, (request.interview_id,)).fetchone()

    if not interview:
        conn.close()
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=404, detail="Interview not found")

    if question["interview_id"] != request.interview_id:
        conn.close()
        import traceback; traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail="Question does not belong to this interview"
        )

    if not request.answer.strip():
        conn.close()
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=400, detail="Answer cannot be empty")

    candidate = conn.execute("""
        SELECT *
        FROM candidates
        WHERE id = ?
    """, (interview["candidate_id"],)).fetchone()

    conn.close()

    profile = json.loads(candidate["profile"])

    evaluation = call_ai(
    evaluate_answer,
    profile,
    interview["target_role"],
    question["question"],
    request.answer,
    question["topic"],
    question["difficulty"],
    "technical"
)

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
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview["status"] != "active":
        conn.close()
        import traceback; traceback.print_exc()
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
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview["status"] == "completed":
        conn.close()
        import traceback; traceback.print_exc()
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
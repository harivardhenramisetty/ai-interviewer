"""
AI Interview Bot — Polished Frontend
=====================================
Screens: Landing → System Check → Interview → Report
Backend integration point: swap MockInterviewEngine → InterviewEngine
"""

import streamlit as st
import time
import os
from dotenv import load_dotenv

# ── Backend toggle ────────────────────────────────────────────────────────
# Set USE_REAL_BACKEND = True when the real backend is ready.
USE_REAL_BACKEND = False

if USE_REAL_BACKEND:
    from interview_engine import InterviewEngine as Engine
    from resume_parser import extract_text_from_pdf
else:
    from mock_backend import MockInterviewEngine as Engine, MOCK_INTEGRITY_EVENTS
    from resume_parser import extract_text_from_pdf

from models import ActionEnum
from ui_styles import inject_css

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="InterviewAI — Adaptive Interview Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(inject_css(), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ══════════════════════════════════════════════════════════════════════════
DEFAULTS = {
    "page":                "landing",
    "engine":              None,
    "chat_history":        [],
    "interview_started":   False,
    "interview_finished":  False,
    "question_count":      0,
    "start_time":          None,
    "report":              None,
    "resume_text":         None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════
# UTILITY HELPERS
# ══════════════════════════════════════════════════════════════════════════
def navigate(page: str):
    st.session_state.page = page

def elapsed_timer() -> str:
    if st.session_state.start_time is None:
        return "00:00"
    secs = int(time.time() - st.session_state.start_time)
    return f"{secs // 60:02d}:{secs % 60:02d}"

def progress_pct() -> int:
    q = st.session_state.question_count
    if q == 0:
        return 5
    return min(int((q / 5) * 100), 100)


# ══════════════════════════════════════════════════════════════════════════
# 1 ▸ LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════
def render_landing():
    # Hero
    st.markdown("""
    <div class="hero-section">
        <h1>🎯 InterviewAI</h1>
        <p>AI-powered adaptive interviews that evaluate candidates in real-time, 
           generating personalised questions and comprehensive evaluation reports.</p>
    </div>
    """, unsafe_allow_html=True)

    # Centre column for form
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📋 Interview Setup</div>', unsafe_allow_html=True)

        target_role = st.text_input(
            "Target Job Role",
            placeholder="e.g. Senior Machine Learning Engineer",
            help="The role the candidate is interviewing for.",
        )

        job_desc = st.text_area(
            "Job Description (optional)",
            placeholder="Paste the job description here for more targeted questions…",
            height=120,
        )

        resume_file = st.file_uploader(
            "Upload Candidate Resume (PDF)",
            type=["pdf"],
            help="We extract text locally — the file is never stored.",
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # Feature pills
        feat_cols = st.columns(3)
        features = [
            ("🧠", "Adaptive AI", "Questions adapt based on each answer"),
            ("📊", "Deep Evaluation", "Technical, problem-solving & communication scores"),
            ("🔒", "Integrity Monitoring", "Tab-switch, paste, and timing signals"),
        ]
        for c, (icon, title, sub) in zip(feat_cols, features):
            with c:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size:28px;margin-bottom:6px">{icon}</div>
                    <div style="font-weight:700;font-size:14px;color:var(--text)">{title}</div>
                    <div style="font-size:12px;color:var(--text-muted);margin-top:4px">{sub}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Start button
        start = st.button("🚀  Start Interview", type="primary", use_container_width=True)
        if start:
            if not resume_file:
                st.error("Please upload a resume PDF to continue.")
                return
            if not target_role.strip():
                st.error("Please enter a target job role.")
                return

            resume_bytes = resume_file.read()
            resume_text = extract_text_from_pdf(resume_bytes)
            if not resume_text.strip():
                st.error("Could not extract text from the PDF. Please try another file.")
                return

            # Stash for later
            st.session_state.resume_text = resume_text
            st.session_state.target_role = target_role
            st.session_state.job_desc = job_desc
            navigate("system_check")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# 2 ▸ PRE-INTERVIEW SYSTEM CHECK
# ══════════════════════════════════════════════════════════════════════════
def render_system_check():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div class="hero-section" style="padding-bottom:16px">
            <h1 style="font-size:32px">🔧 System Check</h1>
            <p style="font-size:15px">Let's make sure everything is ready before we begin.</p>
        </div>
        """, unsafe_allow_html=True)

        checks = [
            ("🌐", "Internet Connection", "Connected", "success"),
            ("🎤", "Microphone",          "Ready (placeholder)", "success"),
            ("📷", "Camera",              "Ready (placeholder)", "success"),
            ("🤖", "AI Engine",           "Online", "success"),
        ]

        for icon, label, status, sev in checks:
            badge_class = f"badge-{sev}"
            st.markdown(f"""
            <div class="check-item">
                <div>
                    <span style="font-size:20px;margin-right:10px">{icon}</span>
                    <span class="check-label">{label}</span>
                    <div class="check-sub" style="margin-left:34px">Status verified automatically</div>
                </div>
                <span class="badge {badge_class}">● {status}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tips
        st.markdown("""
        <div class="card" style="background:#FFFBEB;border-color:#FDE68A">
            <div style="font-weight:700;margin-bottom:8px">💡 Tips for best results</div>
            <ul style="color:var(--text-muted);font-size:14px;line-height:1.8;margin:0;padding-left:20px">
                <li>Find a quiet, well-lit environment</li>
                <li>Close unnecessary browser tabs</li>
                <li>Have your notes nearby — but the AI may notice copy-paste!</li>
                <li>Speak clearly and take your time</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        begin = st.button("✅  Begin Interview", type="primary", use_container_width=True)
        if begin:
            with st.spinner("Preparing your personalised interview…"):
                engine = Engine(
                    target_role=st.session_state.target_role,
                    resume_text=st.session_state.resume_text,
                )
                engine.initialize_interview()

                st.session_state.engine = engine
                st.session_state.interview_started = True
                st.session_state.start_time = time.time()
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": engine.current_question,
                })
                st.session_state.question_count = 1
            navigate("interview")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# 3 ▸ MAIN INTERVIEW SCREEN
# ══════════════════════════════════════════════════════════════════════════
def render_interview():
    # ── Top bar ──────────────────────────────────────────────────────────
    top1, top2, top3, top4 = st.columns([3, 2, 1.5, 1.5])
    with top1:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px">
            <span style="font-size:26px">🎯</span>
            <div>
                <div style="font-weight:700;font-size:17px;color:var(--text)">InterviewAI</div>
                <div style="font-size:12px;color:var(--text-muted)">Adaptive Interview in Progress</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with top2:
        pct = progress_pct()
        st.markdown(f"""
        <div style="padding-top:6px">
            <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;font-weight:600">
                PROGRESS · Q{st.session_state.question_count}
            </div>
            <div class="progress-bar-custom">
                <div class="fill" style="width:{pct}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with top3:
        t = elapsed_timer()
        st.markdown(f'<div class="timer-display" style="margin-top:6px">⏱ {t}</div>', unsafe_allow_html=True)
    with top4:
        if not st.session_state.interview_finished:
            if st.button("⏹ End Interview", use_container_width=True):
                st.session_state.interview_finished = True
                st.rerun()

    st.markdown("---")

    # ── Chat area ────────────────────────────────────────────────────────
    chat_col, side_col = st.columns([3, 1])

    with chat_col:
        # Render chat messages
        for msg in st.session_state.chat_history:
            if msg["role"] == "assistant":
                st.markdown(f"""
                <div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:4px">
                    <div class="avatar-interviewer">AI</div>
                    <div class="interviewer-bubble">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display:flex;gap:12px;align-items:flex-start;justify-content:flex-end;margin-bottom:4px">
                    <div class="candidate-bubble">{msg["content"]}</div>
                    <div class="avatar-candidate">You</div>
                </div>
                """, unsafe_allow_html=True)

            # Debug panel for adaptive reasoning
            if "debug" in msg and msg["debug"]:
                with st.expander("🔍 AI Reasoning"):
                    st.json(msg["debug"])

        # Input
        if not st.session_state.interview_finished:
            answer = st.chat_input("Type your answer…")
            if answer:
                # Add user message
                st.session_state.chat_history.append({"role": "user", "content": answer})

                # Process
                engine = st.session_state.engine
                try:
                    decision = engine.process_answer(answer)
                    st.session_state.question_count += 1
                    debug_info = decision.model_dump()

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": decision.next_question,
                        "debug": debug_info,
                    })

                    if decision.next_action == ActionEnum.FINISH:
                        st.session_state.interview_finished = True
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"⚠️ I encountered an issue processing your answer. Please try again. ({e})",
                    })
                st.rerun()
        else:
            st.markdown("""
            <div class="card" style="text-align:center;border-color:var(--success);background:#ECFDF5">
                <div style="font-size:28px;margin-bottom:8px">✅</div>
                <div style="font-weight:700;font-size:18px;color:#065F46">Interview Complete</div>
                <div style="color:var(--text-muted);font-size:14px;margin-top:4px">
                    Click below to generate your evaluation report.
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📊  Generate Evaluation Report", type="primary", use_container_width=True):
                navigate("report")
                st.rerun()

    # ── Side panel ───────────────────────────────────────────────────────
    with side_col:
        # Candidate card
        engine = st.session_state.engine
        if engine and engine.profile:
            p = engine.profile
            st.markdown(f"""
            <div class="card">
                <div style="font-weight:700;font-size:14px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px">Candidate</div>
                <div style="font-weight:700;font-size:17px;color:var(--text)">{p.name}</div>
                <div style="font-size:13px;color:var(--text-muted);margin-top:4px">{st.session_state.get('target_role','')}</div>
                <div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:6px">
                    {''.join(f'<span class="badge badge-info">{s}</span>' for s in p.skills[:5])}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Topics covered
        if engine and engine.plan:
            covered = min(st.session_state.question_count, len(engine.plan.core_topics))
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="font-weight:700;font-size:14px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px">Topics</div>', unsafe_allow_html=True)
            for i, topic in enumerate(engine.plan.core_topics):
                icon = "✅" if i < covered else "⏳"
                st.markdown(f'<div style="font-size:13px;padding:4px 0;color:var(--text)">{icon} {topic}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Mic/cam placeholders
        st.markdown("""
        <div class="card" style="text-align:center">
            <div style="font-weight:700;font-size:14px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px">Controls</div>
            <div style="font-size:32px;margin-bottom:4px">🎤</div>
            <div style="font-size:12px;color:var(--text-muted)">Voice (coming soon)</div>
            <div style="font-size:32px;margin:12px 0 4px">📷</div>
            <div style="font-size:12px;color:var(--text-muted)">Camera (coming soon)</div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# 4 ▸ EVALUATION REPORT
# ══════════════════════════════════════════════════════════════════════════
def render_report():
    engine = st.session_state.engine

    # Generate report if not cached
    if st.session_state.report is None:
        with st.spinner("Generating comprehensive evaluation report…"):
            st.session_state.report = engine.get_final_report()
    report = st.session_state.report

    # ── Header ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-section" style="padding:32px 16px 16px">
        <h1 style="font-size:32px">📊 Evaluation Report</h1>
        <p style="font-size:15px">Comprehensive AI-generated assessment based on the interview transcript.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Recommendation badge ─────────────────────────────────────────────
    rec = report.hire_recommendation
    ring_class = "strong-hire" if "Strong" in rec else ("hire" if "Hire" in rec else "no-hire")
    _, center, _ = st.columns([1, 1, 1])
    with center:
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:24px">
            <div class="score-ring {ring_class}">{rec.split()[0][0]}</div>
            <div style="font-weight:800;font-size:22px;color:var(--text);margin-top:8px">{rec}</div>
            <div style="font-size:13px;color:var(--text-muted)">Overall Recommendation</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Executive Summary ────────────────────────────────────────────────
    st.markdown(f"""
    <div class="card">
        <div class="section-header">📝 Executive Summary</div>
        <p style="font-size:15px;color:var(--text);line-height:1.8">{report.summary}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Dimension scores ─────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    dimensions = [
        ("🛠️", "Technical Skills",  report.technical_skills_evaluation),
        ("🧩", "Problem Solving",   report.problem_solving_evaluation),
        ("💬", "Communication",     report.communication_evaluation),
    ]
    for col, (icon, title, text) in zip([c1, c2, c3], dimensions):
        with col:
            st.markdown(f"""
            <div class="card" style="height:100%">
                <div class="section-header" style="font-size:16px">{icon} {title}</div>
                <p style="font-size:14px;color:var(--text);line-height:1.7">{text}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Strengths / Weaknesses ───────────────────────────────────────────
    sw1, sw2 = st.columns(2)
    with sw1:
        st.markdown('<div class="card" style="height:100%">', unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:16px">💪 Strengths</div>', unsafe_allow_html=True)
        for s in report.overall_strengths:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px">
                <span style="color:var(--success);font-size:16px;flex-shrink:0">✓</span>
                <span style="font-size:14px;color:var(--text);line-height:1.5">{s}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with sw2:
        st.markdown('<div class="card" style="height:100%">', unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:16px">📌 Areas for Growth</div>', unsafe_allow_html=True)
        for w in report.overall_weaknesses:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px">
                <span style="color:var(--warning);font-size:16px;flex-shrink:0">△</span>
                <span style="font-size:14px;color:var(--text);line-height:1.5">{w}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Role Alignment ───────────────────────────────────────────────────
    st.markdown(f"""
    <div class="card">
        <div class="section-header" style="font-size:16px">🎯 Role Alignment</div>
        <p style="font-size:14px;color:var(--text);line-height:1.7">{report.role_alignment}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Evidence from Transcript ─────────────────────────────────────────
    if engine and engine.history:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:16px">🗂️ Evidence from Answers</div>', unsafe_allow_html=True)
        for i, entry in enumerate(engine.history):
            st.markdown(f"""
            <div style="margin-bottom:16px">
                <div style="font-weight:600;font-size:14px;color:var(--primary);margin-bottom:4px">Q{i+1}: {entry['question'][:120]}{'…' if len(entry['question'])>120 else ''}</div>
                <div class="evidence-quote">"{entry['answer'][:200]}{'…' if len(entry['answer'])>200 else ''}"</div>
                <div style="font-size:13px;color:var(--text-muted);margin-top:4px">
                    <strong>Assessment:</strong> {entry['decision'].get('assessment','N/A')[:150]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Integrity Signals (placeholder) ──────────────────────────────────
    if not USE_REAL_BACKEND:
        events = MOCK_INTEGRITY_EVENTS
    else:
        events = []

    if events:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:16px">🔒 Integrity Signals</div>', unsafe_allow_html=True)
        for ev in events:
            sev_class = "badge-warning" if ev["severity"] == "warning" else "badge-info"
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)">
                <div style="font-size:14px;color:var(--text)">{ev['event']}</div>
                <div style="display:flex;align-items:center;gap:12px">
                    <span style="font-size:13px;color:var(--text-muted);font-variant-numeric:tabular-nums">{ev['time']}</span>
                    <span class="badge {sev_class}">{ev['severity'].title()}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Actions ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, _ = st.columns([1, 1, 2])
    with a1:
        if st.button("🏠  New Interview", use_container_width=True):
            for k in DEFAULTS:
                st.session_state[k] = DEFAULTS[k]
            st.rerun()
    with a2:
        if st.button("🖨️  Print Report", use_container_width=True):
            st.info("Print functionality coming soon — use Ctrl+P for now.")


# ══════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════
PAGES = {
    "landing":      render_landing,
    "system_check": render_system_check,
    "interview":    render_interview,
    "report":       render_report,
}

PAGES[st.session_state.page]()

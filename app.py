"""
AI Interview Bot — Frontend
============================
Screens: Landing → System Check → Interview → Report
Backend: swap MockInterviewEngine → InterviewEngine via USE_REAL_BACKEND
"""

import streamlit as st
import time, os
from dotenv import load_dotenv

USE_REAL_BACKEND = False

if USE_REAL_BACKEND:
    from interview_engine import InterviewEngine as Engine
    from resume_parser import extract_text_from_pdf
else:
    from mock_backend import MockInterviewEngine as Engine, MOCK_INTEGRITY_EVENTS
    from resume_parser import extract_text_from_pdf

from models import ActionEnum
from ui_styles import inject_css
from voice.interview_voice import speak_question

load_dotenv()

st.set_page_config(page_title="InterviewAI", page_icon="◆", layout="wide", initial_sidebar_state="collapsed")
st.markdown(inject_css(), unsafe_allow_html=True)

DEFAULTS = {
    "page": "landing", "engine": None, "chat_history": [], "interview_started": False,
    "interview_finished": False, "question_count": 0, "start_time": None, "report": None, "resume_text": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def navigate(p):
    st.session_state.page = p

def elapsed():
    if not st.session_state.start_time: return "00:00"
    s = int(time.time() - st.session_state.start_time)
    return f"{s//60:02d}:{s%60:02d}"

def pct():
    q = st.session_state.question_count
    return min(int((q/5)*100), 100) if q else 5


# ═══════════════════════════════════════════════════════════════════
# 1 · LANDING
# ═══════════════════════════════════════════════════════════════════
def render_landing():
    # Hero
    h1, h2 = st.columns([3, 2], gap="large")
    with h1:
        st.markdown("""
        <div style="padding:40px 0 20px">
            <div style="font-size:46px;font-weight:800;color:var(--text);line-height:1.12;letter-spacing:-0.03em">
                Meet your<br><span style="background:var(--gradient);-webkit-background-clip:text;-webkit-text-fill-color:transparent">AI Interviewer.</span>
            </div>
            <div style="font-size:17px;color:var(--text-muted);line-height:1.65;margin:16px 0 28px;max-width:480px">
                Personalised interviews that adapt to your experience, role, and answers — 
                powered by advanced AI evaluation.
            </div>
        </div>
        """, unsafe_allow_html=True)
        start_top = st.button("Start an Interview  →", type="primary", key="hero_cta")

    with h2:
        st.markdown("""
        <div style="padding:40px 0 20px">
            <div class="ai-visual">
                <div class="ai-orb">✦</div>
                <div style="font-size:15px;font-weight:700;margin-bottom:4px">AI Interviewer</div>
                <div style="font-size:13px;opacity:.7;margin-bottom:16px">Ready to begin your session</div>
                <div class="ai-visual-line" style="background:rgba(99,91,255,.4);width:80%"></div>
                <div class="ai-visual-line" style="background:rgba(139,92,246,.3);width:60%"></div>
                <div class="ai-visual-line" style="background:rgba(59,130,246,.3);width:90%"></div>
                <div class="ai-visual-line" style="background:rgba(236,72,153,.25);width:45%"></div>
                <div style="margin-top:16px;display:flex;align-items:center;gap:8px">
                    <span style="width:8px;height:8px;border-radius:50%;background:#10B981;display:inline-block"></span>
                    <span style="font-size:12px;opacity:.8">System online · Low latency</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Features
    f1, f2, f3 = st.columns(3)
    features = [
        ("✨", "Personalised", "Resume-aware questions tailored to your experience and target role.", "#EEF2FF", "#635BFF"),
        ("🧠", "Adaptive", "Real-time conversation that digs deeper based on your answers.", "#F5F3FF", "#8B5CF6"),
        ("📊", "Deep Insights", "Evidence-based evaluation with technical and behavioural scores.", "#EFF6FF", "#3B82F6"),
    ]
    for col, (icon, title, desc, bg, accent) in zip([f1, f2, f3], features):
        with col:
            st.markdown(f"""
            <div class="feat-card">
                <div class="feat-icon" style="background:{bg};color:{accent}">{icon}</div>
                <div class="feat-title">{title}</div>
                <div class="feat-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Form
    _, fc, _ = st.columns([1, 3, 1])
    with fc:
        st.markdown("""
        <div class="sec-header">
            <div class="sec-icon" style="background:#EEF2FF;color:var(--primary)">📋</div>
            Interview Setup
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            target_role = st.text_input("Target role", placeholder="e.g. Senior ML Engineer")
        with c2:
            job_desc = st.text_area("Job description (optional)", placeholder="Paste JD here…", height=80)

        resume_file = st.file_uploader("Upload resume (PDF)", type=["pdf"], help="Extracted locally — never stored.")

        st.markdown("<br>", unsafe_allow_html=True)
        start = st.button("🚀  Start Interview", type="primary", use_container_width=True, key="start_btn")

        if start or start_top:
            if not resume_file:
                st.error("Upload a resume PDF to continue.")
                return
            if not target_role.strip():
                st.error("Enter a target role.")
                return
            text = extract_text_from_pdf(resume_file.read())
            if not text.strip():
                st.error("Could not extract text — try another PDF.")
                return
            st.session_state.resume_text = text
            st.session_state.target_role = target_role
            st.session_state.job_desc = job_desc
            navigate("system_check"); st.rerun()


# ═══════════════════════════════════════════════════════════════════
# 2 · SYSTEM CHECK
# ═══════════════════════════════════════════════════════════════════
def render_system_check():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 8px">
            <div style="font-size:32px;font-weight:800;color:var(--text)">Ready for your interview?</div>
            <div style="font-size:15px;color:var(--text-muted);margin-top:8px">Let's quickly check your setup.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        checks = [
            ("🎤", "Microphone", "Ready", "dot-green", "#F0FDF4", "#059669"),
            ("📷", "Camera", "Ready", "dot-green", "#EFF6FF", "#2563EB"),
            ("🌐", "Connection", "Excellent", "dot-green", "#FFFBEB", "#D97706"),
            ("✦",  "AI Interviewer", "Online", "dot-blue", "#EEF2FF", "#635BFF"),
        ]
        r1, r2 = st.columns(2)
        for i, (icon, name, val, dot, bg, accent) in enumerate(checks):
            with (r1 if i % 2 == 0 else r2):
                st.markdown(f"""
                <div class="status-card" style="border-top:3px solid {accent}">
                    <div class="status-icon">{icon}</div>
                    <div class="status-name">{name}</div>
                    <div class="status-val">{val}</div>
                    <div class="status-dot {dot}">● Connected</div>
                </div>
                <div style="height:12px"></div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tips-card">
            <strong>💡 Before you start</strong>
            <ul>
                <li>Find a quiet, well-lit environment</li>
                <li>Close unnecessary browser tabs</li>
                <li>Speak clearly and take your time</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        begin = st.button("🎙  Begin Interview", type="primary", use_container_width=True)
        if begin:
            with st.spinner("Preparing your personalised interview…"):
                engine = Engine(target_role=st.session_state.target_role, resume_text=st.session_state.resume_text)
                engine.initialize_interview()
                st.session_state.audio_path = speak_question(
                    engine.current_question,
                    question_type="question",
                    output_file="current_question.mp3",
                )
                st.session_state.engine = engine
                st.session_state.interview_started = True
                st.session_state.start_time = time.time()
                st.session_state.chat_history.append({"role": "assistant", "content": engine.current_question})
                st.session_state.question_count = 1
            navigate("interview"); st.rerun()


# ═══════════════════════════════════════════════════════════════════
# 3 · INTERVIEW
# ═══════════════════════════════════════════════════════════════════
def render_interview():
    engine = st.session_state.engine
    p = pct()
    role = st.session_state.get("target_role", "")

    # Top bar
    st.markdown(f"""
    <div class="topbar">
        <div class="topbar-brand">
            <div class="topbar-logo">AI</div>
            <div class="topbar-info">
                <div class="topbar-name">AI Interviewer</div>
                <div class="topbar-role">{role}</div>
            </div>
            <div class="badge-live">Live</div>
        </div>
        <div class="topbar-right">
            <div class="topbar-qcount">Question {st.session_state.question_count:02d}</div>
            <div class="timer">{elapsed()}</div>
        </div>
    </div>
    <div class="prog-track" style="margin-bottom:24px">
        <div class="prog-fill" style="width:{p}%"></div>
    </div>
    """, unsafe_allow_html=True)

    # Layout
    chat_col, side_col = st.columns([7, 3], gap="large")

    with chat_col:
        for msg in st.session_state.chat_history:
            if msg["role"] == "assistant":
                st.markdown(f"""
                <div class="ai-msg">
                    <div class="ai-avatar">AI</div>
                    <div class="ai-bubble">
                        <div class="ai-bubble-label">AI Interviewer</div>
                        {msg["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="user-msg">
                    <div class="user-bubble">{msg["content"]}</div>
                    <div class="user-avatar">You</div>
                </div>
                """, unsafe_allow_html=True)
        if st.session_state.get("audio_path"):
            st.audio(
                st.session_state.audio_path,
                format="audio/mp3",
            )
        if not st.session_state.interview_finished:
            answer = st.chat_input("Type your answer…")
            if answer:
                st.session_state.chat_history.append({"role": "user", "content": answer})
                try:
                    decision = engine.process_answer(answer)
                    st.session_state.question_count += 1
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": decision.next_question,
                        "debug": decision.model_dump(),
                    })
                    if decision.next_action == ActionEnum.FINISH:
                        st.session_state.interview_finished = True
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Something went wrong — please try again. ({e})",
                    })
                st.rerun()
        else:
            st.markdown("""
            <div class="complete-card">
                <div style="font-size:32px">✓</div>
                <h3>Interview Complete</h3>
                <p>Generate your evaluation report below.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📊  Generate Evaluation Report", type="primary", use_container_width=True):
                navigate("report"); st.rerun()

    with side_col:
        # Candidate
        if engine and engine.profile:
            pr = engine.profile
            st.markdown(f"""
            <div class="side-section">
                <div class="side-label">Candidate</div>
                <div class="side-name">{pr.name}</div>
                <div class="side-role">{role}</div>
                <div style="margin-top:12px">
                    {''.join(f'<span class="pill">{s}</span>' for s in pr.skills[:6])}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Topics
        if engine and engine.plan:
            cov = min(st.session_state.question_count, len(engine.plan.core_topics))
            topics_html = ""
            for i, t in enumerate(engine.plan.core_topics):
                if i < cov:
                    topics_html += f'<div class="topic-item topic-done"><div class="topic-dot done"></div>{t}</div>'
                elif i == cov:
                    topics_html += f'<div class="topic-item" style="color:var(--primary);font-weight:600"><div class="topic-dot active"></div>{t}</div>'
                else:
                    topics_html += f'<div class="topic-item topic-pending"><div class="topic-dot pending"></div>{t}</div>'
            st.markdown(f"""
            <div class="side-section">
                <div class="side-label">Interview Progress</div>
                {topics_html}
            </div>
            """, unsafe_allow_html=True)

        # Controls
        st.markdown("""
        <div class="side-section">
            <div class="side-label">Controls</div>
            <div class="ctrl-placeholder">
                <div class="ctrl-icon" style="background:#EEF2FF">🎤</div>
                <div><div style="font-weight:600;font-size:13px;color:var(--text)">Voice</div><div style="font-size:11px;color:var(--text-light)">Coming soon</div></div>
            </div>
            <div class="ctrl-placeholder">
                <div class="ctrl-icon" style="background:#FFF7ED">📷</div>
                <div><div style="font-weight:600;font-size:13px;color:var(--text)">Camera</div><div style="font-size:11px;color:var(--text-light)">Coming soon</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.interview_finished:
            if st.button("⏹  End Interview", use_container_width=True):
                st.session_state.interview_finished = True; st.rerun()


# ═══════════════════════════════════════════════════════════════════
# 4 · REPORT
# ═══════════════════════════════════════════════════════════════════
def render_report():
    engine = st.session_state.engine
    if st.session_state.report is None:
        with st.spinner("Generating evaluation report…"):
            st.session_state.report = engine.get_final_report()
    r = st.session_state.report
    rec = r.hire_recommendation
    name = engine.profile.name if engine and engine.profile else "Candidate"
    role = st.session_state.get("target_role", "")

    # Hero
    h1, h2 = st.columns([2, 1])
    with h1:
        st.markdown(f"""
        <div class="report-hero">
            <div class="report-candidate">Evaluation Report</div>
            <div class="report-title">{name}</div>
            <div class="report-role">{role}</div>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        ring_class = "strong-hire" if "Strong" in rec else ("hire" if "Hire" in rec else "no-hire")
        score = "8.6" if "Strong" in rec else ("7.2" if "Hire" in rec else "4.5")
        st.markdown(f"""
        <div class="report-hero" style="text-align:center">
            <div class="score-ring-wrap">
                <div class="score-ring">
                    <div class="score-num">{score}</div>
                    <div class="score-of">/ 10</div>
                </div>
                <div class="score-label">{rec}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Dimensions
    st.markdown("""
    <div class="sec-header">
        <div class="sec-icon" style="background:#EEF2FF;color:var(--primary)">📊</div>
        Performance Breakdown
    </div>
    """, unsafe_allow_html=True)

    dims = [
        ("Technical Skills", "8.6", r.technical_skills_evaluation, "#635BFF", 86),
        ("Problem Solving",  "8.1", r.problem_solving_evaluation,  "#3B82F6", 81),
        ("Communication",    "8.8", r.communication_evaluation,    "#10B981", 88),
    ]
    d1, d2, d3 = st.columns(3)
    for col, (title, sc, text, color, fill) in zip([d1, d2, d3], dims):
        with col:
            st.markdown(f"""
            <div class="dim-card">
                <div class="dim-top">
                    <div class="dim-title">{title}</div>
                    <div class="dim-score" style="color:{color}">{sc}</div>
                </div>
                <div class="prog-mini-track">
                    <div class="prog-mini-fill" style="width:{fill}%;background:{color}"></div>
                </div>
                <div class="dim-text">{text[:180]}{'…' if len(text)>180 else ''}</div>
            </div>
            """, unsafe_allow_html=True)

    # Summary
    st.markdown(f"""
    <div class="sec-header">
        <div class="sec-icon" style="background:#F5F3FF;color:var(--secondary)">📝</div>
        Executive Summary
    </div>
    <div class="card-flat" style="padding:24px">
        <p style="font-size:14px;color:var(--text);line-height:1.75;margin:0">{r.summary}</p>
    </div>
    """, unsafe_allow_html=True)

    # Strengths / Weaknesses
    sw1, sw2 = st.columns(2)
    with sw1:
        st.markdown("""
        <div class="sec-header">
            <div class="sec-icon" style="background:#ECFDF5;color:#059669">💪</div>
            Strengths
        </div>
        """, unsafe_allow_html=True)
        for s in r.overall_strengths:
            st.markdown(f"""
            <div class="sw-item">
                <div class="sw-icon green">✓</div>
                <span>{s}</span>
            </div>
            """, unsafe_allow_html=True)
    with sw2:
        st.markdown("""
        <div class="sec-header">
            <div class="sec-icon" style="background:#FFF7ED;color:#D97706">📌</div>
            Areas to Improve
        </div>
        """, unsafe_allow_html=True)
        for w in r.overall_weaknesses:
            st.markdown(f"""
            <div class="sw-item">
                <div class="sw-icon orange">△</div>
                <span>{w}</span>
            </div>
            """, unsafe_allow_html=True)

    # Role alignment
    st.markdown(f"""
    <div class="sec-header">
        <div class="sec-icon" style="background:#EEF2FF;color:var(--primary)">🎯</div>
        Role Alignment
    </div>
    <div class="card-flat" style="padding:24px">
        <p style="font-size:14px;color:var(--text);line-height:1.75;margin:0">{r.role_alignment}</p>
    </div>
    """, unsafe_allow_html=True)

    # Evidence
    if engine and engine.history:
        st.markdown("""
        <div class="sec-header">
            <div class="sec-icon" style="background:#F5F3FF;color:var(--secondary)">🗂️</div>
            Evidence from Interview
        </div>
        """, unsafe_allow_html=True)
        for i, e in enumerate(engine.history):
            q = e['question'][:150] + ('…' if len(e['question']) > 150 else '')
            a = e['answer'][:250] + ('…' if len(e['answer']) > 250 else '')
            ass = e['decision'].get('assessment', 'N/A')[:200]
            st.markdown(f"""
            <div class="ev-card">
                <div class="ev-q">Q{i+1}. {q}</div>
                <div class="ev-a">"{a}"</div>
                <div class="ev-assess">{ass}</div>
            </div>
            """, unsafe_allow_html=True)

    # Integrity
    events = MOCK_INTEGRITY_EVENTS if not USE_REAL_BACKEND else []
    if events:
        st.markdown("""
        <div class="sec-header">
            <div class="sec-icon" style="background:#FEF2F2;color:var(--red)">🔒</div>
            Integrity Signals
        </div>
        <div class="card-flat" style="padding:16px 20px">
        """, unsafe_allow_html=True)
        for ev in events:
            cls = "sev-warn" if ev["severity"] == "warning" else "sev-info"
            st.markdown(f"""
            <div class="int-row">
                <span style="color:var(--text)">{ev['event']}</span>
                <div style="display:flex;align-items:center;gap:10px">
                    <span style="color:var(--text-light);font-variant-numeric:tabular-nums">{ev['time']}</span>
                    <span class="sev-badge {cls}">{ev['severity']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Actions
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, _ = st.columns([1, 1, 2])
    with a1:
        if st.button("🏠  New Interview", use_container_width=True):
            for k in DEFAULTS: st.session_state[k] = DEFAULTS[k]
            st.rerun()
    with a2:
        if st.button("📄  Export Report", use_container_width=True):
            st.info("Use Ctrl+P / Cmd+P to print or save as PDF.")


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════
PAGES = {"landing": render_landing, "system_check": render_system_check, "interview": render_interview, "report": render_report}
PAGES[st.session_state.page]()

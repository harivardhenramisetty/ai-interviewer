import streamlit as st
import os
from dotenv import load_dotenv
from resume_parser import extract_text_from_pdf
from interview_engine import InterviewEngine
from models import ActionEnum

# Load environment variables
load_dotenv()

st.set_page_config(page_title="AI Interview Bot", layout="wide")

st.title("🤖 AI-Powered Interview Bot MVP")

# Check for API key
if not os.getenv("GEMINI_API_KEY"):
    st.error("⚠️ GEMINI_API_KEY is not set. Please add it to your environment or .env file.")
    st.stop()

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'interview_finished' not in st.session_state:
    st.session_state.interview_finished = False

# Sidebar for setup
with st.sidebar:
    st.header("Setup Interview")
    
    target_role = st.text_input("Target Job Role / Description", value="Software Engineer (Python/AI)")
    resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    
    start_btn = st.button("Start Interview", disabled=st.session_state.interview_started)
    
    if start_btn and resume_file and target_role:
        with st.spinner("Analyzing resume and preparing interview plan..."):
            resume_bytes = resume_file.read()
            resume_text = extract_text_from_pdf(resume_bytes)
            
            if not resume_text.strip():
                st.error("Could not extract text from the PDF. Please try another one.")
            else:
                try:
                    engine = InterviewEngine(target_role=target_role, resume_text=resume_text)
                    engine.initialize_interview()
                    
                    st.session_state.engine = engine
                    st.session_state.interview_started = True
                    
                    # Add first question to chat
                    st.session_state.chat_history.append({"role": "assistant", "content": engine.current_question})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error initializing interview. Please try again. Details: {e}")

# Main chat interface
if st.session_state.interview_started:
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "debug" in msg:
                with st.expander("Agent Reasoning (Debug)"):
                    st.json(msg["debug"])
            
    # Input for candidate
    if not st.session_state.interview_finished:
        candidate_answer = st.chat_input("Type your answer here...")
        
        if candidate_answer:
            # Display user answer
            st.session_state.chat_history.append({"role": "user", "content": candidate_answer})
            with st.chat_message("user"):
                st.write(candidate_answer)
                
            # Process answer
            with st.chat_message("assistant"):
                with st.spinner("Analyzing answer and thinking..."):
                    engine = st.session_state.engine
                    try:
                        decision = engine.process_answer(candidate_answer)
                        
                        next_question = decision.next_question
                        action = decision.next_action
                        
                        st.write(next_question)
                        
                        debug_info = decision.model_dump()
                        with st.expander("Agent Reasoning (Debug)"):
                            st.json(debug_info)
                            
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": next_question,
                            "debug": debug_info
                        })
                        
                        if action == ActionEnum.FINISH:
                            st.session_state.interview_finished = True
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error processing your answer. The agent might have struggled to format its response. Details: {e}")

    # Generate Report button when finished
    if st.session_state.interview_finished:
        st.success("Interview concluded.")
        if st.button("Generate Final Evaluation Report"):
            with st.spinner("Generating comprehensive report..."):
                engine = st.session_state.engine
                try:
                    report = engine.get_final_report()
                    
                    st.header("Final Evaluation Report")
                    st.subheader("Executive Summary")
                    st.write(report.summary)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Strengths")
                        for s in report.overall_strengths:
                            st.markdown(f"- {s}")
                        st.subheader("Technical Skills")
                        st.write(report.technical_skills_evaluation)
                        st.subheader("Problem Solving")
                        st.write(report.problem_solving_evaluation)
                    
                    with col2:
                        st.subheader("Weaknesses / Gaps")
                        for w in report.overall_weaknesses:
                            st.markdown(f"- {w}")
                        st.subheader("Communication")
                        st.write(report.communication_evaluation)
                        st.subheader("Role Alignment")
                        st.write(report.role_alignment)
                        
                    st.subheader("Recommendation")
                    st.info(f"**{report.hire_recommendation}**")
                except Exception as e:
                    st.error(f"Error generating final report: {e}")

elif not st.session_state.interview_started:
    st.info("👈 Please upload a resume and specify a target role in the sidebar to begin.")

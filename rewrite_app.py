import re

with open("app.py", "r") as f:
    content = f.read()

# Replace the imports
new_imports = """import requests
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def api_post(endpoint, json=None, data=None, files=None):
    res = requests.post(f"{API_BASE_URL}{endpoint}", json=json, data=data, files=files)
    if res.status_code >= 400:
        err = res.json().get('detail', 'Unknown error') if res.headers.get('content-type', '').startswith('application/json') else res.text
        raise Exception(f"API Error ({res.status_code}): {err}")
    return res.json()
"""

# We need to replace everything from `USE_REAL_BACKEND = False` up to `load_dotenv()` with requests logic
# Also remove ActionEnum

content = re.sub(
r"USE_REAL_BACKEND = False.*?from ui_styles import inject_css\n\nload_dotenv\(\)",
"from ui_styles import inject_css\n\nload_dotenv()\n\n" + new_imports,
content, flags=re.DOTALL
)

# Fix Session State DEFAULTS
content = content.replace('"engine": None, ', '"interview_id": None, "candidate_id": None, "current_question_id": None, ')

# Fix Resume Upload & Parse (Landing)
# Current:
# text = extract_text_from_pdf(resume_file.read())
# ...
# st.session_state.resume_text = text
# st.session_state.target_role = target_role
# navigate("system_check"); st.rerun()
upload_logic = """
            with st.spinner("Uploading and parsing resume..."):
                try:
                    # Upload
                    up_res = api_post("/upload-resume", files={"file": ("resume.pdf", resume_file.getvalue(), "application/pdf")})
                    cid = up_res["candidate_id"]
                    
                    # Parse
                    parse_res = api_post("/parse-resume", json={"candidate_id": cid, "target_role": target_role})
                    
                    st.session_state.candidate_id = cid
                    st.session_state.target_role = target_role
                    st.session_state.candidate_profile = parse_res.get("profile", {})
                    navigate("system_check"); st.rerun()
                except Exception as e:
                    st.error(f"Failed to process resume: {e}")
                    return
"""

content = re.sub(
r"text = extract_text_from_pdf\(resume_file\.read\(\)\).*?navigate\(\"system_check\"\); st\.rerun\(\)",
upload_logic.strip(),
content, flags=re.DOTALL
)

# Fix Start Interview (System Check)
# Current:
# engine = Engine(target_role=st.session_state.target_role, resume_text=st.session_state.resume_text)
# engine.initialize_interview()
# st.session_state.engine = engine
# st.session_state.interview_started = True
# st.session_state.start_time = time.time()
# st.session_state.chat_history.append({"role": "assistant", "content": engine.current_question})
# st.session_state.question_count = 1

start_logic = """
                try:
                    start_res = api_post("/start-interview", json={
                        "candidate_id": st.session_state.candidate_id,
                        "target_role": st.session_state.target_role
                    })
                    st.session_state.interview_id = start_res["interview_id"]
                    st.session_state.current_question_id = start_res["question_id"]
                    st.session_state.question_count = 1
                    st.session_state.interview_started = True
                    st.session_state.start_time = time.time()
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": start_res["question"]
                    })
                except Exception as e:
                    st.error(f"Failed to start interview: {e}")
                    return
"""

content = re.sub(
r"engine = Engine\(.*?st\.session_state\.question_count = 1",
start_logic.strip(),
content, flags=re.DOTALL
)


# Fix Interview Engine usage in Render Interview
content = content.replace("engine = st.session_state.engine", "")

# Fix candidate display
content = content.replace("if engine and engine.profile:", "if st.session_state.get('candidate_profile'):")
content = content.replace("pr = engine.profile", "pr = st.session_state.candidate_profile")
content = content.replace("pr.name", "pr.get('name', 'Candidate')")
content = content.replace("pr.skills[:6]", "pr.get('skills', [])[:6]")

# Fix topics display
content = content.replace("if engine and engine.plan:", "if st.session_state.get('candidate_profile'):")
content = content.replace("engine.plan.core_topics", "st.session_state.candidate_profile.get('relevant_topics', ['Experience'])")

# Fix Answer Submission & Next Question
# Current:
# decision = engine.process_answer(answer)
# st.session_state.question_count += 1
# st.session_state.chat_history.append({"role": "assistant", "content": decision.next_question, "debug": decision.model_dump()})
# if decision.next_action == ActionEnum.FINISH:

ans_logic = """
                    with st.spinner("Evaluating answer..."):
                        sub_res = api_post("/submit-answer", json={
                            "interview_id": st.session_state.interview_id,
                            "question_id": st.session_state.current_question_id,
                            "answer": answer
                        })
                        
                        next_res = api_post(f"/next-question/{st.session_state.interview_id}")
                        
                        if next_res.get("finished"):
                            st.session_state.interview_finished = True
                        else:
                            st.session_state.question_count = next_res["question_number"]
                            st.session_state.current_question_id = next_res["question_id"]
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": next_res["question"],
                                "debug": sub_res
                            })
"""

content = re.sub(
r"decision = engine\.process_answer\(answer\).*?st\.session_state\.interview_finished = True",
ans_logic.strip(),
content, flags=re.DOTALL
)


# Fix Report Generation
# Current:
# engine = st.session_state.engine
# if st.session_state.report is None:
#     with st.spinner("Generating evaluation report…"):
#         st.session_state.report = engine.get_final_report()
# r = st.session_state.report
# rec = r.hire_recommendation
# name = engine.profile.name if engine and engine.profile else "Candidate"
rep_logic = """
    if st.session_state.report is None:
        with st.spinner("Generating final report..."):
            try:
                st.session_state.report = api_post(f"/finish-interview/{st.session_state.interview_id}")
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
                st.stop()
    r = st.session_state.report
    rec = r.get("recommendation", "Review")
    name = st.session_state.candidate_profile.get("name", "Candidate") if st.session_state.get("candidate_profile") else "Candidate"
"""

content = re.sub(
r"engine = st\.session_state\.engine.*?name = engine\.profile\.name if engine and engine\.profile else \"Candidate\"",
rep_logic.strip(),
content, flags=re.DOTALL
)

# Fix Report Attributes
# r.technical_skills_evaluation -> we need to map to report output
# r is a dict now.
content = content.replace("r.technical_skills_evaluation", "r.get('summary', '')")
content = content.replace("r.problem_solving_evaluation", "r.get('summary', '')")
content = content.replace("r.communication_evaluation", "r.get('summary', '')")
content = content.replace("r.overall_strengths", "r.get('strengths', [])")
content = content.replace("r.overall_weaknesses", "r.get('gaps', [])")
content = content.replace("r.role_alignment", "r.get('summary', '')")

# Fix Evidence 
# if engine and engine.history:
# e['decision'].get('assessment', 'N/A') -> e['evaluation'].get('feedback', 'N/A')
content = content.replace("if engine and engine.history:", "if False:") # Just disable it or fetch it

with open("app.py", "w") as f:
    f.write(content)

import re

with open("frontend/app.py", "r") as f:
    content = f.read()

# 1. Update api_post and add render_api_error
new_api_post = """import requests
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def api_post(endpoint, json=None, data=None, files=None):
    try:
        res = requests.post(f"{API_BASE_URL}{endpoint}", json=json, data=data, files=files, timeout=45)
    except requests.exceptions.Timeout:
        raise Exception("The server took too long to respond. Please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Connection error: {str(e)}")

    if res.status_code >= 400:
        err = res.json().get('detail', 'Unknown error') if res.headers.get('content-type', '').startswith('application/json') else res.text
        if res.status_code in (429, 503):
            raise Exception(f"AI service is currently busy. Please wait a moment and try again.")
        raise Exception(f"API Error ({res.status_code}): {err}")
    return res.json()
"""

content = re.sub(r"import requests.*?return res\.json\(\)\n", new_api_post, content, flags=re.DOTALL)

# 2. Update render_landing error handling
old_landing = """                try:
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
                    return"""
new_landing = """                try:
                    cid = st.session_state.get("candidate_id")
                    if not cid:
                        up_res = api_post("/upload-resume", files={"file": ("resume.pdf", resume_file.getvalue(), "application/pdf")})
                        cid = up_res["candidate_id"]
                        st.session_state.candidate_id = cid
                        st.session_state.target_role = target_role
                    
                    parse_res = api_post("/parse-resume", json={"candidate_id": cid, "target_role": target_role})
                    st.session_state.candidate_profile = parse_res.get("profile", {})
                    navigate("system_check"); st.rerun()
                except Exception as e:
                    st.session_state.landing_err = e
            if st.session_state.get('landing_err'):
                st.error(f"⚠️ {str(st.session_state.landing_err)}")
                if st.button("🔄 Try Again", key="retry_landing"):
                    st.session_state.landing_err = None
                    st.rerun()"""
content = content.replace(old_landing, new_landing)


# 3. Update render_system_check error handling
old_sys_check = """        begin = st.button("🎙  Begin Interview", type="primary", use_container_width=True)
        if begin:
            with st.spinner("Preparing your personalised interview…"):
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
            navigate("interview"); st.rerun()"""
new_sys_check = """        begin = st.button("🎙  Begin Interview", type="primary", use_container_width=True)
        if begin or st.session_state.get('retry_sys_check_flag'):
            st.session_state.retry_sys_check_flag = False
            with st.spinner("Preparing your personalised interview..."):
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
                    navigate("interview"); st.rerun()
                except Exception as e:
                    st.session_state.sys_check_err = e
        if st.session_state.get('sys_check_err'):
            st.error(f"⚠️ {str(st.session_state.sys_check_err)}")
            if st.button("🔄 Try Again", key="retry_sys_check"):
                st.session_state.retry_sys_check_flag = True
                st.session_state.sys_check_err = None
                st.rerun()"""
content = content.replace(old_sys_check, new_sys_check)


# 4. Update render_interview error handling
old_int_err = """                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Something went wrong — please try again. ({e})",
                    })
                st.rerun()"""
new_int_err = """                except Exception as e:
                    st.session_state.int_err = e
                st.rerun()
            if st.session_state.get('int_err'):
                st.error(f"⚠️ {str(st.session_state.int_err)}")
                if st.button("🔄 Try Again", key="retry_int"):
                    # Remove the failed user answer from history so they can re-enter it, or we could just submit again
                    # But the answer was already appended to chat_history. So if they try again, they can just type again.
                    # Let's just pop the last user answer if it failed.
                    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
                        st.session_state.chat_history.pop()
                    st.session_state.int_err = None
                    st.rerun()"""
content = content.replace(old_int_err, new_int_err)

# 5. Update render_report error handling
old_rep_err = """    if st.session_state.report is None:
        with st.spinner("Generating final report..."):
            try:
                st.session_state.report = api_post(f"/finish-interview/{st.session_state.interview_id}")
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
                st.stop()"""
new_rep_err = """    if st.session_state.report is None:
        if st.session_state.get('retry_report_flag', True):
            st.session_state.retry_report_flag = False
            with st.spinner("Generating final report..."):
                try:
                    st.session_state.report = api_post(f"/finish-interview/{st.session_state.interview_id}")
                except Exception as e:
                    st.session_state.rep_err = e
        if st.session_state.get('rep_err'):
            st.error(f"⚠️ {str(st.session_state.rep_err)}")
            if st.button("🔄 Try Again", key="retry_rep"):
                st.session_state.retry_report_flag = True
                st.session_state.rep_err = None
                st.rerun()
            st.stop()"""
content = content.replace(old_rep_err, new_rep_err)

with open("frontend/app.py", "w") as f:
    f.write(content)


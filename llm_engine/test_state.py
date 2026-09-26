import sys
import time
from pathlib import Path

# Add workspace and llm_engine directory to sys.path
engine_dir = Path(__file__).resolve().parent
workspace_dir = engine_dir.parent
for p in (str(engine_dir), str(workspace_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from llm_engine.models import CandidateProfile
    from llm_engine.interview_engine import start_interview, submit_answer
except ImportError:
    from models import CandidateProfile  # type: ignore
    from interview_engine import start_interview, submit_answer  # type: ignore

print("Testing End-to-End State Management...")
    
fake_profile = CandidateProfile(
    candidate_summary="Fake candidate for testing state.",
    skills=["Python"],
    experience_level="Mid",
    strengths=["Testing"],
    potential_gaps=["None"],
    relevant_topics=["Python"]
)

session = None
for _ in range(5):
    try:
        print("\n--- Starting Interview (max_questions=2) ---")
        session = start_interview(
            candidate_profile=fake_profile,
            target_role="Tester",
            max_questions=2
        )
        print(f"Status: {session.status}")
        print(f"Question Number: {session.question_number}")
        print(f"History Length: {len(session.history)}")
        print(f"Current Question: {session.current_question.question if session.current_question else 'None'}")
        break
    except Exception as e:
        print(f"Error starting: {e}")
        time.sleep(2)

if session:
    for _ in range(5):
        try:
            print("\n--- Submitting First Answer ---")
            session = submit_answer(session, "This is my first fake answer.")
            print(f"Status: {session.status}")
            print(f"Question Number: {session.question_number}")
            print(f"History Length: {len(session.history)}")
            print(f"Current Question: {session.current_question.question if session.current_question else 'None'}")
            break
        except Exception as e:
            print(f"Error submitting first: {e}")
            time.sleep(2)

if session and session.question_number == 2:
    for _ in range(5):
        try:
            print("\n--- Submitting Second Answer ---")
            session = submit_answer(session, "This is my second fake answer.")
            print(f"Status: {session.status}")
            print(f"Question Number: {session.question_number}")
            print(f"History Length: {len(session.history)}")
            print(f"Current Question: {session.current_question.question if session.current_question else 'None'}")
            break
        except Exception as e:
            print(f"Error submitting second: {e}")
            time.sleep(2)


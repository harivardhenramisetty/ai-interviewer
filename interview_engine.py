from llm_client import initialize_interview_setup, evaluate_answer_and_decide, generate_final_report
from models import CandidateProfile, InterviewPlan, AdaptiveDecision, FinalReport, ActionEnum

class InterviewEngine:
    def __init__(self, target_role: str, resume_text: str):
        self.target_role = target_role
        self.resume_text = resume_text
        self.profile: CandidateProfile = None
        self.plan: InterviewPlan = None
        self.history = [] # List of dicts {"question": ..., "answer": ..., "decision": ...}
        self.is_finished = False
        self.current_question = ""
        
    def initialize_interview(self):
        print("Initializing interview (single LLM call)...")
        setup = initialize_interview_setup(self.resume_text, self.target_role)
        self.profile = setup.profile
        self.plan = setup.plan
        self.current_question = self.plan.first_question
        
    def process_answer(self, answer: str) -> AdaptiveDecision:
        print("Evaluating answer...")
        decision = evaluate_answer_and_decide(
            self.profile,
            self.target_role,
            self.history,
            self.current_question,
            answer
        )
        
        self.history.append({
            "question": self.current_question,
            "answer": answer,
            "decision": decision.model_dump()
        })
        
        if decision.next_action == ActionEnum.FINISH:
            self.is_finished = True
        
        self.current_question = decision.next_question
        return decision
        
    def get_final_report(self) -> FinalReport:
        if not self.is_finished and len(self.history) == 0:
            return None
        return generate_final_report(self.profile, self.target_role, self.history)

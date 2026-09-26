"""
Mock backend for frontend development.
Mirrors the real InterviewEngine interface so the UI can be developed independently.
Replace this with real imports when integrating with the backend team.
"""
import time
import random
from models import (
    CandidateProfile, InterviewPlan, InitialSetup,
    AdaptiveDecision, FinalReport, ActionEnum,
)


# ---------------------------------------------------------------------------
# Mock candidate profiles
# ---------------------------------------------------------------------------
MOCK_PROFILE = CandidateProfile(
    name="Alice Smith",
    skills=["Python", "TensorFlow", "PyTorch", "Streamlit", "Docker", "SQL", "FastAPI"],
    experience_summary="3 years as ML Engineer at DataInc building production AI systems including recommendation engines and NLP pipelines.",
    education_summary="M.S. Computer Science, Stanford University, 2021. B.S. Mathematics, UC Berkeley, 2019.",
)

MOCK_PLAN = InterviewPlan(
    core_topics=[
        "System Design & Architecture",
        "Machine Learning Fundamentals",
        "Deep Learning Frameworks",
        "Production ML Ops",
        "Problem Solving & Algorithms",
    ],
    first_question="Welcome Alice! Let's start with your experience at DataInc. Can you walk me through the most complex ML system you designed there, focusing on the architecture decisions you made and why?",
)

# ---------------------------------------------------------------------------
# Pre-built adaptive decisions for demo flow
# ---------------------------------------------------------------------------
MOCK_DECISIONS = [
    AdaptiveDecision(
        assessment="The candidate demonstrated solid understanding of ML system design, referencing a recommendation engine with clear architectural reasoning. However, the answer lacked specifics on scalability and monitoring.",
        strengths=["Clear architectural thinking", "Real-world project experience", "Good framework knowledge"],
        weaknesses=["Lacked scalability details", "No mention of monitoring or observability"],
        topics_to_probe=["Scalability patterns", "ML monitoring", "A/B testing"],
        next_action=ActionEnum.FOLLOW_UP,
        next_question="That's a great overview. You mentioned using PyTorch for the recommendation engine. How did you handle model serving at scale? What was your inference latency target and how did you achieve it?",
        reason="The candidate showed breadth but needs to demonstrate depth in production ML operations.",
    ),
    AdaptiveDecision(
        assessment="Good technical depth on model serving. The candidate clearly understands the trade-offs between batch and real-time inference. Mentioned ONNX export and TorchServe which shows practical knowledge.",
        strengths=["Strong model serving knowledge", "Understands latency trade-offs", "Practical tooling experience"],
        weaknesses=["Could elaborate more on failure handling"],
        topics_to_probe=["Error handling in ML pipelines", "Data drift detection"],
        next_action=ActionEnum.NEW_TOPIC,
        next_question="Let's switch gears. Can you describe a situation where a model you deployed started underperforming in production? How did you detect it and what was your remediation process?",
        reason="Moving to a new topic to assess the candidate's experience with real-world ML failure scenarios.",
    ),
    AdaptiveDecision(
        assessment="Excellent answer demonstrating strong problem-solving skills. The candidate described a systematic approach to debugging model drift, including data quality checks, feature distribution analysis, and automated retraining pipelines.",
        strengths=["Systematic debugging approach", "Data drift awareness", "Automated retraining experience"],
        weaknesses=[],
        topics_to_probe=["Leadership and communication"],
        next_action=ActionEnum.NEW_TOPIC,
        next_question="Great problem-solving approach. Final question: Tell me about a time you had to communicate a complex technical trade-off to non-technical stakeholders. How did you ensure alignment?",
        reason="Enough technical signal gathered. Assessing communication and leadership skills before concluding.",
    ),
    AdaptiveDecision(
        assessment="The candidate showed strong communication skills, using analogies and data-driven arguments to explain technical concepts. Demonstrated ability to align engineering decisions with business outcomes.",
        strengths=["Excellent communication", "Business-aware engineering", "Stakeholder management"],
        weaknesses=[],
        topics_to_probe=[],
        next_action=ActionEnum.FINISH,
        next_question="Thank you so much, Alice. That concludes our interview. You'll hear back from us within 48 hours. Do you have any questions for me?",
        reason="Sufficient signal gathered across all evaluation dimensions. Ready to generate final report.",
    ),
]

MOCK_REPORT = FinalReport(
    technical_skills_evaluation="Strong technical foundation across ML/DL frameworks (PyTorch, TensorFlow). Demonstrated practical experience with model serving, ONNX optimization, and production deployment patterns. Solid understanding of data pipelines and feature engineering. Could benefit from deeper systems programming knowledge.",
    problem_solving_evaluation="Excellent systematic approach to debugging and problem resolution. Demonstrated a structured methodology for diagnosing model drift issues, including root cause analysis and automated remediation. Shows strong analytical thinking.",
    communication_evaluation="Outstanding communication skills. Able to translate complex technical concepts into accessible language for non-technical stakeholders. Uses data-driven arguments and real-world analogies effectively. Active listener who addresses questions directly.",
    overall_strengths=[
        "Deep practical ML/AI experience with production systems",
        "Strong architectural thinking and system design skills",
        "Excellent problem-solving methodology",
        "Outstanding communication and stakeholder management",
        "Self-driven learner with growth mindset",
    ],
    overall_weaknesses=[
        "Limited discussion of scalability beyond single-service architectures",
        "Could strengthen knowledge of ML monitoring and observability tools",
        "No mention of experience with distributed training",
    ],
    role_alignment="Strong alignment with the Senior AI Developer role. The candidate's 3 years of production ML experience, combined with strong communication skills and systematic problem-solving approach, make her a compelling fit. Her Stanford education and practical framework expertise exceed the role requirements.",
    hire_recommendation="Strong Hire",
    summary="Alice Smith is a highly qualified candidate for the Senior AI Developer position. She demonstrated deep technical expertise in ML system design and deployment, excellent problem-solving methodology, and outstanding communication skills. Her experience building production recommendation systems at DataInc directly aligns with our team's needs. Minor gaps in distributed systems knowledge can be addressed through on-the-job learning. Recommendation: Strong Hire.",
)

MOCK_INTEGRITY_EVENTS = [
    {"time": "00:02:15", "event": "Tab switch detected", "severity": "warning"},
    {"time": "00:05:42", "event": "Browser focus restored", "severity": "info"},
    {"time": "00:12:30", "event": "Clipboard paste detected", "severity": "warning"},
    {"time": "00:18:05", "event": "Long pause detected (45s)", "severity": "info"},
]


# ---------------------------------------------------------------------------
# MockInterviewEngine — drop-in replacement interface for InterviewEngine
# ---------------------------------------------------------------------------
class MockInterviewEngine:
    """
    Mirrors the real InterviewEngine API so the UI code can swap between
    mock and real backends by changing a single import.
    """

    def __init__(self, target_role: str, resume_text: str):
        self.target_role = target_role
        self.resume_text = resume_text
        self.profile = MOCK_PROFILE
        self.plan = MOCK_PLAN
        self.history: list[dict] = []
        self.is_finished = False
        self.current_question = ""
        self._decision_index = 0

    # --- public API (same signature as the real engine) -------------------

    def initialize_interview(self) -> None:
        time.sleep(1.5)          # simulate network latency
        self.current_question = self.plan.first_question

    def process_answer(self, answer: str) -> AdaptiveDecision:
        time.sleep(1.0)          # simulate LLM thinking
        idx = min(self._decision_index, len(MOCK_DECISIONS) - 1)
        decision = MOCK_DECISIONS[idx]
        self._decision_index += 1

        self.history.append({
            "question": self.current_question,
            "answer": answer,
            "decision": decision.model_dump(),
        })

        if decision.next_action == ActionEnum.FINISH:
            self.is_finished = True

        self.current_question = decision.next_question
        return decision

    def get_final_report(self) -> FinalReport:
        time.sleep(1.5)
        return MOCK_REPORT

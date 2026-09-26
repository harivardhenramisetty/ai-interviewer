from backend.llm_adapter import _map_profile_to_engine

backend_profile = {
    "name": "Test Candidate",
    "education": ["B.Tech"],
    "skills": ["Python", "SQL"],
    "projects": ["Movie Recommender"],
    "experience": [],
    "certifications": []
}

engine_profile = {
    "candidate_summary": "AI/DS student with Python and SQL experience",
    "skills": ["Python", "SQL"],
    "experience_level": "beginner",
    "strengths": [],
    "potential_gaps": [],
    "relevant_topics": ["machine learning", "data analysis"]
}

try:
    print("Testing Backend Profile...")
    p1 = _map_profile_to_engine(backend_profile)
    print(p1.model_dump_json(indent=2))

    print("\nTesting Engine Profile...")
    p2 = _map_profile_to_engine(engine_profile)
    print(p2.model_dump_json(indent=2))

    print("\nCOMPATIBILITY TEST PASSED")
except Exception as e:
    print(f"FAILED: {e}")

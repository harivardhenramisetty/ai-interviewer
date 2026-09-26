with open("app.py", "r") as f:
    content = f.read()

content = content.replace("rec = r.hire_recommendation", "rec = r.get('recommendation', 'Review')")
content = content.replace("events = MOCK_INTEGRITY_EVENTS if not USE_REAL_BACKEND else []", "events = []")

with open("app.py", "w") as f:
    f.write(content)

import re

with open("backend/main.py", "r") as f:
    content = f.read()

content = content.replace(
"        raise HTTPException(",
"        import traceback; traceback.print_exc()\n        raise HTTPException("
)

with open("backend/main.py", "w") as f:
    f.write(content)

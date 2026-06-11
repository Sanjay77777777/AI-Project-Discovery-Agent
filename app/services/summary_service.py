from app.services.ollama_service import ask_llm
from app.services.analysis_service import read_readme
import json

def summarize_repository(repo_name: str):

    readme_data = read_readme(repo_name)

    content = readme_data["content"][:8000]

    prompt = f"""
You are a software architect.

Read the repository README.

Return ONLY raw JSON.

Do NOT use markdown.
Do NOT use code fences.
Do NOT write explanations.

Return exactly:

{{
    "project_summary": "...",
    "project_type": "...",
    "main_language": "...",
    "setup_method": "..."
}}

README:

{content}
"""

    response = ask_llm(prompt)

    return json.loads(response)
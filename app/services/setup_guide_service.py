import json

from app.services.analysis_service import (
    analyze_repository,
    read_readme
)

from app.services.ollama_service import ask_llm


def generate_setup_guide(repo_name: str):

    analysis = analyze_repository(repo_name)

    readme = read_readme(repo_name)

    content = readme["content"][:8000]

    prompt = f"""
You are a senior software engineer.

Repository Analysis:

{analysis}

README:

{content}

Return ONLY raw JSON.

Do NOT use markdown.
Do NOT use code fences.

Return exactly:

{{
    "requirements": [],
    "install_steps": [],
    "run_commands": []
}}

Use the repository information to generate
realistic setup instructions.
"""

    response = ask_llm(prompt)

    response = response.replace("```json", "")
    response = response.replace("```", "")
    response = response.strip()

    return json.loads(response)
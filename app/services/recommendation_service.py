from app.services.github_service import search_repositories
from app.services.ollama_service import ask_llm
from app.services.analysis_service import read_readme
import json

def recommend_repository(user_query: str):

    repositories = search_repositories(user_query)

    repo_text = ""

    for repo in repositories:
        repo_text += f"""
Name: {repo.name}
Owner: {repo.owner}
Description: {repo.description}
Language: {repo.language}
Stars: {repo.stars}

"""

    prompt = f"""
A user is looking for a software project.

User Request:
{user_query}

Repositories:
{repo_text}

Choose the SINGLE best repository.

Reply in this exact format:

REPOSITORY: <repository name>

REASON: <short reason>
"""

    return ask_llm(prompt)



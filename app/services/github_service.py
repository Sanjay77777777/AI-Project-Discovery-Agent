import requests
from app.models.repository import Repository

def search_repositories(query: str):
    url = "https://api.github.com/search/repositories"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 5
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    data = response.json()

    repositories = []

    for repo in data.get("items", []):
        repositories.append(
        Repository(
            name=repo["name"],
            owner=repo["owner"]["login"],
            stars=repo["stargazers_count"],
            url=repo["html_url"],
            description=repo["description"],
            language=repo["language"]
)
)

    return repositories
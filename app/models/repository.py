from pydantic import BaseModel


class Repository(BaseModel):
    name: str
    owner: str
    stars: int
    url: str
    description: str | None = None
    language: str | None = None
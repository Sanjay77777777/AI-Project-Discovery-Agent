from pydantic import BaseModel


class Recommendation(BaseModel):
    recommendation: str
    reason: str
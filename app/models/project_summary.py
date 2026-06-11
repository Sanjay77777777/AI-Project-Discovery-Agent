from pydantic import BaseModel

class ProjectSummary(BaseModel):
    project_summary: str
    project_type: str
    main_language: str
    setup_method: str
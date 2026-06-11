from pydantic import BaseModel


class SetupGuide(BaseModel):
    requirements: list[str]
    install_steps: list[str]
    run_commands: list[str]
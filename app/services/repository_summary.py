import logging
from pathlib import Path
from app.services.ollama_service import ask_llm
from app.config import REPOSITORIES_DIR

logger = logging.getLogger(__name__)


HIGH_VALUE_FILES = [
    "README.md",
    "README.rst",
    "README.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-dev.lock",
    "docs/index.md",
    "docs/en/docs/index.md",
    "docs/README.md",
]


class RepositorySummary:
    def __init__(self, repo_name: str):
        self.repo_name = repo_name
        self.repo_path = REPOSITORIES_DIR / repo_name

    def _find_source_files(self) -> list[tuple[Path, str]]:
        found = []
        for pattern in HIGH_VALUE_FILES:
            candidate = self.repo_path / pattern
            if candidate.exists() and candidate.is_file():
                rel = str(candidate.relative_to(self.repo_path))
                content = candidate.read_text(encoding="utf-8", errors="ignore")
                found.append((rel, content))
        return found

    def _build_context(self, sources: list[tuple[str, str]]) -> str:
        parts = []
        for rel_path, content in sources:
            parts.append(f"<<< FILE: {rel_path} >>>\n{content}\n")
        return "\n==========\n".join(parts)

    def generate_summary(self) -> dict:
        logger.info("Summary request for '%s'", self.repo_name)
        sources = self._find_source_files()
        logger.info("Summary for '%s': found %s high-value files", self.repo_name, len(sources))

        if not sources:
            return {
                "summary": "No high-level documentation files found.",
                "architecture": "Unknown",
                "technologies": [],
                "sources": [],
            }

        context = self._build_context(sources)
        source_paths = [s[0] for s in sources]

        system = (
            "You are a repository analyst. Analyze the provided files "
            "and produce a concise overview. Use ONLY the content provided.\n\n"
            "Do not guess.\n"
            "Do not invent information.\n"
            "If something is not in the context, do not mention it."
        )

        prompt = (
            f"Repository: {self.repo_name}\n\n"
            f"Files:\n{context}\n\n"
            "From these files, extract:\n"
            "1. Project summary — what does this project do?\n"
            "2. Architecture overview — how is it structured?\n"
            "3. Technologies used — list key languages, frameworks, tools.\n\n"
            "Format your response exactly as:\n"
            "SUMMARY:\n...\n\n"
            "ARCHITECTURE:\n...\n\n"
            "TECHNOLOGIES:\n...\n"
        )

        answer = ask_llm(prompt, system=system)
        summary, architecture, technologies = self._parse_response(answer)

        return {
            "summary": summary,
            "architecture": architecture,
            "technologies": technologies,
            "sources": source_paths,
        }

    def _parse_response(self, text: str) -> tuple[str, str, list[str]]:
        summary = ""
        architecture = ""
        technologies: list[str] = []

        lines = text.splitlines()
        current_section = None

        section_markers = {
            "summary": ["summary:", "**summary:**", "## summary", "project summary"],
            "architecture": ["architecture:", "**architecture:**", "## architecture", "architecture overview"],
            "technologies": ["technologies:", "**technologies:**", "## technologies", "technologies used"],
        }

        def match_section(line: str) -> str | None:
            lower = line.strip().lower().lstrip("#").lstrip("*").strip()
            for section, markers in section_markers.items():
                for m in markers:
                    if lower.startswith(m):
                        return section
            return None

        for line in lines:
            section = match_section(line)
            if section:
                current_section = section
                continue

            if current_section == "summary":
                summary += line + "\n"
            elif current_section == "architecture":
                architecture += line + "\n"
            elif current_section == "technologies":
                stripped = line.strip().lstrip("-*•").strip()
                if stripped:
                    technologies.append(stripped)

        summary = summary.strip()
        architecture = architecture.strip()

        return summary, architecture, technologies

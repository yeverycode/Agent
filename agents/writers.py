from __future__ import annotations

from typing import Any, Dict

from tools.doc_gen import generate_readme, save_readme, validate_sections


class WriterAgent:
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash", mode: str = "portfolio"):
        self.model = model
        self.mode = mode
        self.api_key = api_key

    def run(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        markdown = generate_readme(
            project_data=project_data,
            model=self.model,
            mode=self.mode,
            api_key=self.api_key,
        )

        saved_path = save_readme(markdown)
        section_check = validate_sections(markdown)

        return {
            "status": "success",
            "readme_markdown": markdown,
            "saved_path": saved_path,
            "section_check": section_check,
        }

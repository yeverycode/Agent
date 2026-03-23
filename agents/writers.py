from __future__ import annotations

from typing import Any, Dict

from tools.doc_gen import generate_readme, save_readme, validate_sections


class WriterAgent:
    def __init__(self, model: str = "gemini-2.5-flash", mode: str = "portfolio"):
        self.model = model
        self.mode = mode

    def run(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        markdown = generate_readme(
            project_data=project_data,
            model=self.model,
            mode=self.mode,
        )

        saved_path = save_readme(markdown)
        section_check = validate_sections(markdown)

        return {
            "status": "success",
            "readme_markdown": markdown,
            "saved_path": saved_path,
            "section_check": section_check,
        }
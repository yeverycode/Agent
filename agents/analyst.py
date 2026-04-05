from __future__ import annotations

import os
from typing import Any, Dict

from google import genai

from agents.prompts.analyst_prompt import (
    ANALYST_INSTRUCTION,
    ANALYST_INPUT_PROMPT_TEMPLATE,
)
from tools.parser import (
    build_analysis_context,
    extract_structure_hints,
    select_candidate_files,
    summarize_tree_structure,
)


class AnalystAgent:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.model = model
        self.api_key = api_key

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

        self.client = genai.Client(api_key=self.api_key)

    def _generate_analysis(self, context: str) -> str:
        prompt = ANALYST_INPUT_PROMPT_TEMPLATE.format(context=context)

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {"role": "user", "parts": [{"text": ANALYST_INSTRUCTION}]},
                {"role": "user", "parts": [{"text": prompt}]},
            ],
        )

        return response.text.strip()

    def run(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        project_data 예시:
        {
            "repo_name": "GitZen",
            "repo_url": "https://github.com/....",
            "tree_paths": [...],
            "selected_files": {
                "README.md": "...",
                "src/App.tsx": "..."
            }
        }
        """
        repo_name = project_data.get("repo_name", "unknown-repo")
        repo_url = project_data.get("repo_url", "")
        tree_paths = project_data.get("tree_paths", [])
        selected_files = project_data.get("selected_files", {})

        # selected_files가 비어 있으면 tree 기반으로 후보만 뽑아줌
        candidate_files = select_candidate_files(tree_paths, max_files=8)

        structure_summary = summarize_tree_structure(tree_paths)
        structure_hints = extract_structure_hints(tree_paths)

        analysis_context = build_analysis_context(
            repo_name=repo_name,
            repo_url=repo_url,
            tree_paths=tree_paths,
            file_contents=selected_files,
        )

        raw_analysis = self._generate_analysis(analysis_context)

        return {
            "status": "success",
            "repo_name": repo_name,
            "repo_url": repo_url,
            "candidate_files": candidate_files,
            "structure_summary": structure_summary,
            "structure_hints": structure_hints,
            "analysis_context": analysis_context,
            "analysis_result": raw_analysis,
        }

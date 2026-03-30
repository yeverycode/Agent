from __future__ import annotations

import os
from typing import Any, Dict

from google import genai

from tools.parser import (
    build_analysis_context,
    extract_structure_hints,
    select_candidate_files,
    summarize_tree_structure,
)


ANALYST_INSTRUCTION = """
너는 GitHub 프로젝트를 분석해 취업 준비생이 자신의 프로젝트를 설명할 수 있도록 돕는 분석가다.

입력으로 저장소 파일 트리와 핵심 파일 내용이 주어진다.
이 정보를 바탕으로 프로젝트의 목적, 디렉토리 구조, 주요 기능, 핵심 파일 역할을 한국어로 설명하라.

반드시 아래 원칙을 지켜라:
1. README만 믿지 말고 파일명, 디렉토리 구조, 코드 내용도 함께 근거로 사용하라.
2. 확인 가능한 사실과 추정은 구분하라.
3. 과장된 마케팅 문구 대신 실제 프로젝트 설명처럼 작성하라.
4. 취업 준비생이 면접이나 포트폴리오에서 활용할 수 있도록 명확하게 써라.
5. 확실하지 않은 내용은 '추정'이라고 표시하라.

반드시 아래 JSON 형식으로만 응답하라:

{
    "project_overview": "프로젝트 개요",
    "directory_structure": "디렉토리 구조 설명",
    "key_features": "주요 기능 설명",
    "key_files": "핵심 파일 역할 설명",
    "execution_flow": "핵심 실행 흐름 또는 사용자 흐름",
    "uncertain_points": "불확실하거나 추가 확인이 필요한 부분"
}
""".strip()


class AnalystAgent:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

        self.client = genai.Client(api_key=self.api_key)

    def _generate_analysis(self, context: str) -> str:
        prompt = f"""
다음은 GitHub 프로젝트 분석을 위한 입력 데이터다.

{context}

위 정보를 바탕으로 JSON만 출력하라.
""".strip()

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
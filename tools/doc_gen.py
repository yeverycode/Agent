from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from google import genai
from agents.prompts.doc_gen_prompt import build_prompt_from_project_data


def build_readme_prompt(project_data: Dict[str, Any], mode: str = "portfolio") -> str:
    return build_prompt_from_project_data(project_data, mode=mode)


def clean_markdown(text: str) -> str:
    text = text.strip()

    if text.startswith("```markdown"):
        text = text[len("```markdown"):].strip()
    elif text.startswith("```md"):
        text = text[len("```md"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def generate_readme(
    project_data: Dict[str, Any],
    model: str = "gemini-2.5-flash",
    mode: str = "portfolio",
    api_key: str | None = None,
) -> str:
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

    client = genai.Client(api_key=api_key)
    prompt = build_readme_prompt(project_data, mode=mode)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    result = getattr(response, "text", None)
    if not result:
        raise ValueError("Gemini 응답 텍스트가 비어 있습니다.")

    return clean_markdown(result)


def save_readme(markdown_text: str, output_dir: str = "outputs", filename: str = "README.generated.md") -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename
    file_path.write_text(markdown_text, encoding="utf-8")
    return str(file_path)


def validate_sections(markdown_text: str) -> Dict[str, bool]:
    required_sections = [
        "프로젝트 소개",
        "주요 기능",
        "프로젝트 구조",
        "핵심 파일 설명",
        "기술 스택",
        "시스템 아키텍처",
        "실행 방법",
        "기술 선택 이유",
        "개선 방향"
    ]
    return {section: (section in markdown_text) for section in required_sections}

from __future__ import annotations

from typing import Dict


def build_doc_gen_prompt(
    project_name: str,
    repo_url: str,
    one_line_summary: str,
    directory_text: str,
    feature_text: str,
    key_files_text: str,
    tech_text: str,
    architecture_summary: str,
    key_points_text: str,
    uncertain_text: str,
    mermaid_code: str,
    tone: str,
) -> str:
    return f"""
당신은 GitHub 프로젝트를 정리하는 기술 문서 작성자입니다.
아래 분석 결과를 바탕으로 한국어 README.md를 작성하세요.

[작성 목적]
- {tone}

[중요 규칙]
1. 출력은 Markdown 본문만 작성합니다.
2. 과장하지 않습니다.
3. 확실하지 않은 내용은 '추정'이라고 표시합니다.
4. README에 바로 붙여넣을 수 있게 자연스럽게 작성합니다.
5. 아래 섹션을 포함합니다:
   - 프로젝트 소개
   - 주요 기능
   - 프로젝트 구조
   - 핵심 파일 설명
   - 기술 스택
   - 시스템 아키텍처
   - 실행 방법
   - 기술 선택 이유
   - 개선 방향

[프로젝트 기본 정보]
- 프로젝트명: {project_name}
- 저장소 URL: {repo_url}
- 한 줄 요약: {one_line_summary}

[디렉토리 구조 설명]
{directory_text}

[주요 기능]
{feature_text}

[핵심 파일]
{key_files_text}

[기술 스택]
{tech_text}

[아키텍처 요약]
{architecture_summary}

[핵심 포인트]
{key_points_text}

[불확실하거나 추정인 부분]
{uncertain_text}

[Mermaid 코드]
{mermaid_code}

[추가 조건]
- 실행 방법은 정보가 없으면 '추가 작성 필요'라고 표시하세요.
- 기술 선택 이유는 기술별 장점을 한두 문장으로 정리하세요.
- Mermaid 코드가 있으면 README 안에 코드 블록으로 포함하세요.
""".strip()


def build_prompt_from_project_data(project_data: Dict, mode: str = "portfolio") -> str:
    project_name = project_data.get("project_name", "Unknown Project")
    repo_url = project_data.get("repo_url", "")
    analysis = project_data.get("analysis_summary", {})
    tech = project_data.get("tech_summary", {})

    one_line_summary = analysis.get("one_line_summary", "프로젝트 설명이 제공되지 않았습니다.")
    directory_explanation = analysis.get("directory_explanation", [])
    main_features = analysis.get("main_features", [])
    key_files = analysis.get("key_files", [])
    uncertain_points = analysis.get("uncertain_points", [])

    tech_stack = tech.get("tech_stack", {})
    architecture_summary = tech.get("architecture_summary", "")
    mermaid_code = tech.get("mermaid_code", "")
    key_points = tech.get("key_points", [])

    def format_list_or_str(data):
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data) if data else "- 정보 없음"
        elif isinstance(data, str):
            return data
        return "- 정보 없음"

    directory_text = format_list_or_str(directory_explanation)
    feature_text = format_list_or_str(main_features)
    key_points_text = format_list_or_str(key_points)
    uncertain_text = format_list_or_str(uncertain_points)

    if isinstance(key_files, list) and len(key_files) > 0 and isinstance(key_files[0], dict):
        key_files_text = "\n".join(
            f"- `{item.get('path', 'Unknown')}`: {item.get('role', '')}" for item in key_files
        )
    elif isinstance(key_files, dict):
        key_files_text = "\n".join(f"- `{k}`: {v}" for k, v in key_files.items())
    elif isinstance(key_files, list):
        key_files_text = "\n".join(f"- {item}" for item in key_files)
    elif isinstance(key_files, str):
        key_files_text = key_files
    else:
        key_files_text = "- 정보 없음"

    tech_lines = []
    if isinstance(tech_stack, dict):
        for category, values in tech_stack.items():
            if isinstance(values, list):
                joined = ", ".join(values) if values else "-"
                tech_lines.append(f"- {category}: {joined}")
            else:
                tech_lines.append(f"- {category}: {values}")
        tech_text = "\n".join(tech_lines) or "- 정보 없음"
    else:
        tech_text = "- 정보 없음"

    tone = {
        "portfolio": "면접과 포트폴리오 제출에 적합한 README로 작성하세요.",
        "beginner": "초보 개발자가 읽어도 이해하기 쉽게 설명하세요.",
        "professional": "오픈소스 프로젝트 문서처럼 정돈된 형식으로 작성하세요.",
    }.get(mode, "가독성 좋은 README로 작성하세요.")

    return build_doc_gen_prompt(
        project_name=project_name,
        repo_url=repo_url,
        one_line_summary=one_line_summary,
        directory_text=directory_text,
        feature_text=feature_text,
        key_files_text=key_files_text,
        tech_text=tech_text,
        architecture_summary=architecture_summary or "- 정보 없음",
        key_points_text=key_points_text,
        uncertain_text=uncertain_text,
        mermaid_code=mermaid_code or "없음",
        tone=tone,
    )

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
    static_sections = """
6. 아래 내용을 "코드 작성" 섹션과 "데이터 흐름 요약" 섹션으로 반드시 포함하세요.

[코드 작성 섹션에 포함할 내용]
- [`main.py`](http://main.py) 코드 작성

```python
import os
import json
from dotenv import load_dotenv

# 각 에이전트 클래스 임포트
from agents.repo_manager import RepoManagerAgent
from agents.analyst import AnalystAgent
from agents.tech_expert import TechExpertAgent
from agents.writers import WriterAgent

def main():
    load_dotenv()
    
    # 깃허브 토큰 및 gemini api 키 설정
    github_token = os.getenv("MY_GITHUB_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
        
    if not github_token or not gemini_api_key:
        print("필수 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
        
    TARGET_REPO = "YourGitHubID/YourRepoName" # 분석 레포 설정
    MODEL = "gemini-2.5-flash"

    print(f"[README 생성 에이전트] '{TARGET_REPO}' 분석을 시작합니다.\\n")

    try:
        # 각 에이전트에 토큰 주입
        repo_mgr = RepoManagerAgent(token=github_token, api_key=gemini_api_key, model=MODEL)
        analyst = AnalystAgent(api_key=gemini_api_key, model=MODEL)
        tech_exp = TechExpertAgent(api_key=gemini_api_key, model=MODEL)
        writer = WriterAgent(api_key=gemini_api_key, model=MODEL, mode="portfolio")

        # RepoManager (하늘)
        print("[Step 1] GitHub에서 핵심 파일 추출 중...")
        repo_data = repo_mgr.extract_project_data(TARGET_REPO)
        
        # Analyst (유민)
        print("[Step 2] 프로젝트 구조 및 기능 분석 중...")
        analysis_res = analyst.run(repo_data)
        
        # 분석 결과(JSON 문자열)를 파이썬 객체로 변환
        analysis_json = json.loads(analysis_res.get("analysis_result", "{}"))

        # TechExpert (서영)
        print("[Step 3] 기술 스택 추출 및 Mermaid 도식화 생성 중...")
        tech_res = tech_exp.run(analysis_res) 
        tech_data = tech_res.get("tech_summary", {})

        # Writer (예인)
        print("[Step 4] 모든 데이터를 취합하여 최종 README 생성 중...")
        # 에이전트 간 데이터 규격 매핑
        combined_context = {
            "project_name": repo_data["repo_name"].split("/")[-1],
            "repo_url": repo_data["repo_url"],
            "analysis_summary": {
                "one_line_summary": analysis_json.get("project_overview"),
                "directory_explanation": [analysis_json.get("directory_structure")],
                "main_features": [analysis_json.get("key_features")],
                "key_files": [{"path": "Core Logic", "role": analysis_json.get("key_files")}],
                "uncertain_points": [analysis_json.get("uncertain_points")]
            },
            "tech_summary": tech_data
        }
        
        final_readme = writer.run(combined_context)

        # 결과 출력
        if final_readme.get("status") == "success":
            print(f"\\n 성공! README가 생성되었습니다.")
            print(f"파일 위치: {final_readme.get('saved_path')}")
            print(f"체크리스트: {final_readme.get('section_check')}")

    except Exception as e:
        print(f"\\n 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
```

[데이터 흐름 요약 섹션에 포함할 내용]
- **[Step 0]** `main.py` 가 중앙에서 GitHub 토큰과 Gemini API 키를 로드하여 모든 에이전트에게 전달
- **[Step 1]** `RepoManager` 에이전트 작동
- **[Step 2]** `Analyst` 에이전트 작동
- **[Step 3]** `TechExpert` 에이전트 작동
- **[Step 4]** `Writer` 에이전트 작동

---

#### 1. 하늘님 (repo_manager agent)

- 파일 위치 : `agents/repo_manager.py`
- 수정사항 : `main.py`에서 전달하는 GitHub 토큰과 Gemini 키를 우선 사용하도록 생성자 변경

```python
# [수정 후]
def __init__(self, token: str = None, api_key: str = None, model: str = "gemini-2.5-flash"):
    self.token = token or os.getenv("MY_GITHUB_TOKEN")
    self.api_key = api_key or os.getenv("GEMINI_API_KEY")
    self.model = model
    self.client = genai.Client(api_key=self.api_key)
```

---

#### 2. 유민님 (analyst agent)

- 파일 위치 : `agents/analyst.py`
- 수정사항 : 생성자에서 `api_key`를 인자로 받고, 내부 클라이언트에 적용

```python
# [수정 후]
def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
    self.api_key = api_key or os.getenv("GEMINI_API_KEY")
    self.model = model
    self.client = genai.Client(api_key=self.api_key)
```

---

#### 3. 예인님 (writer agent & doc_gen)

- 파일 위치 : `agents/writers.py` 및 `tools/doc_gen.py`
- 수정사항 : 생성자에서 `api_key`를 인자로 받고, 에이전트가 받은 `generate_readme` 함수까지 전달

```python
# [수정 후] agents/writers.py
def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash", mode: str = "portfolio"):
    self.api_key = api_key or os.getenv("GEMINI_API_KEY")
    self.model = model
    self.mode = mode

def run(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
    markdown = generate_readme(
        project_data=project_data,
        model=self.model,
        mode=self.mode,
        api_key=self.api_key 
    )
    

# [수정 후] tools/doc_gen.py
def generate_readme(project_data, model, mode, api_key=None):
    current_key = api_key or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=current_key)
```
""".strip()
    static_sections = static_sections.replace("{", "{{").replace("}", "}}")

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
{static_sections}

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

    directory_text = "\n".join(f"- {item}" for item in directory_explanation) or "- 정보 없음"
    feature_text = "\n".join(f"- {item}" for item in main_features) or "- 정보 없음"
    key_files_text = "\n".join(
        f"- `{item['path']}`: {item['role']}" for item in key_files
    ) or "- 정보 없음"

    tech_lines = []
    for category, values in tech_stack.items():
        if isinstance(values, list):
            joined = ", ".join(values) if values else "-"
            tech_lines.append(f"- {category}: {joined}")
        else:
            tech_lines.append(f"- {category}: {values}")
    tech_text = "\n".join(tech_lines) or "- 정보 없음"

    key_points_text = "\n".join(f"- {item}" for item in key_points) or "- 정보 없음"
    uncertain_text = "\n".join(f"- {item}" for item in uncertain_points) or "- 없음"

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

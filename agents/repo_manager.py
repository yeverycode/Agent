from __future__ import annotations

import os
import json
import re
from typing import Any, Dict

from google import genai

from tools.github_api import (
    create_readme_pr,
    fetch_file_contents,
    fetch_tree_paths,
    get_github_repo,
)
from tools.parser import select_candidate_files
from agents.prompts.repo_manager_prompt import REPO_MANAGER_PROMPT_TEMPLATE

class RepoManagerAgent:
    def __init__(self, token: str | None = None, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        self.token = token or os.getenv("MY_GITHUB_TOKEN")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model

        if not self.token:
            raise ValueError("MY_GITHUB_TOKEN이 .env 파일에 설정되어 있지 않습니다.")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

        self.client = genai.Client(api_key=self.api_key)

    def _select_files_with_llm(self, tree_paths: list[str], max_files: int = 8) -> list[str]:
        """
        LLM에게 전체 파일 트리를 보여주고 도메인(백엔드, 프론트, ML, 게임 등)을 스스로 파악하여 
        해당 도메인에서 가장 중요한 핵심 파일을 추론
        """
        valid_extensions = (
            '.py', '.js', '.ts', '.java', '.html', '.css', '.md', '.json', '.toml', '.xml', '.yml', '.yaml',
            '.ipynb', '.cpp', '.hpp', '.c', '.h', '.cs', '.go', '.rs', '.tf', '.sh'
        )
        text_paths = [p for p in tree_paths if p.endswith(valid_extensions) or '.' not in p.split('/')[-1]]
        
        tree_text = "\n".join(text_paths)
        
        prompt = REPO_MANAGER_PROMPT_TEMPLATE.format(
                    max_files=max_files,
                    tree_text=tree_text
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            result_text = response.text
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            parsed_data = json.loads(result_text)
            
            print("\n💡 [AI 도메인 추론 결과]")
            print(f" - 도메인: {parsed_data.get('domain', 'Unknown')}")
            print(f" - 근  거: {parsed_data.get('reasoning', 'No reasoning provided')}")
            
            selected_files = parsed_data.get("selected_files", [])
                
            # 실제로 존재하는 파일인지 확인
            validated_files = [f for f in selected_files if f in tree_paths]
            return validated_files[:max_files]
            
        except Exception as e:
            print(f"⚠️ LLM 파일 선택 중 오류 발생: {e}")
            return select_candidate_files(tree_paths, max_files=max_files)

    def extract_project_data(self, repo_name: str) -> Dict[str, Any]:
        """
        깃허브 프로젝트 전체 트리 추출 및 LLM 선별 핵심 파일 반환
        """
        repo = get_github_repo(self.token, repo_name)
        
        tree_paths = fetch_tree_paths(repo)
        
        candidate_paths = self._select_files_with_llm(tree_paths, max_files=10)
        
        for path in candidate_paths:
            print(f" - {path}")
        print()
        
        selected_files = fetch_file_contents(repo, candidate_paths)

        return {
            "status": "success",
            "repo_name": repo_name,
            "repo_url": repo.html_url,
            "tree_paths": tree_paths,
            "selected_files": selected_files,
        }

    def publish_readme(self, repo_name: str, readme_content: str) -> Dict[str, Any]:
        """
        작성된 README.md를 받아 깃허브에 PR 생성
        """
        try:
            repo = get_github_repo(self.token, repo_name)
            pr_url = create_readme_pr(repo, readme_content)
            
            return {
                "status": "success",
                "pr_url": pr_url
            }
        except Exception as e:
            return {
                "status": "fail",
                "error": str(e)
            }

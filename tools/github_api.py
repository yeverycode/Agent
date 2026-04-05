from __future__ import annotations

import time
from typing import Dict, List

from github import Github
from github.Repository import Repository


def get_github_repo(token: str, repo_name: str) -> Repository:
    """
    타겟 레포지토리 객체 가져오기
    """
    g = Github(token)
    return g.get_repo(repo_name)


def fetch_tree_paths(repo: Repository) -> List[str]:
    """
    레포지토리의 전체 파일/폴더 트리 가져오기
    """
    default_branch = repo.default_branch
    branch = repo.get_branch(default_branch)
    tree = repo.get_git_tree(branch.commit.sha, recursive=True)
    
    return [element.path for element in tree.tree if element.type == "blob"]


def fetch_file_contents(repo: Repository, file_paths: List[str]) -> Dict[str, str]:
    """
    매개변수로 받은 특정 파일들의 텍스트만 추출하여 딕셔너리로 반환
    """
    contents_dict = {}
    for path in file_paths:
        try:
            file_content = repo.get_contents(path)
            contents_dict[path] = file_content.decoded_content.decode("utf-8")
        except Exception as e:
            print(f"⚠️ 깃허브 파일 읽기 실패 ({path}): {e}")
            
    return contents_dict


def create_readme_pr(repo: Repository, readme_content: str) -> str:
    """
    새 브랜치 생성 후 README.md 생성/수정 커밋한 후 PR 오픈
    """
    base_branch_name = repo.default_branch 
    new_branch_name = f"ai/update-readme-{int(time.time())}"
    commit_message = "docs: AI README 업데이트"

    base_branch = repo.get_branch(base_branch_name)
    repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=base_branch.commit.sha)
    
    try:
        contents = repo.get_contents("README.md", ref=new_branch_name)
        repo.update_file(
            contents.path, commit_message, readme_content, 
            contents.sha, branch=new_branch_name
        )
    except:
        repo.create_file("README.md", commit_message, readme_content, branch=new_branch_name)

    # 타겟 레포의 소유자를 멘션해서 알림을 주는 용도
    owner_id = repo.owner.login

    pr_title = "[AI] Docs: README.md 생성 및 업데이트"
    pr_body = f"""@{owner_id}"""
    
    pr = repo.create_pull(
        title=pr_title, body=pr_body, 
        head=new_branch_name, base=base_branch_name
    )
    
    return pr.html_url
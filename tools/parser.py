from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


IMPORTANT_ROOT_FILES = {
    "readme.md",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "dockerfile",
    "docker-compose.yml",
    ".env.example",
    ".env",
}


PRIORITY_FILE_KEYWORDS = [
    "readme.md",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "main.py",
    "app.py",
    "server.py",
    "server.js",
    "server.ts",
    "index.js",
    "index.ts",
    "app.tsx",
    "app.jsx",
    "main.ts",
    "main.tsx",
    "routes.py",
    "urls.py",
    "settings.py",
]


def summarize_tree_structure(tree_paths: List[str]) -> Dict[str, Any]:
    """
    저장소 트리 경로 목록을 받아 상위 디렉토리 분포와 중요한 루트 파일을 요약한다.
    """
    top_dirs = Counter()
    root_files = []
    extension_counter = Counter()

    for path in tree_paths:
        parts = path.split("/")

        # 루트 파일
        if len(parts) == 1:
            if path.lower() in IMPORTANT_ROOT_FILES:
                root_files.append(path)

        # 최상위 디렉토리 카운트
        if len(parts) > 1:
            top_dirs[parts[0]] += 1

        # 확장자 카운트
        if "." in parts[-1]:
            ext = parts[-1].split(".")[-1].lower()
            extension_counter[ext] += 1

    return {
        "top_directories": dict(top_dirs.most_common(10)),
        "important_root_files": sorted(root_files),
        "extension_summary": dict(extension_counter.most_common(10)),
        "total_paths": len(tree_paths),
    }


def select_candidate_files(tree_paths: List[str], max_files: int = 8) -> List[str]:
    """
    분석에 우선적으로 사용할 핵심 파일 후보를 규칙 기반으로 선택한다.
    """
    selected: List[str] = []
    lower_map = {p.lower(): p for p in tree_paths}

    # 1차: 우선순위 높은 파일
    for keyword in PRIORITY_FILE_KEYWORDS:
        for path_lower, original in lower_map.items():
            if path_lower.endswith(keyword) and original not in selected:
                selected.append(original)
                if len(selected) >= max_files:
                    return selected

    # 2차: 주요 디렉토리 안의 대표 코드 파일
    for path in tree_paths:
        path_lower = path.lower()
        if path in selected:
            continue

        if (
            any(folder in path_lower for folder in ["src/", "app/", "pages/", "components/", "backend/", "frontend/"])
            and path_lower.endswith((".py", ".js", ".ts", ".tsx", ".jsx"))
        ):
            selected.append(path)
            if len(selected) >= max_files:
                return selected

    return selected


def extract_structure_hints(tree_paths: List[str]) -> Dict[str, Any]:
    """
    구조 기반 힌트를 추출한다.
    (기술 스택/아키텍처)에서도 재사용 가능하도록 설계.
    """
    hints = {
        "has_frontend": False,
        "has_backend": False,
        "has_components_dir": False,
        "has_pages_dir": False,
        "has_api_dir": False,
        "has_docker": False,
        "has_readme": False,
        "possible_framework_files": [],
    }

    for path in tree_paths:
        p = path.lower()

        if "frontend/" in p:
            hints["has_frontend"] = True
        if "backend/" in p or "server/" in p:
            hints["has_backend"] = True
        if "components/" in p:
            hints["has_components_dir"] = True
        if "pages/" in p:
            hints["has_pages_dir"] = True
        if "api/" in p:
            hints["has_api_dir"] = True
        if "dockerfile" in p or "docker-compose" in p:
            hints["has_docker"] = True
        if p == "readme.md":
            hints["has_readme"] = True

        if any(name in p for name in ["package.json", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle"]):
            hints["possible_framework_files"].append(path)

    return hints


def build_analysis_context(
    repo_name: str,
    repo_url: str,
    tree_paths: List[str],
    file_contents: Dict[str, str],
) -> str:
    """
    LLM이 읽기 좋은 분석용 컨텍스트 문자열을 생성한다.
    """
    structure_summary = summarize_tree_structure(tree_paths)
    structure_hints = extract_structure_hints(tree_paths)

    lines: List[str] = []

    lines.append("=== REPOSITORY META ===")
    lines.append(f"Repository name: {repo_name}")
    lines.append(f"Repository URL: {repo_url}")

    lines.append("\n=== TREE SUMMARY ===")
    lines.append(f"Total paths: {structure_summary['total_paths']}")
    lines.append(f"Top directories: {structure_summary['top_directories']}")
    lines.append(f"Important root files: {structure_summary['important_root_files']}")
    lines.append(f"Extension summary: {structure_summary['extension_summary']}")

    lines.append("\n=== STRUCTURE HINTS ===")
    lines.append(str(structure_hints))

    lines.append("\n=== REPOSITORY TREE (partial) ===")
    for path in tree_paths[:300]:
        lines.append(path)

    lines.append("\n=== SELECTED FILE CONTENTS ===")
    for path, content in file_contents.items():
        lines.append(f"\n--- FILE: {path} ---")
        lines.append(content[:4000])

    return "\n".join(lines)
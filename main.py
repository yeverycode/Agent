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
    
    github_token = os.getenv("MY_GITHUB_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
        
    if not github_token or not gemini_api_key:
        print("필수 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
        
    TARGET_REPO = "YourGitHubID/YourRepoName" # 분석 레포 설정
    MODEL = "gemini-2.5-flash"

    print(f"[README 생성 에이전트] '{TARGET_REPO}' 분석을 시작합니다.\n")

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
            print(f"\n 성공! README가 생성되었습니다.")
            print(f"파일 위치: {final_readme.get('saved_path')}")
            print(f"체크리스트: {final_readme.get('section_check')}")

    except Exception as e:
        print(f"\n 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
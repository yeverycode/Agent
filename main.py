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
        
    TARGET_REPO = "tishakong/SMWU_CG_LAB01" # 분석 레포 설정
    MODEL = "gemini-2.5-flash"

    print(f"[README 생성 에이전트] '{TARGET_REPO}' 분석을 시작합니다.\n")

    try:
        # 각 에이전트에 토큰 주입
        repo_mgr = RepoManagerAgent(token=github_token, api_key=gemini_api_key, model=MODEL)
        analyst = AnalystAgent(api_key=gemini_api_key, model=MODEL)
        tech_exp = TechExpertAgent(api_key=gemini_api_key, model=MODEL)
        writer = WriterAgent(api_key=gemini_api_key, model=MODEL, mode="portfolio")

        # ---------------------------------------------------------
        # Step 1: RepoManager - 데이터 추출
        # ---------------------------------------------------------
        # 전체 트리 구조 파악 및 핵심 파일 내용 수집
        project_data = repo_mgr.extract_project_data(TARGET_REPO)
        if project_data.get("status") == "fail":
            print(f"❌ 데이터 추출 실패: {project_data.get('error')}")
            return

        # ---------------------------------------------------------
        # Step 2: Analyst - 프로젝트 구조 및 기능 분석
        # ---------------------------------------------------------
        print("\n🔍 Analyst 에이전트가 프로젝트를 분석 중입니다...")
        analyst_output = analyst.run(project_data)
        
        # 분석 결과(JSON 문자열)를 파싱하여 데이터 객체에 저장
        try:
            # Analyst가 반환한 raw_analysis(JSON string)를 dict로 변환
            raw_analysis_str = analyst_output.get("analysis_result", "{}")
            # JSON 코드 블록 기호(```json ... ```) 제거 로직 포함
            if "```json" in raw_analysis_str:
                raw_analysis_str = raw_analysis_str.split("```json")[1].split("```")[0].strip()
            
            analysis_dict = json.loads(raw_analysis_str)
            project_data["analysis_summary"] = analysis_dict
        except Exception as e:
            print(f"⚠️ 분석 결과 파싱 중 오류 발생: {e}")
            project_data["analysis_summary"] = {}

        # ---------------------------------------------------------
        # Step 3: TechExpert - 기술 스택 및 아키텍처 분석
        # ---------------------------------------------------------
        print("\n💻 TechExpert 에이전트가 기술 스택을 정리 중입니다...")
        tech_output = tech_exp.run(analyst_output)
        
        if tech_output.get("status") == "success":
            project_data["tech_summary"] = tech_output.get("tech_summary")
        else:
            print(f"⚠️ 기술 분석 실패: {tech_output.get('error')}")
            project_data["tech_summary"] = {}

        # ---------------------------------------------------------
        # Step 4: Writer - README 생성
        # ---------------------------------------------------------
        print("\n✍️ Writer 에이전트가 README 초안을 작성하고 있습니다...")
        writer_output = writer.run(project_data)
        
        if writer_output.get("status") == "success":
            final_readme = writer_output.get("readme_markdown")
            print(f"✅ README 생성 완료! 로컬 저장 경로: {writer_output.get('saved_path')}")
        else:
            print("❌ README 생성 실패")
            return

        # ---------------------------------------------------------
        # Step 5: RepoManager - PR 생성 및 게시
        # ---------------------------------------------------------
        print("\n📤 깃허브에 Pull Request를 생성합니다...")
        publish_result = repo_mgr.publish_readme(TARGET_REPO, final_readme)
        
        if publish_result.get("status") == "success":
            print("\n" + "="*50)
            print("🎉 모든 작업이 완료되었습니다!")
            print(f"👉 생성된 PR 확인하기: {publish_result.get('pr_url')}")
            print("="*50)
        else:
            print(f"❌ PR 생성 실패: {publish_result.get('error')}")

    except Exception as e:
        print(f"\n❌ 실행 중 예상치 못한 에러 발생: {e}")

if __name__ == "__main__":
    main()
import os
import json
import re
from google import genai
from dotenv import load_dotenv
from agents.prompts.tech_expert_prompt import TECH_EXPERT_PROMPT_TEMPLATE

load_dotenv()

def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 .env 파일에 없습니다.")
    return api_key

def build_tech_prompt(analysis_context: str) -> str:
    return TECH_EXPERT_PROMPT_TEMPLATE.format(analysis_context=analysis_context)

def generate_tech_report(prompt: str, model_name: str, api_key: str = None) -> str:
    current_key = api_key or get_api_key()
    client = genai.Client(api_key=current_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text

def extract_tech_json(response_text: str) -> dict:
    try:
        json_pattern = r"\{.*\}"
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(response_text)
    except Exception as e:
        return {"error": "Parsing Failed", "details": str(e)}
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from agents.prompts import TECH_EXPERT_PROMPT_TEMPLATE

load_dotenv()

def get_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY가 .env 파일에 없습니다.")
    return api_key

def build_tech_prompt(analysis_context: str) -> str:
    return TECH_EXPERT_PROMPT_TEMPLATE.format(analysis_context=analysis_context)

def generate_tech_report(prompt: str, model_name: str) -> str:
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
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
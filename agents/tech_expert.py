from __future__ import annotations
from typing import Any, Dict
from tools.tech_utils import build_tech_prompt, generate_tech_report, extract_tech_json

class TechExpertAgent:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model_name = model

    def run(self, analyst_result: Dict[str, Any]) -> Dict[str, Any]:
        analysis_context = analyst_result.get('analysis_context', '')
        if not analysis_context:
            return {"status": "fail", "error": "Context is missing"}
    
        prompt = build_tech_prompt(analysis_context)
        raw_response = generate_tech_report(prompt, self.model_name)
        extracted_data = extract_tech_json(raw_response)
        
        return {
            "status": "success" if "error" not in extracted_data else "fail",
            "tech_summary": extracted_data.get("tech_summary", extracted_data) 
        }
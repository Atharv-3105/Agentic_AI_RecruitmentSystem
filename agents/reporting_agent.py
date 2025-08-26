import json
import google.generativeai as genai
from google.generativeai import GenerationConfig

from core.config import GOOGLE_API_KEY
from agents.resume_parser import ScreeningResult


class ReportingAgent:
    def __init__(self):
        
        if not GOOGLE_API_KEY:
            raise ValueError("API Key missing!!!!")
        genai.configure(api_key=GOOGLE_API_KEY)

        #Response type will be in Markdown/Plain-Text
        self.generation_config = GenerationConfig(response_mime_type="text/plain")
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=self.generation_config
        )
        
    def _build_prompt(self, screening_json: dict)->str:
        
        #Extract the Key Parts for better Readability
        score = screening_json.get('match-score', 'N/A')
        summary = screening_json.get('summary', 'No summary provided.')
        strengths = "\n".join([f"- {s}" for s in screening_json.get('strengths', [])])
        gaps = "\n".join([f"- {g}" for g in screening_json.get('gaps', [])])
        
        return f"""
        You are an AI assistant for a recruitment team. Your task is to format the following screening analysis into a professional, concise and easy-to-read report for a busy hiring manager. Use Markdown for formatting.
        
        ### Candidate Screening Analysis ###
        
        **Match Score:** {score} / 100
        
        **AI Summary:**
        {summary}
        
        **Strengths:**
        {strengths}
        
        **Gaps / Areas for Review:**
        {gaps}
        
        ---
        **Your Task:**
        Rewrite and format the above information into a clean, professional report. Use clear headings, bullet points and a professional tone. Do not add any new information.  
    
    
        **Final Report:**
    """
    
    
    def generate_prompt(self, screening_data: dict) -> str:
        
        try:
            ScreeningResult(**screening_data)
            
            prompt = self._build_prompt(screening_data)
            response = self.model.generate_content(prompt)
            
            return response.text.strip()
        
        except Exception as e:
            return f"An error occured during report geneartion: {str(e)}"
            
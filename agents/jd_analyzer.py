import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import ValidationError
from typing import List

from agents.resume_parser import ParsedJD, SkillsRequired
from core.config import GOOGLE_API_KEY

class JDAnalyzerAgent:
    def __init__(self):
        
        if not GOOGLE_API_KEY:
            raise ValueError("API Key not found in Environment vairables")
        genai.configure(api_key=GOOGLE_API_KEY)
        
        self.generation_config = GenerationConfig(response_mime_type="application/json")
        self.model = genai.GenerativeModel(
            model_name = "gemini-1.5-flash",
            generation_config=self.generation_config
        )
        
    def build_prompt(self, jd_text: str) -> str:
        return f"""
        You are an expert technical recruiter. Your task is to analyze the following job description(JD) and extract the key requirements into a structures JSON format.
        
        ###JSON SCHEMA TO FOLLOW###
        {{
            "job_title": string (The specific title, e.g., 'Senior Python Developer'),
            "required_skills":[
                {{
                    "skill": "string(e.g., 'Python', 'React', 'Pytorch')",
                    "level": "string(e.g., 'Expert', 'Intermediate', 'Basic', 'Proficient')"
                }}
            ],
            "preferred_skills":[
                {{
                    "skill": "string(e.g, 'Git/Github', 'Go')",
                    "level": "string(e.g., 'Proficient', 'Familiar')"
                    
                }}  
            ],
            "required_years_of_experience": "integer (The minimum number of years of experience requires, e.g., 5)",
            "education_requirements": "string (e.g., 'Bachelor's degree in Computer Science or related field')"
        }}
        
        ###KEY INSTRUCTIONS###
        - Distinguish between **required** skills(must-haves) and **preferred** skills (nice-to-haves).
        - If a specific number of years of experience is mentioned,extract it as an integer. If a range is given (e.g., 3-7 years), use the lower number. If none is mentioned, use 0.
        
        ###JOB DESCRIPTION to ANALYZE###
        {jd_text}
        
        ###JSON OUTPUT ###
    """
    
    
    def parse_jd(self, jd_text: str) ->dict:
        
        try:
            prompt = self.build_prompt(jd_text)
            response = self.model.generate_content(prompt)
            
            parsed_json = json.loads(response.text)
            validated_data = ParsedJD(**parsed_json)
            return validated_data.dict()
        
        except (json.JSONDecodeError, ValidationError) as e:
            return {"error": f"Failed to parse or validate JD model output. Details: {e}"}
        except Exception as e:
            return {"error": f"Unknown error occured. Details: {e}"}    
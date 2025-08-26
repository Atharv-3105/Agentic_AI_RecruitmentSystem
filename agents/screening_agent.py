import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import ValidationError

from core.config import GOOGLE_API_KEY
from agents.resume_parser import ParsedResume, ParsedJD, ScreeningResult


class ScreeningAgent:
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("API Key not found.!!")
        genai.configure(api_key=GOOGLE_API_KEY)
        
        self.generation_config = GenerationConfig(response_mime_type="application/json")
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=self.generation_config)
        
    def _build_prompt(self, resume_json: dict, jd_json: dict) ->str:
        ''' 
            This function builds a prompt for Gemini to compare a Resume & JD.
        '''
        return f"""
        You are an expert AI Technical Recruiter. Your task is to analyze the following candidate resume and job description (JD), both provided in JSON format. Provide a detailed analysis of the candidate's suitability for the role.

        ### JSON Schema for Your Output ###
        {{
            "match_score": "integer (A score from 0 to 100)",
            "summary": "string (A 2-3 sentence summary of the candidate's fit)",
            "strengths": ["string (A list of reasons why the candidate is a good fit)"],
            "gaps": ["string (A list of areas where the candidate is lacking or does not meet requirements)"]
        }}

        ### Key Instructions ###
        - Base your analysis strictly on the information provided in the JSON data.
        - The match score should reflect how well the candidate's skills, experience, and education align with the JD's requirements.
        - Strengths and gaps should be specific and reference details from both the resume and the JD.

        ---
        ### Candidate Resume Data ###
        {json.dumps(resume_json, indent=2)}
        ---
        ### Job Description Data ###
        {json.dumps(jd_json, indent=2)}
        ---

        ### Your Analysis (JSON Output): ###
        """
    
    def screen(self, resume_data: dict, jd_data: dict)-> dict:
        try:
            validated_resume = ParsedResume(**resume_data)
            validated_jd = ParsedJD(**jd_data)
            
            prompt = self._build_prompt(validated_resume.dict(), validated_jd.dict())
            response = self.model.generate_content(prompt)
            
            parsed_json = json.loads(response.text)
            validated_result = ScreeningResult(**parsed_json)
            return validated_result.model_dump() 
          
        except ValidationError as e:
            return {"error": f"Input Data validation failed. Details: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}
             
            
            
            
    
    
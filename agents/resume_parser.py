import json 
import google.generativeai as genai 
from google.generativeai.types import GenerationConfig
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

from utils.file_handler import extract_text_from_pdf, extract_text_from_docx, extract_text_from_image
from core.config import GOOGLE_API_KEY

#===============Pydantic models for Type-Validation of the LLM output==================
class WorkExperience(BaseModel):
    title: Optional[str] = Field(None, alias = "job_title")
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date:  Optional[str] = None
    responsibilities: Optional[List[str]] = Field(default_factory=list)


class Project(BaseModel):
    title: Optional[str] = Field(None, alias = "project_name")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: Optional[List[str]] = Field(default_factory=list)


class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year_of_completion: Optional[str] = None
    grade: Optional[str] = Field(None, description="The grade, GPA, CGPA, or percentage obtained.")

class ParsedResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    work_experience: List[WorkExperience] = Field(default_factory = list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    
class SkillsRequired(BaseModel):
    skill: str
    level: Optional[str] = Field(None, description="e.g, 'Expert', 'Proficient', 'Familiar'")

class ParsedJD(BaseModel):
    job_title: Optional[str] = None
    required_skills: List[SkillsRequired] = Field(default_factory=list)
    preferred_skills: List[SkillsRequired] = Field(default_factory=list)
    required_years_of_experience: Optional[int] = None
    education_requirements: Optional[str] = None
    
class ScreeningResult(BaseModel):
    match_score: int = Field(..., description="A score from 0 to 100 representing the match quality.")
    summary: str = Field(..., description="A qualitative summary of the candidate's fit.")
    strengths: List[str] = Field(default_factory=list, description = "Specific points where the candidate meets or exceeds requirements.")
    gaps: List[str] = Field(default_factory=list, description = "Specific areas where the candidate is lacking.")
    
#=======================PyDantic Model==================================================
    
    
class ResumeParserAgent:
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("API Key not found")
        genai.configure(api_key = GOOGLE_API_KEY)
        # self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        #Define Generation_config to bound the model to only output JSON
        self.generation_config = GenerationConfig(response_mime_type="application/json")
        try:
            available_models = [m.name for m in genai.list_models()]
            if any("gemini-1.5-flash" in m for m in available_models):
                self.model = genai.GenerativeModel(model_name='gemini-1.5-flash', generation_config=self.generation_config)
                print("Using gemini-1.5-flash")
            else:
                self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=self.generation_config)
                print("Using Gemini-1.5-Flash")
        except Exception as e:
            print("Could not list models. Falling back to Gemini-1.5-flash. Reason: {e}")
            self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=self.generation_config)
            
    def _get_raw_text(self, filename: str, file_bytes: bytes)->str:
        '''
            This function will Determine the filetype and Extract Raw text
        '''
        
        if filename.lower().endswith(".pdf"):
            return extract_text_from_pdf(file_bytes = file_bytes)

        elif filename.lower().endswith(".docx"):
            return extract_text_from_docx(file_bytes)
        
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return extract_text_from_image(file_bytes)
        
        else:
            raise ValueError("Unsupported File Type")
        
    def parse(self, filename: str, file_bytes: bytes)->dict:
        try:
            raw_text = self._get_raw_text(filename, file_bytes)
            
            #Check if raw_text is empty
            if not raw_text:
                return {"Error":"Failed to extract raw text from the resume"}

            prompt = self._build_prompt(raw_text)
            
            #Call the Gemini API
            response = self.model.generate_content(prompt)
            
            parsed_data = ParsedResume(**json.loads(response.text))
            
            #----------------Post-Processing the Parsed_Data to generate Project Title------------
            for project in parsed_data.projects:
                if not project.title and project.responsibilities:
                    generated_title = self._synthesize_title(project.responsibilities)
                    project.title = generated_title
            
            return parsed_data.dict()
        
        #Handle Error-Logic
        except ValueError as ve:
            return {"ValueError": str(ve)}
        
        except json.JSONDecodeError:
            return {"Error": "Failed to Decode JSON from the models's response"}
        
        except ValidationError as e:
            return {"Error": "Model response failed validation", 
                    "details":e.errors()}
            
        except Exception as e:
            return {"Error": f"Unexpected error occured: {str(e)}"}
        
   
    def _build_prompt(self, raw_resume_text: str) -> str:
        return f"""
        You are an expert AI resume parser. Your goal is to extract information into a structured JSON that strictly adheres to the schema below.

        ### JSON Schema & Rules ###
        {{
            "name": "string",
            "email": "string",
            "phone": "string",
            "summary": "string",
            "work_experience": [{{...}}],
            "projects": [
                {{
                    "title": "string (This can be null if no explicit title is found)",
                    "start_date": "string",
                    "end_date": "string",
                    "responsibilities": ["string"]
                }}
            ],
            "education": [
                {{
                    "degree": "string",
                    "institution": "string (The name of the university, college or school)",
                    "year_of_completion": "string",
                    "grade": "string (e.g., '8.5 CGPA', '92%', 'First Class with Distinction')"
                }} 
                ],
            "skills": ["string"]
        }}

        ### Key Instructions ###
        - 'work_experience' is for professional jobs at a company.
        - 'projects' are for academic or personal work.

        ### Resume to Parse ###
        **Resume Text:**
        {raw_resume_text}

        **JSON Output:**
        """
    
    def _synthesize_title(self, responsibilities: List[str]) -> str:
        ''' 
            Agent-2: Takes a list of responsibilities and generates a concise project title.
        '''
        if not responsibilities:
            return "Untitled Project"
        
        responsibilities_text = "-" + "\n-".join(responsibilities)
        prompt = f"""
            You are an expert title generator. Your task is to create ONE concise, descriptive project title (3-7 words) from the responsibilities provided.

            **CRITICAL INSTRUCTIONS:**
            - Your response MUST be the title string itself.
            - Do NOT include JSON formatting, keys (like 'project_title'), braces `{{}}`, or brackets `[]`.
            - Provide ONLY the single best title, not a list of options.

            --- EXAMPLE ---
            Responsibilities:
            - Developed an autonomous video analysis system using a multimodal LLM.
            - Designed a web interface for video upload and structured analysis.
            Project Title:
            Autonomous Video Analysis System
            --- END EXAMPLE ---

            Now, perform the same task for the following:

            **Responsibilities:**
            {responsibilities_text}

            **Project Title:**
            """
        title_response = self.model.generate_content(prompt)
        return title_response.text.strip().replace('"', '')
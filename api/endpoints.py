from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from agents.resume_parser import ResumeParserAgent
from agents.jd_analyzer import JDAnalyzerAgent
from agents.screening_agent import ScreeningAgent
from agents.reporting_agent import ReportingAgent
from agents.resume_parser import ParsedJD, ParsedResume
from pydantic import BaseModel

from db.database import get_document , add_document

router = APIRouter(
    prefix = "/v1",
    tags = ["Resume Analyzer"],
)

#Depenedency Injections to create a single Agent Instance per each request
def get_parser_agent():
    return ResumeParserAgent()
def get_jd_analyzer_agent():
    return JDAnalyzerAgent()
def get_screening_agent():
    return ScreeningAgent()
def get_reporting_agent():
    return ReportingAgent()

#-----------------EndPoints-----------------------

#--------------Endpoint for Resume Upload-------------------
@router.post("/resumes", status_code=201)
async def parse_resume_endpoint(resume_file: UploadFile = File(..., description="Upload your Resume file(PDF,DOCX,PNG,JPG)."),
                                agent: ResumeParserAgent = Depends(get_parser_agent)):
    
    #Set a file-size limit(<=10MB)
    if resume_file.size > 10*1024*1024:
        raise HTTPException(status_code=413, detail = "File size should be <=10MB")
    
    #Check for allowed file-types 
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/png", "image/jpeg"]
    if resume_file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail = "Unsupported File-Type")
    
    try:
        file_content = await resume_file.read()
        structured_data = agent.parse(resume_file.filename, file_content)
        
        if "error" in structured_data:
            raise HTTPException(status_code=500, detail = structured_data)
        
        resume_id = add_document("resumes", structured_data)
        return {"message": "Resume parsed and saved successfully",
                "resume_id": resume_id}
    
    except Exception as e:
        raise HTTPException(status_code= 500, detail = f"An unexpected error occurred during parsing: {str(e)}")
    except HTTPException as he:
        raise he


#-----------------End-Point for JD Upload-------------------------------
class JDText(BaseModel):
    text: str
    
@router.post("/jds/upload-file", status_code=201)
async def parse_jd_file_endpoint(jd_file: UploadFile = File(..., description="A text file(.txt) containing the job description"), 
                                 agent: JDAnalyzerAgent = Depends(get_jd_analyzer_agent)):
    '''
        Accepts Job Decription text file, parses it, and returns structured criteria.
    '''  
    
    #Set a file-size limit(<=2MB)
    if jd_file.size > 2*1024*1024:
        raise HTTPException(status_code=413, detail = "File size should be <=2MB")
    
    if not jd_file.filename.lower().endswith(".txt") or jd_file.content_type != "text/plain":
        raise HTTPException(status_code=412, detail = "Unsupported file type. Please upload a .txt file")
    
    try:
        jd_text_bytes = await jd_file.read()
        jd_text = jd_text_bytes.decode("utf-8")
        
        if not jd_text.strip():
            raise HTTPException(status_code=412, detail = "The uploaded file is empty.")
        
        structured_data = agent.parse_jd(jd_text)
        
        if "error" in structured_data:
            raise HTTPException(status_code=412, details = structured_data)
        
        jd_id = add_document("jds", structured_data)
        return {"message": "JD from file parsed and saved successfully.",
                "jd_id": jd_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail = f"An unexpected error occured during parsing: {str(e)}")

@router.post("/jds/paste-text", status_code = 201)
async def parse_jd_text_endpoint(jd_text: str = Body(..., media_type="text/plain", description="Paste the Job Description text"),
                                 agent: JDAnalyzerAgent = Depends(get_jd_analyzer_agent)):
    
    if not jd_text.strip():
        raise HTTPException(status_code=413, detail="JD Text cannot be empty")
    
    try:
        structured_data = agent.parse_jd(jd_text)
        
        if "error" in structured_data:
            raise HTTPException(status_code=413, detail = structured_data)
        
        jd_id = add_document("jds", structured_data)
        return {"message": "JD from text parsed and saved successfully.",
                "jd_id": jd_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail = f"An unexpected error occurred during parsing: {str(e)}")
    
    

#-----------------------------End-Point for ScreeningAgent----------------------------------
class ScreeningRequestByIds(BaseModel):
    resume_id: str
    jd_id: str

@router.post("/screen", status_code=201)
async def screen_by_ids(request: ScreeningRequestByIds, agent: ScreeningAgent = Depends(get_screening_agent)):
    resume_data = get_document("resumes", request.resume_id)
    jd_data = get_document("jds", request.jd_id)

    if not resume_data:
        raise HTTPException(status_code=404, detail=f"Resume with id '{request.resume_id}' not found.")
    if not jd_data:
        raise HTTPException(status_code=404, detail=f"JD with id '{request.jd_id}' not found.")

    result = agent.screen(resume_data, jd_data)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result)
        
    result["resume_id"] = request.resume_id
    result["jd_id"] = request.jd_id
    screening_id = add_document("screenings", result)
    
    return {"screening_id": screening_id, "result": result}

#-------------------------End-Point For Report Generation Endpoint-----------------------------
@router.get("/reports/{screening_id}", status_code = 200)
async def get_screening_report(
    screening_id: str,
    agent: ReportingAgent = Depends(get_reporting_agent)
):
    """ 
        Fetches a screening result by its ID and generates a Human-Readable report.
    """
    screening_data = get_document("screenings", screening_id)
    
    if not screening_data:
        raise HTTPException(status_code = 404, detail = f"Screeing with id '{screening_id}' not found.")
    
    report_markdown = agent.generate_prompt(screening_data)
    
    if "An error occurred" in report_markdown:
        raise HTTPException(status_code = 500, detail = report_markdown)
    
    return {"screening_report":report_markdown, "screening_id":screening_id}



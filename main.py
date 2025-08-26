from fastapi import FastAPI
from core.config import GOOGLE_API_KEY #For Testing Purpose Only
import uvicorn
from api import endpoints

app = FastAPI(title = "Agentic_RAG Resume Parser", 
              description = "API for parsing resumes and matching them with job descriptions.",
              version = "1.0.0")

#Add the router from the Endpoints.py
app.include_router(endpoints.router)
@app.get("/", tags=["Root"])
def read_root():
    return {"status":"API is running"}
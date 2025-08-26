import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

#Get the API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

#Configure the Gemini Model
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


#Configure the Database
MONGODB_CONNECTION = "mongodb://localhost:27017/"
DB_NAME = "Agentic_RAG"
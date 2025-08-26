import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
API = os.getenv("GOOGLE_API_KEY")

if not API:
    print("API_KEY not found in .env file")
else:
    try:
        genai.configure(api_key=API)
        print("API Key configured. Checking for available models")
        
        model_count = 0
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
                model_count += 1
        
        if model_count == 0:
            print("No models supporting 'generateContent'found.")
        else:
            print(f"\n Found {model_count} usable models.")
            
    except Exception as e:
        print("Error occured: {e}")
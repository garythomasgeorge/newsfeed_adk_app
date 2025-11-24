import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv("backend/.env")
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Available models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"- {model.name}")

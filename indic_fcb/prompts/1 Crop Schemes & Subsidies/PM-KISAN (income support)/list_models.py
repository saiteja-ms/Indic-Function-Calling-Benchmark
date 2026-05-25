import os
from google import genai
from dotenv import load_dotenv

# Load .env
env_path = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\.env"
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Fetching available models...")
try:
    for model in client.models.list():
        # Print every model name available to this key
        print(f" - {model.name}")
except Exception as e:
    print(f"Error fetching models: {e}")

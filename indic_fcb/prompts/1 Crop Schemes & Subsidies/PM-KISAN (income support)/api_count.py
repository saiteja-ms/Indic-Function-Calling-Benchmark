import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file explicitly from the root directory
env_path = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\.env"
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("API Key not found! Please check your .env file.")
    exit(1)

# Read the file
file_path = r"C:\Users\SAI TEJA M S\Documents\UGRP Research Work\Indic-Function-Calling-Benchmark\indic_fcb\prompts\1 Crop Schemes & Subsidies\PM-KISAN (income support)\p5_intents.txt"
prompt_text = Path(file_path).read_text(encoding="utf-8")

# Directly call the Gemini REST API for counting tokens (using gemini-pro which is globally available)
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:countTokens?key={api_key}"

payload = {
    "contents": [{
        "parts": [{"text": prompt_text}]
    }]
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    data = response.json()
    print(f"Exact Token Count: {data.get('totalTokens')}")
else:
    print(f"API Error: {response.status_code}")
    print(response.text)
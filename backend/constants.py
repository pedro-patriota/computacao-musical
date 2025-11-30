import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
WORKFLOW_NAME = "computacao-musical-rosa"
OUTPUT_DIR = "results"
DEMO_DIR = "demo"

if not API_KEY:
    print("Warning: API_KEY not found. Check your .env file.")
else:
    print("API_KEY loaded successfully.")
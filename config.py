import os 
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY", "")

LLM_MODEL          = os.getenv("LLM_MODEL",          "gemini-2.0-flash")
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "gemini-2.5-pro")

APP_HOST =  os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

SESSION_TTL_SECONDS = 3600

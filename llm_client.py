import os
import re
import json 
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

from config import GOOGLE_GEMINI_API_KEY, LLM_MODEL, ORCHESTRATOR_MODEL

_client = genai.Client(
    api_key=GOOGLE_GEMINI_API_KEY or os.environ.get('GOOGLE_GEMINI_API_KEY','')
)
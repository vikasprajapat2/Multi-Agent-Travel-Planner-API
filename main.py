import os 
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
from typing import Optional

from agents.planner import PlannerAgent
from memory.Session_store import SessionStore
from config import APP_HOST, APP_PORT

#APP setup

app = FastAPI(
    title= "Multi-Agent Travel Planner API"
    description= "AI-powered travel planning - flights , hotels, itinerary, budget",
    version = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"]
    allow_methods = ["*"]
    allow_headers = ["*"] 
)

Planner = PlannerAgent()

# Pydantic request/ response models
class PlanRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ReplanRequest(BaseModel):
    session_id: str
    change: str
    label: Optional[str] = None

class sessionResponse(BaseModel):
    session_id: str

# Routes
@app.get("/")

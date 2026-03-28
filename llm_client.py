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

def chat(
    prompt:   str,
    system:   str  =""
    model:    str = LLM_MODEL,
    max_tokens: int  = 2048,
    temperature: float = 0.3, 
) -> str:

    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    try:
        response = _client.models.generate_content(
            model = model,
            contents = full_prompt,
            config = types.GenerateContentConfig(
                max_output_tokens = max_tokens,
                temperature = temperature,
            ),
        )

        return response.text or ""

    except Exception as e:
        raise RuntimeError(f"Gemini api error (model={model}):{e}") from e

def chat_json(
        prompt: str, 
        system:  str  = ''
        model: str = LLM_MODEL,
        max_tokens: 2048,
) -> dict:

    raw = chat(
        prompt = prompt,
        system = system,
        model = model,
        max_tokens = max_tokens, 
        temperature = 0.1,,
    )

    cleaned = re.sub(r"'''json\s*|'''\s*", "" , raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", cleaned,re.DOTALL)
    if match:
        try:
            return json.loads(match,,group(1))
        except json.JSONDecodeError:
            pass

    return {"_parse_error" : True, "raw": raw}


def orchestrator_chat(
        prompt: str,
        system: str = "",
        max_tokens: int = 1024,
) -> str:
    
    return chat(
        prompt = prompt,
        system = system, 
        model = ORCHESTRATOR_MODEL,
        max_tokens = max_tokens,
    )

def orchestrator_json(
        prompt: str, 
        system: str = ""
        max_tokens: int = 1024,
) -> dict:

    raw = orchestrator_chat(prompt=prompt, system= system, max_tokens= max_toekens)

    cleaned = re.sub(r "```json\s*|```\s*","", raw).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return {"_parse_error": True, "rew": raw}


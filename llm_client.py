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
    system:   str  ="",
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
        system:  str  = "",
        model: str = LLM_MODEL,
        max_tokens: int = 2048,
) -> dict:

    raw = chat(
        prompt = prompt,
        system = system,
        model = model,
        max_tokens = max_tokens, 
        temperature = 0.1,
    )

    cleaned = re.sub(r"'''json\s*|'''\s*", "" , raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", cleaned,re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
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
        system: str = "",
        max_tokens: int = 1024,
) -> dict:

    raw = orchestrator_chat(prompt=prompt, system= system, max_tokens= max_tokens)

    cleaned = re.sub(r"```json\s*|```\s*","", raw).strip()

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


if __name__ == "__main__":
    print("=" * 55)
    print("  llm_client.py — self test")
    print("=" * 55)
 
    # ── Test 1: Basic text response ───────────────────────────────────────────
    print("\n[Test 1]  chat() — basic text call")
    print("  Sending: 'What is the capital of India? One word only.'")
    try:
        reply = chat(
            prompt = "What is the capital of India? Reply with one word only.",
            system = "You are a geography assistant. Be extremely brief.",
        )
        print(f"  Response: {reply.strip()}")
        print("   chat() is working")
    except RuntimeError as e:
        print(f"   {e}")
        print("  → Check your GOOGLE_GEMINI_API_KEY in .env")
 
    # ── Test 2: JSON output ───────────────────────────────────────────────────
    print("\n[Test 2]  chat_json() — structured output")
    print('  Asking for: {"city": "...", "country": "..."}')
    try:
        result = chat_json(
            prompt = (
                'Return ONLY this JSON (fill in values): '
                '{"city": "Mumbai", "country": "India", "currency": "INR"}'
            ),
            system = "Return ONLY valid JSON. No markdown. No explanation.",
        )
        if result.get("_parse_error"):
            print(f"  Parse error. Raw response: {result['raw'][:100]}")
        else:
            print(f"  Parsed dict: {result}")
            print("  chat_json() is working")
    except RuntimeError as e:
        print(f" {e}")
 
    # ── Test 3: Real travel parsing preview ───────────────────────────────────
    print("\n[Test 3]  chat_json() — travel request parsing preview")
    print("  Input: '5 day Goa trip under 30k for couple'")
    try:
        result = chat_json(
            prompt = (
                "Parse this travel request and return ONLY JSON, no other text:\n"
                "Request: '5 day Goa trip under 30k for couple'\n\n"
                "Return: {\"destination\": \"\", \"budget\": 0, "
                "\"duration_days\": 0, \"travel_type\": \"\"}"
            ),
            system = "You are a travel request parser. Return ONLY valid JSON.",
        )
        if result.get("_parse_error"):
            print(f"   Parse failed. Raw: {result['raw'][:100]}")
        else:
            print(f"  Parsed: {result}")
            print("   Travel JSON parsing works — ready for Part 5 (Planner agent)")
    except RuntimeError as e:
        print(f"  {e}")
 
    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  Part 1 complete!")
    print("  You now have:")
    print("    config.py    — settings + TravelRequest dataclass")
    print("    lm_client.py — Gemini wrapper (4 functions)")
    print()
    print("  Next → Part 2: Data models + session memory")
    print("  Say 'Part 2' to continue.")
    print("=" * 55)
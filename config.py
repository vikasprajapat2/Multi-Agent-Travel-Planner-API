import os 
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

LLM_MODEL          = os.getenv("LLM_MODEL",          "mixtral-8x7b-32768")
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "mixtral-8x7b-32768")

APP_HOST =  os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

USE_MOCK_APIS      = os.getenv("USE_MOCK_APIS",      "false").lower() == "true"
DEFAULT_CURRENCY   = os.getenv("DEFAULT_CURRENCY",   "INR")

SESSION_TTL_SECONDS = 3600

@dataclass
class TravelRequest:
    destination: str

    origin:        str       = "Delhi"       # departure city
    budget:        float     = 30000.0       # total trip budget in INR
    currency:      str       = "INR"
    start_date:    str       = ""            # "YYYY-MM-DD"
    end_date:      str       = ""            # "YYYY-MM-DD"
    duration_days: int       = 5
    travel_type:   str       = "couple"      # solo|couple|family|honeymoon|group
    passengers:    int       = 2             # number of adults
    children:      int       = 0
    raw_query:     str       = "" 


    preferences: list[str] = field(default_factory = list)

    def is_family(self) -> bool:
        return self.travel_type == "family" or self.children > 0
    
    def is_luxury(self) -> bool:
        return "luxury" in self.preferences
    
    def pref_str(self)-> str:
        return ','.join(self.preferences) if self.preferences else 'general sightseeing'
 
    def budget_per_day(self) -> float:
        return self.budget / max(self.duration_days,1)
    
    def budget_per_person(self) -> float:
        return self.budget / max(self.passengers,1)
    
    def nights(self) -> int:
        return max(self.duration_days -1,1)
    
if __name__ == "__main__":
    print("="*55)
    print(' config.py - self test')
    print("=" * 55)

    print('\n[1] API key check')
    if GROQ_API_KEY and GROQ_API_KEY != "gsk_your_groq_api_key_here":
        visible = GROQ_API_KEY[:8] + '...' + GROQ_API_KEY[-4:]
        print(f"   Key loaded: {visible}")

    else:
        print(' key missing! Steps:')
        print(' 1. cp. env.example .env')
        print(" 2.. open .env -> pest key from aistudio.google.com/apikey")

    print("\n[2] settings")
    print(f"  LLM_MODEL          = {LLM_MODEL}")
    print(f"   ORCHESTRATOR_MODEL = {ORCHESTRATOR_MODEL}")
    print(f"   USE_MOCK_APIS      = {USE_MOCK_APIS}")
    print(f"   DEFAULT_CURRENCY   = {DEFAULT_CURRENCY}")

    print("\n[3] TravelRequest demo")

    req = TravelRequest(
        destination   = "Goa",
        origin        = "Ahmedabad",
        budget        = 30000,
        duration_days = 5,
        travel_type   = "couple",
        preferences   = ["beach", "food"],
        passengers    = 2,
    )
 
    print(f"  destination    : {req.destination}")
    print(f"  origin         : {req.origin}")
    print(f"  budget         : ₹{req.budget:,.0f}")
    print(f"  duration       : {req.duration_days} days / {req.nights()} nights")
    print(f"  travel_type    : {req.travel_type}")
    print(f"  preferences    : {req.pref_str()}")
    print(f"  budget_per_day : ₹{req.budget_per_day():,.0f}")
    print(f"  is_family()    : {req.is_family()}")
    print(f"  is_luxury()    : {req.is_luxury()}")
 
    print("\n   TravelRequest works correctly")
    print("\n" + "=" * 55)
    print("  Next → run:  python llm_client.py")
    print("=" * 55)


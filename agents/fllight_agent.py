import os
import sys 
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TravelRequest
from llm_client import chat_json
from tools.flight_api import search_flights 

#System prompt

SYSTEM_PROMPT = """You are a specialist flight search agent for Indian travellers.
 
Your job: given a list of available flights and trip details, select the
best options and explain your reasoning briefly.
 
Rules:
- Always pick the best value flight as "recommended"
- Include up to 2 alternatives
- Consider: price, stops, departure time, airline reputation
- Non-stop preferred over 1-stop for same price range
- For families: prefer morning departures
- For honeymoon: prefer reputable airlines
 
Return ONLY valid JSON, no markdown, no explanation outside JSON:
{
  "recommended": {flight dict},
  "alternatives": [{flight dict}, ...],
  "best_deal_note": "One sentence why this is the best choice",
  "round_trip_cost": 12000,
  "per_person_cost": 6000
}"""

# flight sagents class

class FlightAgent:
    name = 'FlightAgent'

    def run(self, request: TravelRequest) -> dict:

        flight_budget_total = request.budget * 0.30
        budget_per_person = flight_budget_total / max(request.passengers, 1)

        raw_options = search_flights(
            origin = request.origin, 
            destination= request.destination,
            date = request.start_date or "2025-06-01",
            passengers= request.passengers,
            budget_per_person= budget_per_person
        )

        if not raw_options:
            return self._empty_result("NO flights found for this route and date")

        prompt = f"""Trip details:
    - Route: {request.origin} → {request.destination}
    - Date: {request.start_date}
    - Passengers: {request.passengers} adults
    - Total flight budget: ₹{flight_budget_total:,.0f}
    - Travel type: {request.travel_type}
    - Preferences: {request.pref_str()}
    
    Available flights (already filtered by budget):
    {json.dumps(raw_options, indent=2)}
    
    Pick the best recommended flight and up to 2 alternatives.
    Return ONLY the JSON structure specified. No other text."""
    
        result = chat_json(prompt = prompt, system=SYSTEM_PROMPT, max_tokens=800)

        if result.get("_parse_error") or not result.get('recommended'):
            print(f" [{self.name}] JSON parse issue - using fallback")

        return result
    
    def _fallback(self, raw_option: list, passengers: int) -> dict:
        best = raw_option[0]
        return {
            "recommended": best,
            'alternatives': raw_option[1:3],
            'best_deal_note': "best price available on this route",
            'round_trip_cost': best.get("price_inr", 0),
            'per_person_cost': best.get('price_inr', 0) // max(passengers, 1)
        }
    def _empty_result(self, reason: str) -> dict:
        return {
            'recommended': {},
            "alternatives": [],
            'best_deal_note': reason,
            "round_trip_cost": 0,
            'per_person_cost': 0,
        }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("=" * 55)
    print("  flight_agent.py — self test")
    print("=" * 55)

    agent = FlightAgent()
    tests = [
        TravelRequest(
            destination="Goa", origin="Ahmedabad",
            budget=30000, duration_days=5,
            travel_type="couple", passengers=2,
            start_date="2025-06-15",
            preferences=["beach", "food"],
        ),
        TravelRequest(
            destination="Manali", origin="Delhi",
            budget=50000, duration_days=7,
            travel_type="family", passengers=3, children=1,
            start_date="2025-05-20",
            preferences=["adventure", "nature"],
        ),
    ]

    for req in tests:
        print(f'\n trip: {req.origin}-> {req.destination} | '
            f"{req.travel_type} | ₹{req.budget:,}") 
        result = agent.run(req)

        rec = result.get('recommended', {})
        if rec:
            print(f"  Recommended : {rec.get('airline')} {rec.get('flight_number')}")
            print(f"  Departs     : {rec.get('depart_time')}")
            print(f"  Duration    : {rec.get('duration')}")
            stops = "Non-stop" if rec.get("stops") == 0 else "1 stop"
            print(f"  Stops       : {stops}")
            print(f"  Total cost  : ₹{result.get('round_trip_cost', 0):,}")
            print(f"  Note        : {result.get('best_deal_note', '')}")
        else:
            print("  No flights found")
 
        alts = result.get("alternatives", [])
        if alts:
            print(f"  Alternatives: {len(alts)} option(s)")
            for a in alts:
                print(f"    • {a.get('airline')} {a.get('flight_number')} | ₹{a.get('price_inr',0):,}")
 
    print("\n" + "=" * 55)
    print("  FlightAgent done. Moving to HotelAgent...")
    print("=" * 55)

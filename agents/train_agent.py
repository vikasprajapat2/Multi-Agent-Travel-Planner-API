import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TravelRequest
from llm_client import chat_json
from tools.transport_api import search_trains

SYSTEM_PROMPT ="""You are a specialist indian railway travel agent with deep knowledge of train routes, classes, and booking strategies.
your jon :  given train options and traveller profile, recommend the best train and travel class with clear reasoning.

TRAIN CLASS GUIDE:
    SL (sleeper) - no AC , budget travelers, short overnight journeys
    3A  (AC 3-tier)  — most popular, good comfort, families, medium journeys
    2A  (AC 2-tier)  — more space and privacy, couples, long journeys
    1A  (First AC)   — premium cabins, luxury travellers, honeymoon
    
Rulers:
- Never recommed SL for families with children or honeymoon
- For journeys over 12 hours, recommend at minimum 3A
- Check availability - prefer "Avalable" over "RAC" or "Waitlist"
- Tatkal quota exists for last-minute booking (30% surcharge)
- Booking opens 60 days in andvance on IRCTC

Return ONLY valid JSON:
{
  "recommended": {train dict},
  "alternatives": [{train dict}],
  "best_class": "3A",
  "class_note": "Why this class suits this trip",
  "total_cost": 0,
  "per_person_cost": 0,
  "booking_tip": "Practical tip for booking this train",
  "irctc_search": "train name or number to search on irctc.co.in"
}"""

class TrainAgent:
    name = "TrainAgent0"
    def run(self, request: 'TravelRequest') -> dict:
        if request.travel_type == "honeymoon" or request.is_luxury():
            default_class = "2A"
        elif request.travel_type == "family":
            default_class = "3A"
        elif request.travel_type == "solo" and request.budget < 15000:
            default_class = "SL"
        else:
            default_class = "3A"
 
        date = request.start_date or "2025-06-01"    

        class_up = {"SL": "3A", "3A": "2A", "2A": "1A", "1A": "1A"}
        compare_class = class_up[default_class]

        print(f"Searching {default_class} and {compare_class} class trains...")

        trains_defaults = search_trains(
            origin = request.origin,
            destination =  request.destination,
            date = date,
            passengers = request.passengers,
            travel_class = default_class,
        )

        train_upgrade = search_trains(
            origin = request.origin,
            destination = request.destination,
            date = date,
            passengers = request.passengers,
            travel_class = compare_class
        )

        if not trains_defaults and not train_upgrade:
            return self._empty_result()

        prompt = f"""Find the best train for this trip:
Route      : {request.origin} → {request.destination}
Date       : {date}
Passengers : {request.passengers} adults{f', {request.children} children' if request.children else ''}
Travel type: {request.travel_type}
Budget     : Rs.{request.budget:,.0f} total
Preferences: {request.pref_str()}
{default_class} class options:
{json.dumps(trains_defaults[:3], indent=2)}
{compare_class} class options (upgrade):
{json.dumps(train_upgrade[:2], indent=2)}
Pick the best train and class. Consider availability, duration, and
whether the upgrade is worth it for this travel type.
Return ONLY the JSON structure. No other text."""
        
        result = chat_json(prompt= prompt, system= SYSTEM_PROMPT,max_tokens=800)

        if result.get("_parse_error") or not result.get('recommended'):
            print(f" [{self.name}] JSON parse issue - using fallback")
            return self._fallback(trains_defaults, request.passengers, default_class)
        
        return result
    
    def _fallback(
            self,
            trains: list,
            passengers: int,
            cls: str,
    ) -> dict:
        
        available = [t for t in trains if t.get("availability") == "Available"]
        best = (available or trains)[0] if trains else {}
        price = best.get("price_inr", 0)
        return {
            "recommended": best,
            "alternatives" : trains[1:3],
            "best_class": cls,
            "class_note": f"{cls} class recommended for this journey",
            "total_cost": price,
            "per_person_cost": price // max(passengers, 1),
            "booking_tip": "Book 60 days in advance on irctc.co.in for bests availability",
            "irctc_search": best.get("train_name", ''),
        }
    
    def _empty_result(self) -> dict:
        return {
            "recommended":    {},
            "alternatives":   [],
            "best_class":     "3A",
            "class_note":     "No direct trains found for this route",
            "total_cost":     0,
            "per_person_cost":0,
            "booking_tip":    "Check irctc.co.in for connecting trains via major junctions",
            "irctc_search":   "",   
        }
    

# self test
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
 
    print("=" * 55)
    print("  train_agent.py — self test")
    print("=" * 55)
 
    agent = TrainAgent()
 
    tests = [
        TravelRequest(
            destination="Goa", origin="Ahmedabad", budget=30000,
            duration_days=5, travel_type="couple", passengers=2,
            start_date="2025-06-15", preferences=["beach"],
        ),
        TravelRequest(
            destination="Jaipur", origin="Delhi", budget=15000,
            duration_days=3, travel_type="family", passengers=3,
            children=1, start_date="2025-06-20", preferences=["culture"],
        ),
        TravelRequest(
            destination="Goa", origin="Mumbai", budget=50000,
            duration_days=5, travel_type="honeymoon", passengers=2,
            start_date="2025-12-20", preferences=["luxury", "beach"],
        ),
    ]
 
    for req in tests:
        print(f"\n  Trip: {req.origin} → {req.destination} | "
              f"{req.travel_type} | Rs.{req.budget:,}")
        print("  (Calling Gemini...)")
 
        result = agent.run(req)
        rec = result.get("recommended") or {}
 
        if rec:
            avail = rec.get("availability", "Unknown")
            print(f"  Train     : {rec.get('train_name','')} ({rec.get('train_number','')})")
            print(f"  Timings   : {rec.get('depart_time','')[-5:]} → "
                  f"{rec.get('arrive_time','')[-5:]} ({rec.get('duration','')})")
            print(f"  Class     : {result.get('best_class','')} | "
                  f"Availability: {avail}")
            print(f"  Cost      : Rs.{result.get('total_cost',0):,} total | "
                  f"Rs.{result.get('per_person_cost',0):,}/person")
            print(f"  Note      : {result.get('class_note','')}")
            print(f"  Tip       : {result.get('booking_tip','')}")
        else:
            print("  No trains found for this route")
 
    print("\n" + "=" * 55)
    print("  TrainAgent done!")
    print("=" * 55)
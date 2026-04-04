import os
import sys
import json
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from config import TravelRequest
from llm_client import chat_json
from tools.transport_api import search_buses

 
SYSTEM_PROMPT = """You are a specialist intercity bus travel agent for India.
You know all major bus operators, routes, and booking platforms.
 
Your job: given bus options and traveller profile, recommend the best
bus with clear reasoning about operator quality and bus type.
 
BUS TYPE GUIDE:
  Non-AC Seater  — short routes (<4h), budget, not overnight
  Non-AC Sleeper — overnight budget option, basic comfort
  AC Seater/Volvo— 4-8h routes, good comfort, daytime or short overnight
  AC Sleeper     — overnight 8h+ routes, best comfort, separate berths
 
OPERATOR QUALITY (Indian context):
  VRL Travels    — most reliable, wide network, good punctuality
  SRS Travels    — good South/West India coverage
  Neeta Travels  — reliable Gujarat/Rajasthan routes
  GSRTC/MSRTC/KSRTC — state buses, cheapest, less comfortable
  Private Volvo  — best comfort, premium pricing
 
Rules:
- Never recommend Non-AC for journeys over 8 hours
- For families with children: AC Sleeper preferred (more comfortable)
- For honeymoon: AC Sleeper with side-by-side berths
- For budget solo: Non-AC Sleeper is fine for overnight
- Always mention RedBus or AbhiBus for booking
- Check seats_left — flag if less than 5 seats remaining
 
Return ONLY valid JSON:
{
  "recommended": {bus dict},
  "alternatives": [{bus dict}],
  "best_type": "AC Sleeper",
  "type_note": "Why this bus type suits this journey",
  "total_cost": 0,
  "per_person_cost": 0,
  "booking_tip": "Practical booking advice",
  "booking_platform": "redbus.in",
  "departure_advice": "Best departure time for this route"
}"""
 
class BusAgent:
    name = "NusAgent"

    def run(salf, request: TravelRequest) -> dict:
        date = request.start_date or "2025-06-01"
        print(f"Searching buses...")
        raw_buses = search_buses(
            origin      = request.origin,
            destination = request.destination,
            date        = date,
            passengers  = request.passengers,
        )

        if not raw_buses:
            return self._empty_result()
        
        route_duration = raw_buses[0].get("duration",'unknown') if raw_buses else "unknown"

        prompt = f"""Find the best bus for this trip:
 
Route      : {request.origin} → {request.destination}
Date       : {date}
Duration   : approximately {route_duration}
Passengers : {request.passengers} adults{f', {request.children} children' if request.children else ''}
Travel type: {request.travel_type}
Budget     : Rs.{request.budget:,.0f} total
Preferences: {request.pref_str()}
 
{'Family trip — need comfortable seats, avoid overnight if children under 5' if request.is_family() else ''}
{'Honeymoon — prefer AC Sleeper with side berths for privacy' if request.travel_type == 'honeymoon' else ''}
{'Budget conscious — cheaper options acceptable' if 'budget' in request.preferences else ''}
 
Available buses:
{json.dumps(raw_buses, indent=2)}
 
Pick the best bus and type. Consider operator reputation, comfort,
departure timing, and value for money.
Return ONLY the JSON structure. No other text."""
        
        result = chat_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=800)
 
        if result.get("_parse_error") or not result.get("recommended"):
            print(f"  [{self.name}] JSON parse issue — using fallback")
            return self._fallback(raw_buses, request.passengers)
 
        return result

    def _fallback(self, raw_buses: list, passengers: int) -> dict:
        sorted_buses = sorted(
            raw_buses,
            key=lambda b: (-b.get("rating", 0), b.get("price_inr", 9999999))
        )
        best  = sorted_buses[0] if sorted_buses else {}
        price = best.get("price_inr", 0)
 
        return {
            "recommended":     best,
            "alternatives":    sorted_buses[1:3],
            "best_type":       best.get("bus_type", "AC Sleeper"),
            "type_note":       "Best rated operator on this route",
            "total_cost":      price,
            "per_person_cost": price // max(passengers, 1),
            "booking_tip":     "Book on redbus.in — compare prices across operators",
            "booking_platform":"redbus.in",
            "departure_advice":"Evening/night departures save a hotel night",
        }
    
    def _empty_result(self) -> dict:
        return {
            "recommended":     {},
            "alternatives":    [],
            "best_type":       "AC Sleeper",
            "type_note":       "No direct buses found for this route",
            "total_cost":      0,
            "per_person_cost": 0,
            "booking_tip":     "Try redbus.in with nearby pickup/drop points",
            "booking_platform":"redbus.in",
            "departure_advice":"Check connecting routes via major cities",
        }
    
#self test

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
 
    print("=" * 55)
    print("  bus_agent.py — self test")
    print("=" * 55)
 
    agent = BusAgent()
 
    tests = [
        TravelRequest(
            destination="Goa", origin="Ahmedabad", budget=30000,
            duration_days=5, travel_type="couple", passengers=2,
            start_date="2025-06-15", preferences=["beach"],
        ),
        TravelRequest(
            destination="Mumbai", origin="Pune", budget=10000,
            duration_days=2, travel_type="solo", passengers=1,
            start_date="2025-06-20", preferences=[],
        ),
        TravelRequest(
            destination="Goa", origin="Mumbai", budget=50000,
            duration_days=5, travel_type="honeymoon", passengers=2,
            start_date="2025-12-20", preferences=["luxury"],
        ),
    ]
 
    for req in tests:
        print(f"\n  Trip: {req.origin} → {req.destination} | "
              f"{req.travel_type} | Rs.{req.budget:,}")
        print("  (Calling Gemini...)")
 
        result = agent.run(req)
        rec = result.get("recommended") or {}
 
        if rec:
            seats = rec.get("seats_left", 0)
            seats_warn = " Low seats!" if seats < 5 else ""
            print(f"  Operator  : {rec.get('operator','')} | {rec.get('bus_type','')}")
            print(f"  Timings   : {rec.get('depart_time','')[-5:]} → "
                  f"{rec.get('arrive_time','')[-5:]} ({rec.get('duration','')})")
            print(f"  Seats left: {seats}{seats_warn}")
            print(f"  Rating    : {rec.get('rating','')}/5")
            amenities = ", ".join(rec.get("amenities", []))
            print(f"  Amenities : {amenities}")
            print(f"  Cost      : Rs.{result.get('total_cost',0):,} total | "
                  f"Rs.{result.get('per_person_cost',0):,}/person")
            print(f"  Type note : {result.get('type_note','')}")
            print(f"  Book on   : {result.get('booking_platform','')}")
            print(f"  Depart tip: {result.get('departure_advice','')}")
        else:
            print("  No buses found for this route")
 
    print("\n" + "=" * 55)
    print("  BusAgent done!")
    print("=" * 55)
 
import os 
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TravelRequest
from llm_client import chat_json
from tools.hotel_api import search_hotels

SYSTEM_PROMPT ="""You are a sepecialist hotel recommendation agent for indian travellers.
your job: given hotel options and trip context m recommend the single best
hotel and explain why it suits this specific traveller.

Rules:
-match hotel catefory to travel type:
    honeymoon - luxury preferred
    family - mid-range with family amenities
    solo budget - budget or mid
    couple - mif or lixiry depenfing on budget
-Always check if hotel fits within the budget
- Mention the key reason this hotel was chosen 

Return Onlu calid JSON , no markedown m no explaination out side JSON

{
    "recommended": {hotel dict},
    'alternatices': [{hotel dict}],
    "recommendation_reason": "one sentence why this hotel suits this trip",
    "totel_stat_cost": 80000,
    "per_nigh_cost": 2000
}"""

class HotelAgent:
    name = "HotelAgent"
    def run(self, request: TravelRequest)-> dict:
        nights            = request.nights()
        estimated_flights = request.budget * 0.30
        hotel_budget      = (request.budget - estimated_flights) * 0.45
        max_per_night     = hotel_budget / max(nights, 1)

        raw_options = search_hotels(
            destination   = request.destination,
            check_in      = request.start_date or "2025-06-01",
            nights        = nights,
            guests        = request.passengers,
            max_per_night = max_per_night,
            travel_type   = request.travel_type,
            preferences   = request.preferences,
        )
        if not raw_options:
            return self._empty_result()
        
        prompt = f"""Trip details:
- Destination: {request.destination}
- Duration: {nights} nights
- Guests: {request.passengers} adults{f', {request.children} children' if request.children else ''}
- Travel type: {request.travel_type}
- Preferences: {request.pref_str()}
- Hotel budget: ₹{hotel_budget:,.0f} total (₹{max_per_night:,.0f}/night max)
{'- This is a HONEYMOON trip — romantic, premium property preferred' if request.travel_type == 'honeymoon' else ''}
{'- FAMILY trip — need family rooms, kid-friendly amenities' if request.is_family() else ''}
{'- LUXURY preferred' if request.is_luxury() else ''}
 
Available hotels:
{json.dumps(raw_options, indent=2)}
 
Pick the single best hotel for this trip.
Return ONLY the JSON structure specified. No other text."""
        
        result = chat_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=700)
        if result.get("_parse_error") or not result.get("recommended"):
            print(f"[{self.name}] JSON parse issue - using fallback")
            return self._fallback(raw_options, nights)
        return result 
    
    def _fallback(self,raw_options: list, nights: int) -> dict:
        best = raw_options[0]
        return{
            "recommended": best,
            "alternative": raw_options[1:],
            "recommendation_reason":"Best rated option within budget",
            "total_stay_cost":      best.get("total_price", 0),
            "per_night_cost":       best.get("price_per_night", 0),
        }
    def _empty_result(self) -> dict:
        return {
            "recommended":          {},
            "alternatives":         [],
            "recommendation_reason":"No hotels found for this destination",
            "total_stay_cost":      0,
            "per_night_cost":       0,
        }
    
#Self test
if __name__ =="__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("=" * 55)
    print("  hotel_agent.py — self test")
    print("=" * 55)
 
    agent = HotelAgent()
 
    tests = [
        TravelRequest(
            destination="Goa", origin="Ahmedabad",
            budget=30000, duration_days=5,
            travel_type="couple", passengers=2,
            start_date="2025-06-15",
            preferences=["beach"],
        ),
        TravelRequest(
            destination="Dubai", origin="Delhi",
            budget=150000, duration_days=6,
            travel_type="honeymoon", passengers=2,
            start_date="2025-12-20",
            preferences=["luxury"],
        ),
    ]
 
    for req in tests:
        print(f"\n  Trip: {req.destination} | {req.travel_type} | "
              f"₹{req.budget:,} | {req.nights()} nights")
        result = agent.run(req)
 
        rec = result.get("recommended", {})
        if rec:
            stars = "★" * rec.get("stars", 0)
            print(f"  Recommended : {rec.get('name')} {stars}")
            print(f"  Area        : {rec.get('area')}")
            print(f"  Rating      : {rec.get('rating')}/10")
            print(f"  Per night   : ₹{result.get('per_night_cost', 0):,}")
            print(f"  Total stay  : ₹{result.get('total_stay_cost', 0):,}")
            print(f"  Reason      : {result.get('recommendation_reason', '')}")
        else:
            print("  No hotel found")
 
    print("\n" + "=" * 55)
    print("  HotelAgent done. Moving to ItineraryAgent...")
    print("=" * 55)
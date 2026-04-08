import os
import sys
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from config import TravelRequest
from llm_client import chat_json

SYSTEM_PROMPT = """You are a travel budget analyst specialising in Indian travel costs.
 
Your job: given actual flight and hotel costs plus trip details, calculate
the complete budget breakdown and give practical money-saving tips.
 
Be realistic about Indian travel costs:
- Food: ₹300-600/person/day (budget) to ₹800-1500 (mid) to ₹2000+ (luxury)
- Local transport: ₹200-500/day (auto/cab) to ₹800+ (private cab)
- Activities: varies widely by destination
- Shopping/misc: 5-10% buffer is realistic
 
Return ONLY valid JSON, no markdown:
{
  "breakdown": {
    "flights":         {"cost": 0, "percentage": 0},
    "hotel":           {"cost": 0, "percentage": 0},
    "food":            {"cost": 0, "percentage": 0},
    "activities":      {"cost": 0, "percentage": 0},
    "local_transport": {"cost": 0, "percentage": 0},
    "shopping_misc":   {"cost": 0, "percentage": 0}
  },
  "total_cost": 0,
  "total_budget": 0,
  "surplus_or_deficit": 0,
  "status": "within_budget",
  "per_day_spend": 0,
  "per_person_total": 0,
  "optimisation_tips": [
    "Specific actionable tip 1",
    "Specific actionable tip 2",
    "Specific actionable tip 3"
  ],
  "luxury_upgrade_cost": 0
}
 
status must be exactly one of: "within_budget", "over_budget", "tight"
(tight = within budget but less than 5% surplus)"""

class BudgetAgent:
 
    name = "BudgetAgent"
 
    def run(
        self,
        request: TravelRequest,
        flights: dict,
        hotel:   dict,
    ) -> dict:
        """
        Calculate complete trip budget breakdown.
 
        PYTHON CONCEPT — safe dict access with .get() chain:
            flights.get("round_trip_cost") or 0
            The  or 0  handles both:
            - Key missing → .get() returns None → None or 0 → 0
            - Key present but value is None → None or 0 → 0
            - Key present, value is 0 → 0 or 0 → 0
            This is safer than flights["round_trip_cost"] which crashes
            if the key doesn't exist.
 
        COST ESTIMATION LOGIC:
            We know exact costs for flights and hotel (from previous agents).
            For food, activities, transport, shopping — we estimate based on:
            - destination (Goa vs Dubai have different costs)
            - travel_type (luxury vs budget preferences)
            - duration
            Gemini handles these estimates — it knows Goa beach shack prices
            vs Dubai restaurant prices.
        """
 
        # ── Extract known costs from previous agents ──────────────────────────
        flight_cost = flights.get("round_trip_cost") or 0
        hotel_cost  = hotel.get("total_stay_cost")   or 0
        days        = request.duration_days
        pax         = request.passengers
 
        # ── Estimate remaining budget categories ──────────────────────────────
        # These are starting estimates — Gemini refines them
        remaining     = max(request.budget - flight_cost - hotel_cost, 0)
        food_est      = remaining * 0.40
        activity_est  = remaining * 0.30
        transport_est = remaining * 0.20
        misc_est      = remaining * 0.10
 
        prompt = f"""Calculate the complete budget for this trip:
 
Trip: {request.origin} → {request.destination}
Duration: {days} days | Passengers: {pax} adults
Travel type: {request.travel_type}
Preferences: {request.pref_str()}
Total budget: ₹{request.budget:,.0f}
 
CONFIRMED COSTS (from real search results):
- Flights : ₹{flight_cost:,.0f} (round trip, all passengers)
- Hotel   : ₹{hotel_cost:,.0f} ({request.nights()} nights total)
 
ESTIMATED REMAINING COSTS (refine based on destination and travel type):
- Food          : ₹{food_est:,.0f} (₹{food_est/days:,.0f}/day estimate)
- Activities    : ₹{activity_est:,.0f} total
- Local transport: ₹{transport_est:,.0f} total
- Shopping/misc : ₹{misc_est:,.0f} total
 
Adjust estimates realistically for {request.destination} ({request.travel_type} trip).
Provide 3 specific money-saving tips for this exact destination and travel type.
Return ONLY the JSON structure. No other text."""
 
        result = chat_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=900)
 
        if result.get("_parse_error"):
            print(f"  [{self.name}] JSON parse issue - using calculated fallback")
            return self._calculated_fallback(
                request, flight_cost, hotel_cost,
                food_est, activity_est, transport_est, misc_est,
            )
 
        return result
 
    def _calculated_fallback(
        self, request, flight_cost, hotel_cost,
        food_est, activity_est, transport_est, misc_est,
    ) -> dict:
        """
        Pure math fallback — no Gemini needed.
        Used when JSON parsing fails so the system always returns something.
        """
        days  = request.duration_days
        pax   = request.passengers
        total = flight_cost + hotel_cost + food_est + activity_est + transport_est + misc_est
        bgt   = max(request.budget, 1)
        surplus = request.budget - total
 
        if surplus < 0:
            status = "over_budget"
        elif surplus / bgt < 0.05:
            status = "tight"
        else:
            status = "within_budget"
 
        return {
            "breakdown": {
                "flights":         {"cost": int(flight_cost),   "percentage": round(flight_cost/bgt*100)},
                "hotel":           {"cost": int(hotel_cost),    "percentage": round(hotel_cost/bgt*100)},
                "food":            {"cost": round(food_est),    "percentage": round(food_est/bgt*100)},
                "activities":      {"cost": round(activity_est),"percentage": round(activity_est/bgt*100)},
                "local_transport": {"cost": round(transport_est),"percentage":round(transport_est/bgt*100)},
                "shopping_misc":   {"cost": round(misc_est),    "percentage": round(misc_est/bgt*100)},
            },
            "total_cost":         round(total),
            "total_budget":       request.budget,
            "surplus_or_deficit": round(surplus),
            "status":             status,
            "per_day_spend":      round(total / max(days, 1)),
            "per_person_total":   round(total / max(pax, 1)),
            "optimisation_tips":  [
                "Book flights 3-4 weeks in advance for best prices",
                "Eat at local dhabas and street food stalls to save on food",
                "Use public transport or shared autos instead of private cabs",
            ],
            "luxury_upgrade_cost": round(total * 1.6),
        }
 

# Self-test
 
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
 
    print("=" * 55)
    print("  budget_agent.py — self test")
    print("=" * 55)
 
    agent = BudgetAgent()
 
    req = TravelRequest(
        destination   = "Goa",
        origin        = "Ahmedabad",
        budget        = 30000,
        duration_days = 5,
        travel_type   = "couple",
        passengers    = 2,
        start_date    = "2025-06-15",
        preferences   = ["beach", "food"],
    )
 
    # Simulate results from FlightAgent and HotelAgent
    mock_flights = {"round_trip_cost": 10226}
    mock_hotel   = {"total_stay_cost": 22808}
 
    print(f"\n  Trip: {req.destination} | ₹{req.budget:,} budget")
    print(f"  Flight cost: ₹{mock_flights['round_trip_cost']:,}")
    print(f"  Hotel cost : ₹{mock_hotel['total_stay_cost']:,}")
    print("  (Calling Gemini for breakdown...)\n")
 
    result = agent.run(req, mock_flights, mock_hotel)
 
    print(f"  {'Category':<18} {'Cost':>10}  {'%':>5}")
    print(f"  {'-'*36}")
    breakdown = result.get("breakdown", {})
    for category, data in breakdown.items():
        print(f"  {category:<18} ₹{data.get('cost',0):>8,}  {data.get('percentage',0):>4}%")
 
    print(f"  {'-'*36}")
    print(f"  {'TOTAL':<18} ₹{result.get('total_cost',0):>8,}")
    print(f"  {'Budget':<18} ₹{result.get('total_budget',0):>8,}")
    surplus = result.get('surplus_or_deficit', 0)
    sign = "+" if surplus >= 0 else ""
    print(f"  {'Surplus/Deficit':<18} {sign}₹{surplus:>7,}")
    print(f"\n  Status       : {result.get('status','').upper()}")
    print(f"  Per day spend: ₹{result.get('per_day_spend',0):,}")
    print(f"  Per person   : ₹{result.get('per_person_total',0):,}")
 
    tips = result.get("optimisation_tips", [])
    if tips:
        print(f"\n  Money-saving tips:")
        for tip in tips:
            print(f"    • {tip}")
 
    print("\n" + "=" * 55)
    print("  BudgetAgent done. Moving to ContextAgent...")
    print("=" * 55)
 
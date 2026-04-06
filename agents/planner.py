import os 
import sys 
import json
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TravelRequest, DEFAULT_CURRENCY
from llm_client import orchestrator_json
from memory.Session_store import SessionStore

#import all 5 specialist agent 
from agents.fllight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.itinerary_agent import ItineraryAgent
from agents.train_agent import TrainAgent
from agents.bus_agent import BusAgent
from agents.budget_agent import BudgetAgent
from agents.context_agent import ContextAgent
from agents.journey_agent import JourneyAgent


# parse prompt
PARSE_SYSTEM = """You are a travel request parser for Indian travellers.
Extract structured trip parameters from natural language requests.
Return ONLY valid JSON — no markdown, no explanation, no extra text."""

PARSE_PROMPT =  """Parse this travel request into structured JSON.
 
Request: "{query}"
 
Return ONLY this JSON (fill all fields, use defaults if not mentioned):
{{
  "destination": "",
  "origin": "Delhi",
  "budget": 30000,
  "currency": "INR",
  "duration_days": 5,
  "start_date": "{default_date}",
  "end_date": "",
  "travel_type": "couple",
  "preferences": [],
  "passengers": 2,
  "children": 0
}}
 
Rules:
- destination : extract city/place name (required)
- origin      : infer from context, default "Delhi" if unclear
- budget      : extract number. "30k"=30000, "3 lakh"=300000, "₹30,000"=30000, "$500"=41500
- duration_days: "5 days"=5, "a week"=7, "10 days"=10, "weekend"=2, "fortnight"=14
- start_date  : use {default_date} if not mentioned
- travel_type : detect from text — solo|couple|family|honeymoon|group
                "me and my wife"=couple, "with kids"=family, "alone"=solo
- preferences : list from [adventure, luxury, food, culture, beach, nature, shopping, spiritual]
                infer from context words
- passengers  : number of adults (default 2 for couple, 1 for solo)
- children    : number of children (0 if not mentioned)"""

# planner agent
class PlannerAgent:
    def __init__(self):
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.itinerary_agent = ItineraryAgent()
        self.train_agent = TrainAgent()
        self.bus_agent = BusAgent()
        self.budget_agent = BudgetAgent()
        self.context_agent = ContextAgent()
        self.journey_agent   = JourneyAgent()

    # public method 1 - plan()
    def plan(self, user_query: str, session_id: str | None = None) -> dict:
        print(f"\n{'='*50}")
        print(f"[Planner] Parsing: {user_query[:60]}...")
        request = self._parse_request(user_query)
        print(f"[Planner] Parsed  : {request.travel_type} trip | "
                f"{request.origin} → {request.destination} | "
                f"{request.duration_days}d | ₹{request.budget:,.0f}")

        #step 2 : marge saved preferences from session 
        if session_id:
            SessionStore.add_message(session_id, "user", user_query)
            saved_prefs =  SessionStore.get_preferences(session_id)

            if saved_prefs.get('home_city') and request.origin == "Delhi":
                request.origin = saved_prefs["home_city"]
                print(f"[Planner] Using saved home city : {request.origin}")


        #Step 3: Run agents in order
        print(f"\n[Planner] Running agents..")
            
        
        print(f"  [1/8] FlightAgent...")
        flights = self.flight_agent.run(request)
        print(f" → ₹{(flights.get('round_trip_cost') or 0):,} | "
            f"{flights.get('recommended', {}).get('airline', 'N/A')}")
        
        print(f"  [2/8] TrainAgent...")
        trains = self.train_agent.run(request)
        rec_train = trains.get("recommended") or {}
        print(f"        → {rec_train.get('train_name','N/A')} | "
              f"Rs.{trains.get('total_cost',0):,} | "
              f"Class: {trains.get('best_class','N/A')}")
        
        print(f"  [3/8] BusAgent...")
        buses = self.bus_agent.run(request)
        rec_bus = buses.get("recommended") or {}
        print(f"        → {rec_bus.get('operator','N/A')} | "
              f"Rs.{buses.get('total_cost',0):,} | "
              f"{buses.get('best_type','N/A')}")

        print(f"  [4/8] HotelAgent...")
        hotel = self.hotel_agent.run(request)
        rec_hotel = hotel.get('recommended', {})
        print(f"        → ₹{(hotel.get('per_night_cost') or 0):,}/night | "
                f"{rec_hotel.get('name', 'N/A')}")

        print(f"  [5/8] ContextAgent...")
        context = self.context_agent.run(request)
        print(f"        → Season: {context.get('season', 'N/A')} | "
                f"{context.get('condition', 'N/A')}")

        print(f"  [6/8] ItineraryAgent...")
        itinerary = self.itinerary_agent.run(request, hotel, flights)
        days_count = len(itinerary.get('days', []))
        print(f"        → {days_count} days generated")
        
        print(f"  [7/8] JourneyAgent (every leg + sightseeing)...")
        journey = self.journey_agent.run(request, flights, hotel, itinerary)
        legs_count = len(journey.get('legs', []))
        print(f"        → {legs_count} journey legs planned")

        print(f"  [8/8] BudgetAgent...")
        budget = self.budget_agent.run(request, flights, hotel)
        print(f"        → Total: ₹{(budget.get('total_cost') or 0):,} | "
                f"Status: {budget.get('status', 'N/A')}")
        
        # Step 4: Merge all results into final plan

        plan = self._merge_plan(
            request, flights, hotel, itinerary, budget, context, trains, buses, journey
        )

        # step 5: Save to session memory
        if session_id:
            version_id = SessionStore.save_plan(session_id, request, plan)
            plan['version_id'] = version_id

            SessionStore.update_preferences(session_id, {
                "home_city": request.origin,
                'last_destination': request.destination,
            })
            SessionStore.add_message(
                session_id, "assistant",
                f"Plan ready: {plan['trip_title']} — ₹{(budget.get('total_cost') or 0):,}"
            )
            print(f"\n[Planner] saved as version {version_id}")
        
        print(f"[Planner] Done! Plan: {plan['trip_title']}")
        return plan
    
    #public method 2 - replan()
    def replan(self, session_id: str, change_request: str) -> dict:
        prev_request = SessionStore.get_latest_request(session_id)
        if not prev_request:
            raise ValueError("no esisting plan found. start a new trip first"
            )
    
        combined_query = (
            f"Update this trip: {change_request}. "
            f"Keep everything else the same. "
            f"Original trip: {prev_request.get('duration_days')} days to "
            f"{prev_request.get('destination')} from "
            f"{prev_request.get('origin')}, "
            f"budget ₹{prev_request.get('budget', 0):,.0f}, "
            f"travel type: {prev_request.get('travel_type')}, "
            f"preferences: {', '.join(prev_request.get('preferences', []))}"           
        )

        print(f"\n[Planner] Re-planning with change: {change_request}")

        return self.plan(combined_query, session_id)
    
    # PUBLIC METHOD 3 — compare_plans()
 
 
    def compare_plans(self, session_id: str) -> dict:
        """
        Return all saved plan versions for side-by-side comparison.
        Used by the Streamlit UI's "Compare Plans" tab.
        """
        versions = SessionStore.get_plan_versions(session_id)
        return {
            "session_id": session_id,
            "count":      len(versions),
            "plans": [
                {
                    "version_id":  v.version_id,
                    "label":       v.label,
                    "destination": v.request.get("destination"),
                    "duration":    v.request.get("duration_days"),
                    "budget":      v.request.get("budget"),
                    "total_cost":  v.total_cost,
                    "created_at":  v.created_at,
                }
                for v in versions
            ]
        }
    #private helper


    def _parse_request(self, query: str) -> TravelRequest:
      
        default_date = (date.today() + timedelta(days=14)).isoformat()
 
        prompt = PARSE_PROMPT.format(
            query        = query,
            default_date = default_date,
        )
 
        data = orchestrator_json(
            prompt     = prompt,
            system     = PARSE_SYSTEM,
            max_tokens = 512,
        )
 
        # If parsing completely failed, use a safe fallback
        if data.get("_parse_error") or not data.get("destination"):
            print(f"[Planner] Parse failed — using fallback defaults")
            data = {
                "destination":  "Goa",
                "origin":       "Delhi",
                "budget":       30000,
                "currency":     "INR",
                "duration_days":5,
                "start_date":   default_date,
                "end_date":     "",
                "travel_type":  "couple",
                "preferences":  [],
                "passengers":   2,
                "children":     0,
            }
 
        # Calculate end_date if not provided
        if data.get("start_date") and not data.get("end_date"):
            try:
                start    = date.fromisoformat(data["start_date"])
                end      = start + timedelta(days=int(data.get("duration_days", 5)))
                data["end_date"] = end.isoformat()
            except (ValueError, TypeError):
                data["end_date"] = ""
 
        # Build TravelRequest — use .get() with defaults for every field
        # so missing fields never cause a KeyError
        return TravelRequest(
            destination   = str(data.get("destination",   "Goa")),
            origin        = str(data.get("origin",        "Delhi")),
            budget        = float(data.get("budget",      30000)),
            currency      = str(data.get("currency",      DEFAULT_CURRENCY)),
            start_date    = str(data.get("start_date",    default_date)),
            end_date      = str(data.get("end_date",      "")),
            duration_days = int(data.get("duration_days", 5)),
            travel_type   = str(data.get("travel_type",   "couple")),
            preferences   = list(data.get("preferences",  [])),
            passengers    = int(data.get("passengers",    2)),
            children      = int(data.get("children",      0)),
            raw_query     = query,
        )
 
    def _merge_plan(
        self,
        request:   TravelRequest,
        flights:   dict,
        hotel:     dict,
        itinerary: dict,
        budget:    dict,
        context:   dict,
        trains:    dict = None,
        buses:     dict = None,
        journey:   dict = None,
    ) -> dict:
        
        # Extract top tips from context for the summary section
        tips = []
        safety  = context.get("safety_tips",  [])
        packing = context.get("packing_tips",  [])
        if safety:  tips.extend(safety[:2])
        if packing: tips.extend(packing[:2])
 
        return {

            "trip_title":  (f"{request.destination} "
                            f"{request.duration_days}-Day "
                            f"{request.travel_type.title()} Trip"),
            "destination": request.destination,
            "origin":      request.origin,
            "duration":    f"{request.duration_days} Days / {request.nights()} Nights",
            "travel_type": request.travel_type,
            "dates":       f"{request.start_date} → {request.end_date}",
            "passengers":  request.passengers,
            "children":    request.children,
            "preferences": request.preferences,
 

            "flights":     flights,
            "trains":      trains or {},
            "buses":       buses or {},
            "journey":   journey or {},
            "hotel":       hotel,
            "itinerary":   itinerary,
            "budget":      budget,
            "context":     context,

            "tips":        tips,
            "raw_query":   request.raw_query,
        }
 
 

# PART C — Self-test (full end-to-end pipeline)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
 
    print("=" * 55)
    print("  planner.py — FULL END-TO-END TEST")
    print("  This runs all 5 agents + Gemini calls")
    print("  Estimated time: 20-40 seconds")
    print("=" * 55)
 
    planner    = PlannerAgent()
    session_id = SessionStore.create()
    print(f"\n  Session ID: {session_id[:8]}...")
 
    # ── Test 1: Full plan from natural language ───────────────────────────────
    print("\n" + "-"*50)
    print("  TEST 1: Natural language → full plan")
    print("-"*50)
 
    plan = planner.plan(
        "Plan a 5 day trip to Goa from Ahmedabad under 30000 for couple, "
        "we love beach and local food",
        session_id,
    )
 
    print(f"\n  Plan generated: {plan['trip_title']}")
    print(f"  Dates     : {plan['dates']}")
    print(f"  Duration  : {plan['duration']}")
 
    # Flights summary
    rec_f = plan["flights"].get("recommended", {})
    if rec_f:
        print(f"\n  Flight    : {rec_f.get('airline')} {rec_f.get('flight_number')}")
        print(f"  Departs   : {rec_f.get('depart_time')}")
        print(f"  Cost      : ₹{plan['flights'].get('round_trip_cost', 0):,}")
 
    # Hotel summary
    rec_h = plan["hotel"].get("recommended", {})
    if rec_h:
        stars = "★" * rec_h.get("stars", 0)
        print(f"\n  Hotel     : {rec_h.get('name')} {stars}")
        print(f"  Area      : {rec_h.get('area')}")
        print(f"  Per night : ₹{plan['hotel'].get('per_night_cost', 0):,}")
 
    # Itinerary summary
    days = plan["itinerary"].get("days", [])
    if days:
        print(f"\n  Itinerary : {len(days)} days generated")
        print(f"  Day 1     : {days[0].get('title', '')}")
        if len(days) > 1:
            print(f"  Day 2     : {days[1].get('title', '')}")
 
    # Budget summary
    bgt = plan["budget"]
    print(f"\n  Budget    : ₹{bgt.get('total_cost', 0):,} / ₹{bgt.get('total_budget', 0):,}")
    surplus = bgt.get('surplus_or_deficit', 0)
    sign = "+" if surplus >= 0 else ""
    print(f"  Surplus   : {sign}₹{surplus:,}")
    print(f"  Status    : {bgt.get('status', '').upper()}")
 
    # Context
    ctx = plan["context"]
    print(f"\n  Season    : {ctx.get('season', '').title()}")
    print(f"  Weather   : {ctx.get('temperature', '')} — {ctx.get('condition', '')}")
 
    # ── Test 2: Re-planning ───────────────────────────────────────────────────
    print("\n" + "-"*50)
    print("  TEST 2: Re-plan with change (reduce budget)")
    print("-"*50)
 
    updated = planner.replan(session_id, "reduce budget to ₹20,000")
    print(f"\n   Re-planned: {updated['trip_title']}")
    new_bgt = updated["budget"]
    print(f"  New total : ₹{new_bgt.get('total_cost', 0):,}")
    print(f"  Status    : {new_bgt.get('status', '').upper()}")
 
    # ── Test 3: Compare plan versions ────────────────────────────────────────
    print("\n" + "-"*50)
    print("  TEST 3: Compare plan versions")
    print("-"*50)
 
    comparison = planner.compare_plans(session_id)
    print(f"\n  Found {comparison['count']} plan versions:")
    for p in comparison["plans"]:
        print(f"    {p['version_id']}  {p['label']:12s}  "
              f"Budget: ₹{p['budget']:,.0f}  "
              f"Cost: ₹{p['total_cost']:,.0f}")
 
    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  Part 5 complete!")
    print()
    print("  You now have a working end-to-end pipeline:")
    print("  User query → PlannerAgent → 5 Agents → Full Plan")
    print()
    print("  Next → Part 6: FastAPI backend (REST API)")
    print("  Say 'Part 6' to continue.")
    print("=" * 55)
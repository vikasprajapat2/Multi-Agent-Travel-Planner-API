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
from agents.budget_agent import BudgetAgent
from agents.contex_agent import ContextAgent

# parse prompt
PARSE_PROMPT = """You are a travel request parser for Indian travellers.
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
        self.itinerary_agent = BudgetAgent()
        self.budget_agent = BudgetAgent()
        self.context_agent = ContextAgent()

        # public method 1 - plan()
        def plan(self, user_query: str, session_id: str | None = None) -> dict:
            print(f"\n{'='*50}")
            request = self._parse_request(user_query)
            request =  self._parse_request(user_query)
            print(f"[Planner] Parsed  : {request.travel_type} trip | "
                  f"{request.origin} → {request.destination} | "
                  f"{request.duration_days}d | ₹{request.budget:,.0f}")
            
        # Step 1: Parse natural language → TravelRequest
        rint(f"\n{'='*50}")
        print(f"[Planner] Parsing: {user_query[:60]}...")
        request = self._parse_request(user_query)
        print(f"[Planner] Parsed  : {request.travel_type} trip | "
              f"{request.origin} → {request.destination} | "
              f"{request.duration_days}d | ₹{request.budget:,.0f}")

        #step 2 : marge saved preferences from session 
        if session_id:
            SessionStore.add_massage(session_id, "user", user_query)
            saved_prefs =  SessionStore.get_preferences(session_id)

            if saved_prefs.get('home_city') and request.origin == "Delhi":
                request.origin = saved_prefs["home_city"]
                print(f"[Planner] Using saved home city : {request.origin}")


        #Step 3: Run agents in order
        print(f"\n[Planner] Running agents..")
         
        
        print(f"  [1/5] FlightAgent...")
        flights = self.flight_agent.run(request)
        print(f"        → ₹{flights.get('round_trip_cost', 0):,} | "
              f"{flights.get('recommended', {}).get('airline', 'N/A')}")
 
        print(f"  [2/5] HotelAgent...")
        hotel = self.hotel_agent.run(request)
        rec_hotel = hotel.get('recommended', {})
        print(f"        → ₹{hotel.get('per_night_cost', 0):,}/night | "
              f"{rec_hotel.get('name', 'N/A')}")
 
        print(f"  [3/5] ContextAgent...")
        context = self.context_agent.run(request)
        print(f"        → Season: {context.get('season', 'N/A')} | "
              f"{context.get('condition', 'N/A')}")
 
        print(f"  [4/5] ItineraryAgent...")
        itinerary = self.itinerary_agent.run(request, hotel, flights)
        days_count = len(itinerary.get('days', []))
        print(f"        → {days_count} days generated")
 
        print(f"  [5/5] BudgetAgent...")
        budget = self.budget_agent.run(request, flights, hotel)
        print(f"        → Total: ₹{budget.get('total_cost', 0):,} | "
              f"Status: {budget.get('status', 'N/A')}")
        
        # Step 4: Merge all results into final plan

        plan = self._merge_plan(
            request, flights, hotel, itinerary, budget, context
        )

        # step 5: Save to session memory
        if session_id:
            version_id = SessionStore.save_plan(session_id, request, plan)
            plan['version_id'] = version_id


            SessionStore.update_preferences(session_id, request, plan)
            plan['version_id'] = version_id

            SessionStore.update_preferences(session_id, {
                "home_city": request.orign,
                'last_destination': request.destination,
            })
            SessionStore.add_message(
                session_id, "assistant",
                f"Plan ready: {plan['trip_title']} — ₹{budget.get('total_cost',0):,}"
            )
            print(f"\n[Planner] saved as version {version_id}")
        
        print(f"[Planner] Done! Plan: {plan['trip_title']}")
        return plan
    
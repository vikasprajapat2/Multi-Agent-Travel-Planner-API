
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TravelRequest
from llm_client import chat_json
from tools.weather_api import get_weather_context


SYSTEM_PROMPT = """You are a local travel expert with deep knowledge of destinations
popular with Indian travellers — both domestic and international.

Your job: enrich the base weather and safety context with practical local
insights tailored to the specific traveller type.

Add genuinely useful, specific information — not generic travel advice.
Think: "what would a well-travelled friend who lives there tell you?"

Return ONLY valid JSON. Keep the same structure as the input and ADD:
{
  ...all existing fields from input...,
  "local_dishes": [
    {
      "dish": "Fish Curry Rice",
      "where": "Any local beach shack",
      "price_range": "₹150-300/plate",
      "must_try": true
    }
  ],
  "etiquette": [
    "Specific cultural tip 1 for this destination",
    "Specific cultural tip 2"
  ],
  "insider_tip": "One specific money-saving or experience tip a local would share",
  "best_areas_to_stay": ["Area 1", "Area 2"],
  "avoid": ["What to avoid at this destination"]
}"""


class ContextAgent:

    name = "ContextAgent"

    def run(self, request: TravelRequest) -> dict:
        """
        Get weather context and enrich it with Gemini's local knowledge.

        WHY COMBINE TOOL + LLM?
            The weather tool gives reliable season/safety data from our
            curated tables. Gemini then adds the "living knowledge" —
            restaurant names, cultural nuances, insider tips — that no
            static table can capture. Best of both approaches.
        """

     
        base_context = get_weather_context(
            destination = request.destination,
            travel_date = request.start_date or "",
        )
        prompt = f"""Enrich this travel context for {request.destination}.

Traveller profile:
- Travel type  : {request.travel_type}
- Interests    : {request.pref_str()}
- Duration     : {request.duration_days} days
- Group size   : {request.passengers} adults{f', {request.children} children' if request.children else ''}
- Budget level : {'luxury' if request.is_luxury() else 'mid-range'}

Base context (keep all these fields in your response):
{json.dumps(base_context, indent=2)}

Add local_dishes (3-4 must-try with specific prices), etiquette (2-3 tips),
insider_tip (one genuinely useful local secret), best_areas_to_stay,
and avoid (2-3 honest things to skip or be careful about).

Tailor everything to the traveller profile above.
Return ONLY the complete JSON. No other text."""

        result = chat_json(
            prompt     = prompt,
            system     = SYSTEM_PROMPT,
            max_tokens = 1000,
        )

        if result.get("_parse_error"):
            print(f"  [{self.name}] JSON parse issue — returning base context")
            # Return base context — still useful even without enrichment
            return base_context

        return result


# Self-test

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("=" * 55)
    print("  context_agent.py — self test")
    print("=" * 55)

    agent = ContextAgent()

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
            budget=25000, duration_days=6,
            travel_type="solo", passengers=1,
            start_date="2025-05-10",
            preferences=["adventure", "nature"],
        ),
    ]

    for req in tests:
        print(f"\n  Trip: {req.destination} | {req.travel_type} | "
              f"{req.start_date} | Prefs: {req.pref_str()}")
        print("  (Calling Gemini for enriched context...)\n")

        result = agent.run(req)

        print(f"  Season    : {result.get('season','').title()}")
        print(f"  Temp      : {result.get('temperature','')}")
        print(f"  Condition : {result.get('condition','')}")
        print(f"  Advice    : {result.get('travel_advice','')}")

        dishes = result.get("local_dishes", [])
        if dishes:
            print(f"\n  Must-try food:")
            for d in dishes:
                if isinstance(d, dict):
                    print(f"    • {d.get('dish','')} at {d.get('where','')} "
                          f"({d.get('price_range','')})")
                else:
                    print(f"    • {d}")

        etiquette = result.get("etiquette", [])
        if etiquette:
            print(f"\n  Etiquette tips:")
            for tip in etiquette:
                print(f"    • {tip}")

        insider = result.get("insider_tip", "")
        if insider:
            print(f"\n  Insider tip: {insider}")

        safety = result.get("safety_tips", [])
        if safety:
            print(f"\n  Safety: {safety[0]}")

    print("\n" + "=" * 55)
    print("  ContextAgent done!")
    print("  All 5 agents complete — ready for Part 5 (Planner).")
    print("=" * 55)
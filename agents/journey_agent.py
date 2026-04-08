import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
from config import TravelRequest
from llm_client import chat_json

_CITY_AIRPORTS = {
    "ahmedaba" : {
       "airport_name": "Sardar Vallabhbhai Patel International Airport (AMD)",
        "distance_from_centre_km": 10,
        "transport_options": [
            {"mode": "Ola/Uber", "duration": "25-35 min", "cost_inr": 200, "tip": "Book in advance during peak hours"},
            {"mode": "Auto-rickshaw", "duration": "35-45 min", "cost_inr": 120, "tip": "Negotiate fixed fare before getting in"},
            {"mode": "AMTS Bus", "duration": "50-60 min", "cost_inr": 20, "tip": "Cheapest but slower, avoid with heavy luggage"},
        ],
        "recommended": "Ola/Uber",
    },
    "delhi": {
        "airport_name": "Indira Gandhi International Airport (DEL)",
        "distance_from_centre_km": 16,
        "transport_options": [
            {"mode": "Airport Express Metro", "duration": "20 min", "cost_inr": 60, "tip": "Fastest, runs every 10 min from New Delhi station"},
            {"mode": "Ola/Uber", "duration": "30-50 min", "cost_inr": 350, "tip": "Traffic heavy during 8-10am and 5-8pm"},
            {"mode": "Prepaid Taxi (DIAL)", "duration": "30-50 min", "cost_inr": 400, "tip": "Fixed rate from official counter — no bargaining needed"},
        ],
        "recommended": "Airport Express Metro",
    },
    "mumbai": {
        "airport_name": "Chhatrapati Shivaji Maharaj International Airport (BOM)",
        "distance_from_centre_km": 28,
        "transport_options": [
            {"mode": "Ola/Uber", "duration": "40-70 min", "cost_inr": 400, "tip": "Book 30 min before — Mumbai traffic is heavy"},
            {"mode": "Local Train + Auto", "duration": "50-70 min", "cost_inr": 80, "tip": "Andheri station nearest — then auto to T2"},
            {"mode": "BEST Bus", "duration": "60-90 min", "cost_inr": 30, "tip": "Very cheap but avoid with bags in rush hour"},
        ],
        "recommended": "Ola/Uber",
    },
    "bangalore": {
        "airport_name": "Kempegowda International Airport (BLR)",
        "distance_from_centre_km": 40,
        "transport_options": [
            {"mode": "KIAS Volvo Bus", "duration": "60-90 min", "cost_inr": 300, "tip": "AC Volvo, runs frequently from MG Road/Shivajinagar"},
            {"mode": "Ola/Uber", "duration": "60-90 min", "cost_inr": 700, "tip": "Very expensive — traffic on NICE road can add 30 min"},
            {"mode": "Prepaid Taxi", "duration": "60-90 min", "cost_inr": 800, "tip": "Available at airport exit — fixed rate"},
        ],
        "recommended": "KIAS Volvo Bus",
    },
    "chennai": {
        "airport_name": "Chennai International Airport (MAA)",
        "distance_from_centre_km": 16,
        "transport_options": [
            {"mode": "Chennai Metro (Blue Line)", "duration": "40 min", "cost_inr": 50, "tip": "Direct metro from airport — most reliable"},
            {"mode": "Ola/Uber", "duration": "30-50 min", "cost_inr": 280, "tip": "Check app for surge during peak hours"},
            {"mode": "Prepaid Taxi (CMRL)", "duration": "35-55 min", "cost_inr": 320, "tip": "Available at exit — AC vehicles, fixed rate"},
        ],
        "recommended": "Chennai Metro",
    },
    "hyderabad": {
        "airport_name": "Rajiv Gandhi International Airport (HYD)",
        "distance_from_centre_km": 22,
        "transport_options": [
            {"mode": "TSRTC Pushpak Bus", "duration": "60-90 min", "cost_inr": 200, "tip": "AC bus, very reliable, stops at key points"},
            {"mode": "Ola/Uber", "duration": "40-60 min", "cost_inr": 450, "tip": "ORR (Outer Ring Road) makes it faster"},
            {"mode": "Prepaid Cab", "duration": "40-60 min", "cost_inr": 500, "tip": "Fixed rate — no surprises"},
        ],
        "recommended": "TSRTC Pushpak Bus",
    },
    "goa": {
        "airport_name": "Goa International Airport / Manohar Airport (GOI)",
        "distance_from_centre_km": 30,
        "transport_options": [
            {"mode": "Prepaid Taxi (Goa Taxi)", "duration": "40-60 min", "cost_inr": 700, "tip": "Fixed rate from counter inside arrival hall"},
            {"mode": "Ola/Uber", "duration": "40-60 min", "cost_inr": 500, "tip": "Cheaper than prepaid taxi but availability varies"},
            {"mode": "Motorcycle Taxi (Pilot)", "duration": "45 min", "cost_inr": 300, "tip": "Budget option but not safe with luggage"},
        ],
        "recommended": "Prepaid Taxi",
    },
    "jaipur": {
        "airport_name": "Jaipur International Airport (JAI)",
        "distance_from_centre_km": 13,
        "transport_options": [
            {"mode": "Ola/Uber", "duration": "25-35 min", "cost_inr": 200, "tip": "Most reliable option in Jaipur"},
            {"mode": "Auto-rickshaw", "duration": "30-40 min", "cost_inr": 120, "tip": "Negotiate fixed fare — no meter in Jaipur autos"},
            {"mode": "Prepaid Taxi", "duration": "25-35 min", "cost_inr": 250, "tip": "Available at airport exit"},
        ],
        "recommended": "Ola/Uber",
    },
    "kolkata": {
        "airport_name": "Netaji Subhas Chandra Bose International Airport (CCU)",
        "distance_from_centre_km": 17,
        "transport_options": [
            {"mode": "Kolkata Metro (Airport line)", "duration": "40 min", "cost_inr": 30, "tip": "Cheapest and avoids traffic"},
            {"mode": "Ola/Uber", "duration": "35-60 min", "cost_inr": 300, "tip": "VIP Road can be congested"},
            {"mode": "AC Bus (WBTC)", "duration": "50-70 min", "cost_inr": 60, "tip": "Good value, runs to Esplanade"},
        ],
        "recommended": "Kolkata Metro",
    },
    "kochi": {
        "airport_name": "Cochin International Airport (COK)",
        "distance_from_centre_km": 30,
        "transport_options": [
            {"mode": "Kerala KSRTC Bus", "duration": "50-70 min", "cost_inr": 80, "tip": "Runs to Ernakulam — cheap and reliable"},
            {"mode": "Ola/Uber", "duration": "40-60 min", "cost_inr": 450, "tip": "Best option for direct hotel drop"},
            {"mode": "Prepaid Taxi", "duration": "40-60 min", "cost_inr": 500, "tip": "Available at exit — AC vehicles"},
        ],
        "recommended": "Kerala KSRTC Bus",
    },
    # Generic fallback for unlisted cities
    "default": {
        "airport_name": "City Airport",
        "distance_from_centre_km": 15,
        "transport_options": [
            {"mode": "Ola/Uber", "duration": "30-45 min", "cost_inr": 300, "tip": "Most reliable option"},
            {"mode": "Prepaid Taxi", "duration": "30-45 min", "cost_inr": 350, "tip": "Available at airport exit"},
            {"mode": "Local Bus", "duration": "50-70 min", "cost_inr": 40, "tip": "Cheapest but slow with luggage"},
        ],
        "recommended": "Ola/Uber",
    },
}
 
# Local sightseeing transport by destination type
_LOCAL_TRANSPORT = {
    "goa": {
        "primary": "Rental scooter (Rs.300-400/day)",
        "secondary": "Ola/Uber or local taxis",
        "tip": "Renting a scooter is the best way to explore Goa freely",
        "daily_budget_inr": 400,
    },
    "jaipur": {
        "primary": "Auto-rickshaw or Ola/Uber",
        "secondary": "Tuk-tuk for short distances",
        "tip": "Hire an auto for the full day (Rs.600-800) for Pink City sightseeing",
        "daily_budget_inr": 700,
    },
    "delhi": {
        "primary": "Delhi Metro (best for tourist spots)",
        "secondary": "Ola/Uber for off-metro locations",
        "tip": "Buy a Tourist Card (Rs.250 for 3 days) for unlimited metro rides",
        "daily_budget_inr": 300,
    },
    "mumbai": {
        "primary": "Local train + auto-rickshaw",
        "secondary": "BEST Bus or Ola/Uber",
        "tip": "Local train is fastest; buy a day pass for unlimited rides",
        "daily_budget_inr": 200,
    },
    "manali": {
        "primary": "Local taxi (shared or private)",
        "secondary": "Walk in Old Manali and Mall Road",
        "tip": "Shared taxis to Solang Valley / Rohtang are cheapest (Rs.200-300/person)",
        "daily_budget_inr": 600,
    },
    "kerala": {
        "primary": "Local bus or ferry (backwaters)",
        "secondary": "Ola/Uber or auto",
        "tip": "Kerala Water Metro (Kochi) is scenic and cheap — Rs.20-40/trip",
        "daily_budget_inr": 300,
    },
    "default": {
        "primary": "Ola/Uber or local auto-rickshaw",
        "secondary": "Local bus for budget",
        "tip": "Ask hotel reception for trusted local auto drivers — often best deal",
        "daily_budget_inr": 500,
    },
}

# system prompt
SYSTEM_PROMPT="""You are a complete journey planning expert for indian travallers.
You plane Every leg of the Journey - not just the main transport , but every 
step from home to each attraction and back.

You Know :
- Which metro lines go to which airport in each indian city.
- Realistic auto/cab fars in each city.
- Which sightseeing spots are walkable from each other 
- Local transport tricks (shared jeeps in hills, ferries in kerala, etc.)
- Entry fees for 2025 for all major Indian tourist sports
- Best time of day to visit each attraction (to avod crowds/heat)

Return ONLY valid JSON:
{
  "legs": [
    {
      "leg_number": 1,
      "leg_name": "Home to Origin Airport",
      "from": "City name",
      "to": "Airport name",
      "options": [
        {
          "mode": "Transport mode",
          "duration": "30 min",
          "cost_inr": 250,
          "tip": "Practical tip"
        }
      ],
      "recommended": "Best mode name",
      "note": "Why this is recommended"
    }
  ],
  "sightseeing": [
    {
      "day": 1,
      "places": [
        {
          "name": "Place name",
          "from_previous": "Hotel or previous place",
          "transport": "Auto/Metro/Walk",
          "distance_km": 3,
          "travel_time": "15 min",
          "travel_cost_inr": 50,
          "entry_fee_inr": 0,
          "time_to_spend": "2 hours",
          "best_time": "Morning 8-10am",
          "tip": "Practical visitor tip"
        }
      ],
      "daily_transport_cost": 500,
      "daily_entry_fees": 200
    }
  ],
  "total_local_transport_cost": 2000,
  "total_entry_fees": 500,
  "transport_tips": [
    "Specific tip 1",
    "Specific tip 2"
  ]
}"""


# JourneyAgent Class
class JourneyAgent:
    name = "JourneyAgent"
    def run(
        self, 
        request: TravelRequest,
        flights: dict,
        hotel: dict,
        itinerary: dict,
        trains: dict = None,
        buses: dict = None,
    ) -> dict:

        origin_key  = request.origin.lower().split(",")[0].strip()
        dest_key    = request.destination.lower().split(",")[0].strip()
 
        origin_airport = _CITY_AIRPORTS.get(origin_key, _CITY_AIRPORTS["default"])
        dest_airport   = _CITY_AIRPORTS.get(dest_key,   _CITY_AIRPORTS["default"])
        local_transport= _LOCAL_TRANSPORT.get(dest_key, _LOCAL_TRANSPORT["default"])

        rec_flight   = flights.get("recommended") or {}
        rec_train    = (trains or {}).get("recommended") or {}
        rec_bus      = (buses or {}).get("recommended") or {}
        hotel_name   = (hotel.get("recommended") or {}).get("name", "Hotel")
        hotel_area   = (hotel.get("recommended") or {}).get("area", dest_key)

        days = itinerary.get("days", [])
        places_by_day = []
        for day in days:
            day_places = []
            for item in day.get("schedule", []):
                activity = item.get("activity", "")
                location = item.get("location", "")
                cost     = item.get("cost_inr", 0)
                if location and activity:
                    day_places.append({
                        "name":     f"{activity} ({location})",
                        "cost_inr": cost,
                    })
            if day_places:
                places_by_day.append({
                    "day":    day.get("day", 1),
                    "title":  day.get("title", ""),
                    "places": day_places[:5],  # top 5 per day
                })

        prompt = f"""Plan the COMPLETE journey for this trip. Cover every leg.
 
TRIP DETAILS:
  Route      : {request.origin} → {request.destination}
  Travel type: {request.travel_type}
  Passengers : {request.passengers}
  Hotel      : {hotel_name}, {hotel_area}
  Preferences: {request.pref_str()}
 
LEG 1 — HOME TO ORIGIN AIRPORT:
  Origin city    : {request.origin}
  Airport        : {origin_airport['airport_name']}
  Known options  : {json.dumps(origin_airport['transport_options'], indent=2)}
 
LEG 2 — MAIN JOURNEY (TRANSPORT OPTIONS):
  Flight    : {rec_flight.get('airline','')}{rec_flight.get('flight_number','')} | {rec_flight.get('depart_time','')} → {rec_flight.get('arrive_time','')}
  Train     : {rec_train.get('train_name','')} | {rec_train.get('departure_time','')} → {rec_train.get('arrival_time','')}
  Bus       : {rec_bus.get('operator','')} | {rec_bus.get('departure_time','')} → {rec_bus.get('arrival_time','')}
  Instruction: Display Flight, Train, and Bus as choices for this leg so the user can select their preferred mode after generation.
 
LEG 3 — DESTINATION AIRPORT/STATION TO HOTEL:
  Destination    : {request.destination}
  Airport        : {dest_airport['airport_name']}
  Hotel area     : {hotel_area}
  Known options  : {json.dumps(dest_airport['transport_options'], indent=2)}
 
LEG 4 — LOCAL SIGHTSEEING (hotel → places → hotel each day):
  Primary local transport: {local_transport['primary']}
  Daily budget estimate  : Rs.{local_transport['daily_budget_inr']}
  Places to visit by day:
{json.dumps(places_by_day, indent=2)}
 
TASKS:
1. For Leg 1 and 3: list all transport options with real costs and times
2. For each sightseeing day: plan how to get between places (mode, time, cost)
3. Include entry fees for each attraction (real 2025 prices if known)
4. Add best time to visit each place
5. Suggest walking routes where places are close together
6. Calculate total local transport + entry fee costs
 
Return ONLY the JSON structure. Be specific with real place names and costs."""
 
        result = chat_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=3000)
 
        if result.get("_parse_error"):
            print(f"  [{self.name}] JSON parse issue - using structured fallback")
            return self._fallback(request, origin_airport, dest_airport,
                                  local_transport, days)
 
        return result
 
    def _fallback(
        self,
        request:        TravelRequest,
        origin_airport: dict,
        dest_airport:   dict,
        local_transport:dict,
        days:           list,
    ) -> dict:
        """
        Structured fallback using our built-in data when Gemini JSON fails.
        Always returns something useful.
        """
        legs = [
            {
                "leg_number": 1,
                "leg_name":   "Home to Origin Airport",
                "from":       request.origin,
                "to":         origin_airport["airport_name"],
                "options":    origin_airport["transport_options"],
                "recommended":origin_airport["recommended"],
                "note":       "Recommended based on cost and reliability",
            },
            {
                "leg_number": 2,
                "leg_name":   "Main Journey",
                "from":       request.origin,
                "to":         request.destination,
                "options":    [{"mode":"See Flights/Trains/Buses tab",
                                "duration":"Varies","cost_inr":0,"tip":""}],
                "recommended":"See transport tab",
                "note":       "Check Flights, Trains and Buses tabs for options",
            },
            {
                "leg_number": 3,
                "leg_name":   "Airport/Station to Hotel",
                "from":       dest_airport["airport_name"],
                "to":         "Hotel",
                "options":    dest_airport["transport_options"],
                "recommended":dest_airport["recommended"],
                "note":       "Recommended for comfort and safety",
            },
            {
                "leg_number": 4,
                "leg_name":   "Local Sightseeing",
                "from":       "Hotel",
                "to":         "Various attractions",
                "options":    [
                    {"mode": local_transport["primary"],
                     "duration":"Varies","cost_inr":local_transport["daily_budget_inr"],
                     "tip": local_transport["tip"]},
                ],
                "recommended": local_transport["primary"],
                "note":        local_transport["tip"],
            },
        ]
 
        # Build sightseeing from itinerary days
        sightseeing = []
        for day in days[:request.duration_days]:
            places = []
            prev   = "Hotel"
            for item in day.get("schedule", [])[:4]:
                places.append({
                    "name":          item.get("activity", ""),
                    "from_previous": prev,
                    "transport":     local_transport["primary"].split("(")[0].strip(),
                    "distance_km":   3,
                    "travel_time":   "15-20 min",
                    "travel_cost_inr": local_transport["daily_budget_inr"] // max(len(day.get("schedule",[1])),1),
                    "entry_fee_inr": item.get("cost_inr", 0),
                    "time_to_spend": item.get("duration", "2 hours"),
                    "best_time":     "Morning",
                    "tip":           item.get("tip", ""),
                })
                prev = item.get("activity", "")
            if places:
                sightseeing.append({
                    "day":                  day.get("day", 1),
                    "places":               places,
                    "daily_transport_cost": local_transport["daily_budget_inr"],
                    "daily_entry_fees":     sum(p["entry_fee_inr"] for p in places),
                })
 
        total_transport = local_transport["daily_budget_inr"] * request.duration_days
        total_fees      = sum(d.get("daily_entry_fees",0) for d in sightseeing)
 
        return {
            "legs":                      legs,
            "sightseeing":               sightseeing,
            "total_local_transport_cost":total_transport,
            "total_entry_fees":          total_fees,
            "transport_tips": [
                local_transport["tip"],
                "Always carry small change for auto-rickshaws",
                "Use Ola/Uber for late-night travel — safer and metered",
            ],
        }
 

# Self-test

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
 
    print("=" * 60)
    print("  journey_agent.py — self test")
    print("=" * 60)
 
    agent = JourneyAgent()
 
    req = TravelRequest(
        destination   = "Goa",
        origin        = "Ahmedabad",
        budget        = 30000,
        duration_days = 5,
        travel_type   = "couple",
        passengers    = 2,
        start_date    = "2025-06-15",
        end_date      = "2025-06-20",
        preferences   = ["beach", "food"],
    )
 
    # Simulate previous agent outputs
    mock_flights = {
        "recommended": {
            "airline": "IndiGo", "flight_number": "6E358",
            "depart_time": "2025-06-15 06:45",
            "arrive_time": "2025-06-15 08:30",
        }
    }
    mock_hotel = {
        "recommended": {"name": "Goa Plaza", "area": "Baga Beach"}
    }
    mock_itinerary = {
        "days": [
            {
                "day": 1, "title": "Arrival & Beach",
                "schedule": [
                    {"time":"10:00","activity":"Baga Beach","location":"Baga Beach, North Goa","cost_inr":0,"duration":"2 hrs","tip":"Go early morning"},
                    {"time":"14:00","activity":"Britto's Restaurant","location":"Baga","cost_inr":600,"duration":"1 hr","tip":"Try fish curry"},
                    {"time":"18:00","activity":"Sunset at Anjuna","location":"Anjuna Beach","cost_inr":0,"duration":"1 hr","tip":""},
                ],
            },
            {
                "day": 2, "title": "Water Sports",
                "schedule": [
                    {"time":"09:00","activity":"Parasailing","location":"Baga Beach","cost_inr":1200,"duration":"1 hr","tip":"Book early"},
                    {"time":"14:00","activity":"Anjuna Flea Market","location":"Anjuna","cost_inr":0,"duration":"2 hrs","tip":"Bargain hard"},
                    {"time":"19:00","activity":"Thalassa Restaurant","location":"Vagator","cost_inr":1000,"duration":"2 hrs","tip":"Reservations needed"},
                ],
            },
        ]
    }
 
    print(f"\n  Planning complete journey: {req.origin} → {req.destination}")
    print("  (Calling Gemini — may take 10-15 seconds...)\n")
 
    result = agent.run(req, mock_flights, mock_hotel, mock_itinerary)
 
    # Print legs
    legs = result.get("legs", [])
    print(f"  JOURNEY LEGS ({len(legs)} total):")
    for i, leg in enumerate(legs):
        print(f"\n  Leg {leg.get('leg_number', i+1)}: {leg.get('leg_name', 'Unknown')}")
        print(f"    {leg.get('from', '')} → {leg.get('to', '')}")
        for opt in leg.get("options", [])[:2]:
            print(f"    • {opt.get('mode', ''):25s} {opt.get('duration', ''):12s} Rs.{opt.get('cost_inr',0)}")
        print(f"  Recommended: {leg.get('recommended','')}")
        if leg.get("note"):
            print(f"  {leg['note']}")
 
    # Print sightseeing
    sightseeing = result.get("sightseeing", [])
    print(f"\n  SIGHTSEEING ({len(sightseeing)} days):")
    for day in sightseeing:
        print(f"\n  Day {day['day']} — Transport: Rs.{day.get('daily_transport_cost',0)} | Entry: Rs.{day.get('daily_entry_fees',0)}")
        for place in day.get("places", []):
            print(f"    → {place.get('transport','')}: {place.get('name','')[:40]}")
            print(f"       {place.get('travel_time','')} | Rs.{place.get('travel_cost_inr',0)} | "
                  f"Entry: Rs.{place.get('entry_fee_inr',0)} | Stay: {place.get('time_to_spend','')}")
            if place.get("best_time"):
                print(f"       Best time: {place.get('best_time')}")
 
    # Summary
    print(f"\n  Total local transport : Rs.{result.get('total_local_transport_cost',0):,}")
    print(f"  Total entry fees      : Rs.{result.get('total_entry_fees',0):,}")
 
    tips = result.get("transport_tips", [])
    if tips:
        print(f"\n  Tips:")
        for tip in tips:
            print(f"    • {tip}")
 
    print("\n" + "=" * 60)
    print("  JourneyAgent done!")
    print("=" * 60)
 
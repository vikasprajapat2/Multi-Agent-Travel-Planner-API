import os 
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# season data per destination
 
_WEATHER: dict[str, dict] = {
    "goa": {
        "winter": {"temp": "22-30°C", "condition": "Sunny & dry",   "advice": "Peak season — book hotels 4–6 weeks early"},
        "summer": {"temp": "28–38°C", "condition": "Hot & humid",   "advice": "Off-season, fewer crowds, 30–40% cheaper hotels"},
        "monsoon":{"temp": "24–30°C", "condition": "Heavy monsoon", "advice": "Beaches close; great for Dudhsagar waterfall hikes"},
    },
    "manali": {
        "winter": {"temp": "-10–5°C", "condition": "Heavy snowfall","advice": "Rohtang Pass closed; great for snow activities"},
        "summer": {"temp": "10–25°C", "condition": "Pleasant",      "advice": "Best time — Rohtang Pass open, all treks accessible"},
        "monsoon":{"temp": "10–20°C", "condition": "Light rain",    "advice": "Landslide risk on mountain roads; check advisories"},
    },
    "kerala": {
        "winter": {"temp": "20–32°C", "condition": "Warm & pleasant","advice": "Ideal — backwaters, beaches and wildlife at best"},
        "summer": {"temp": "28–38°C", "condition": "Hot & humid",   "advice": "Hills (Munnar, Wayanad) are cooler alternatives"},
        "monsoon":{"temp": "22–30°C", "condition": "Lush rains",    "advice": "Off-season; excellent for Ayurveda retreats"},
    },
    "jaipur": {
        "winter": {"temp": "8–25°C",  "condition": "Cool & sunny",  "advice": "Best time to visit — pleasant days, cold nights"},
        "summer": {"temp": "30–45°C", "condition": "Scorching hot", "advice": "Sightseeing only in early morning (6–10am)"},
        "monsoon":{"temp": "25–35°C", "condition": "Warm with showers","advice": "Forts and palaces look stunning in the rain"},
    },
    "delhi": {
        "winter": {"temp": "5–20°C",  "condition": "Cool, foggy mornings","advice": "Fog delays possible — buffer extra time for flights"},
        "summer": {"temp": "35–48°C", "condition": "Very hot",      "advice": "Stay indoors 11am–4pm; carry water everywhere"},
        "monsoon":{"temp": "25–38°C", "condition": "Humid with rain","advice": "Waterlogging common; use metro over road transport"},
    },
    "mumbai": {
        "winter": {"temp": "15–30°C", "condition": "Pleasant",      "advice": "Best time — cool evenings, sea breeze"},
        "summer": {"temp": "28–38°C", "condition": "Hot & humid",   "advice": "Coastal wind helps; beach evenings are pleasant"},
        "monsoon":{"temp": "24–32°C", "condition": "Heavy rains",   "advice": "Street food season! Watch for waterlogged roads"},
    },
    "maldives": {
        "winter": {"temp": "27–30°C", "condition": "Sunny & calm",  "advice": "Perfect — best visibility for snorkelling/diving"},
        "summer": {"temp": "28–32°C", "condition": "Mostly sunny",  "advice": "Good value — 20–30% lower rates than peak season"},
        "monsoon":{"temp": "26–31°C", "condition": "Occasional rain","advice": "Short showers, still beautiful — big price drops"},
    },
    "bangkok": {
        "winter": {"temp": "20–32°C", "condition": "Sunny & dry",   "advice": "Peak season — best weather but crowded and pricey"},
        "summer": {"temp": "28–38°C", "condition": "Hot",           "advice": "Very hot; temples in early morning, malls midday"},
        "monsoon":{"temp": "25–34°C", "condition": "Daily showers", "advice": "Short afternoon showers — still great for food & culture"},
    },
    "dubai": {
        "winter": {"temp": "16–26°C", "condition": "Perfect",       "advice": "Best time — outdoor activities, desert safaris"},
        "summer": {"temp": "35–47°C", "condition": "Extreme heat",  "advice": "Stay in malls and hotels — outdoor heat is dangerous"},
        "monsoon":{"temp": "28–40°C", "condition": "Hot & clear",   "advice": "Dubai has no real monsoon; summer rules still apply"},
    },
    # Generic fallback for unlisted destinations
    "default": {
        "winter": {"temp": "15–28°C", "condition": "Pleasant",      "advice": "Generally a good time to visit"},
        "summer": {"temp": "30–42°C", "condition": "Hot",           "advice": "Stay hydrated; early morning sightseeing recommended"},
        "monsoon":{"temp": "22–32°C", "condition": "Rainy",         "advice": "Carry rain gear; check local flood advisories"},
    },
}

# sefety tips per destination
_SAFETY: dict[str, list[str]] = {
     "goa":     [
        "Use Ola/Uber or pre-paid taxis — avoid unlicensed bikes",
        "Keep valuables in hotel safe at beaches",
        "Avoid isolated stretches of beach after dark",
    ],
    "delhi":   [
        "Use Delhi Metro — safer and faster than road during rush hour",
        "Only use Ola/Uber or pre-paid taxis from official counters",
        "Keep photocopies of passport and ID in a separate bag",
    ],
    "mumbai":  [
        "Local trains are safe but very crowded during rush hour (8–10am, 5–8pm)",
        "Carry small change for autorickshaws — drivers rarely have change",
        "Watch for pickpockets near Gateway of India and Juhu Beach",
    ],
    "manali":  [
        "Altitude sickness above 3000m — ascend slowly, stay hydrated",
        "Always check road conditions before heading to Rohtang Pass",
        "Inform your hotel about trek plans — register with local police for high-altitude treks",
    ],
    "bangkok": [
        "Use BTS Skytrain or MRT — avoid tuk-tuks for long distances (very overpriced)",
        "Watch for the 'closed temple' scam — temples are almost never closed",
        "Only exchange currency at banks or authorised changers, not street stalls",
    ],
    "dubai":   [
        "Dress modestly in public areas and malls",
        "Alcohol only in licensed hotels and restaurants — not on streets",
        "Very safe city overall — petty crime is rare",
    ],
    "default": [
        "Buy travel insurance before departure — cover medical + cancellation",
        "Keep digital copies of all documents in email or cloud storage",
        "Save local emergency numbers in your phone (police, ambulance, embassy)",
    ],
}
 

# local events per destination 
_EVENTS: dict[str, list[str]] = {
    "goa":    ["Goa Carnival (Feb)", "Sunburn Music Festival (Dec)", "Shigmo Festival (Mar)"],
    "jaipur": ["Jaipur Literature Festival (Jan)", "Elephant Festival (Mar)", "Teej (Jul–Aug)"],
    "kerala": ["Onam (Aug–Sep)", "Thrissur Pooram (Apr–May)", "Kerala Boat Race (Aug)"],
    "manali": ["Hadimba Devi Fair (May)", "Dussehra (Oct)", "Winter Carnival (Jan)"],
    "delhi":  ["Republic Day Parade (Jan 26)", "Diwali in Connaught Place (Oct–Nov)", "Qutub Festival (Oct–Nov)"],
    "mumbai": ["Ganesh Chaturthi (Aug–Sep)", "Mumbai Film Festival (Oct)", "Kala Ghoda Arts Festival (Feb)"],
    "default":["Check local tourism board for festivals during your travel dates"],
}

#packing list per season
_PACKING: dict[str, list[str]] = {
    "winter": ["Light layers (days warm, evenings cool)", "Comfortable walking shoes", "Sunscreen SPF 30+"],
    "summer": ["Loose cotton clothes", "High SPF sunscreen (50+)", "Sunglasses and hat", "Electrolyte sachets"],
    "monsoon":["Waterproof jacket or compact umbrella", "Quick-dry clothes", "Waterproof sandals or shoes"],
}

# Extra packing tips for specific destination types
_EXTRA_PACKING: dict[str, list[str]] = {
    "manali":   ["Heavy jacket (even in summer above 3000m)", "Thermal innerwear", "Sturdy trekking shoes"],
    "goa":      ["Swimwear", "Beach towel", "Flip-flops", "After-sun lotion"],
    "maldives": ["Snorkelling gear (or rent there)", "Reef-safe sunscreen", "Light linen clothes"],
    "kerala":   ["Insect repellent", "Modest clothes for temple visits", "Light raincoat"],
    "dubai":    ["Modest clothes for malls and public areas", "Formal wear for upscale restaurants"],
    "default":  [],
}

# season detection
def _get_season(month: int) -> str:
    if month in (11,12,1,2):
        return "winter"
    if month in (3,4,5):
        return "summer"
    return "monsoon"


# public interface 
def get_weather_context(destination: str, travel_date: str) -> dict:
    dest_key = destination.lower().split(',')[0].strip()
     
    try:
        month = int(travel_date[5:7])
    except(IndexError, ValueError):
        month = 1 
    
    season = _get_season(month)
    weather = _WEATHER.get(dest_key, _WEATHER['default'])[season]
    safety = _SAFETY.get(dest_key, _SAFETY['default'])
    events = _EVENTS.get(dest_key, _EVENTS['default'])

    packing = _PACKING[season] + _EXTRA_PACKING.get(dest_key, _EXTRA_PACKING['default'])

    best_time_map={
        "goa": "October to March", "manali": "April to June",
        "kerala": "October to March", "dubai": "November to March",
        "maldives": "November to April", "default": "October to February",       
    }
    best_time = best_time_map.get(dest_key, best_time_map["default"])

    return {
        "destination":   destination,
        "travel_date":   travel_date,
        "season":        season,
        "temperature":   weather["temp"],
        "condition":     weather["condition"],
        "travel_advice": weather["advice"],
        "safety_tips":   safety,
        "local_events":  events,
        "packing_tips":  packing,
        "best_time":     best_time,
    }

# self  test
if __name__=="__main__":
    print("=" * 55)
    print("  weather_api.py — self test")
    print("=" * 55)
 
    tests = [
        ("Goa",      "2025-06-15", "monsoon"),   # Jun → monsoon
        ("Manali",   "2025-05-20", "summer"),    # May → summer
        ("Jaipur",   "2025-12-10", "winter"),    # Dec → winter
        ("Bangkok",  "2025-01-25", "winter"),    # Jan → winter
        ("Zanzibar", "2025-08-01", "monsoon"),   # unknown → fallback
    ]
 
    for dest, date, expected_season in tests:
        result = get_weather_context(dest, date)
        season_ok = "✅" if result["season"] == expected_season else "❌"
        print(f"\n  {dest:12s} | {date} | Season: {result['season']:7s} {season_ok}")
        print(f"    Temp      : {result['temperature']}")
        print(f"    Condition : {result['condition']}")
        print(f"    Advice    : {result['travel_advice']}")
        print(f"    Safety    : {result['safety_tips'][0]}")
        print(f"    Packing   : {', '.join(result['packing_tips'][:2])}...")
        assert result["season"] == expected_season, \
            f"Expected {expected_season} for month {date[5:7]}"
 
    print("\n  All season detections correct")
    print("\n" + "=" * 55)
    print("  weather_api.py done!")
    print("  All 3 tools complete — ready for Part 4 (agents).")
    print("=" * 55)
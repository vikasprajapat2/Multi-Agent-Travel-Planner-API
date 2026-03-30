
# tools/flight_api.py
# REAL API : AviationStack  →  aviationstack.com
# MOCK     : Realistic Indian flight data (USE_MOCK_APIS=true
# .env setup:
#   AVIATIONSTACK_API_KEY=your_regenerated_key_here
#   USE_MOCK_APIS=false     ← set false to use real AviationStack data
# AviationStack free tier:
#   100 calls/month · real-time schedules · no fare data (prices estimated)
#   Docs: https://aviationstack.com/documentation
#
# RUN TO TEST:
#   PYTHONPATH=. python tools/flight_api.py

import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import random
import requests
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from config import USE_MOCK_APIS

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")
AVIATIONSTACK_BASE    = "http://api.aviationstack.com/v1"

# PART A — FlightOption dataclass

@dataclass
class FlightOption:
    airline:       str
    flight_number: str
    origin:        str
    destination:   str
    depart_time:   str
    arrive_time:   str
    duration:      str
    stops:         int
    price_inr:     int
    cabin:         str
    baggage:       str
    refundable:    bool

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        stop_label = "Non-stop" if self.stops == 0 else f"{self.stops} stop"
        return (
            f"{self.airline} {self.flight_number} | "
            f"{self.depart_time} → {self.arrive_time} ({self.duration}) | "
            f"{stop_label} | ₹{self.price_inr:,}"
        )


# PART B — Mock data (USE_MOCK_APIS=true)

_ROUTES: dict[tuple, dict] = {
    ("AMD", "GOI"): {"airlines": ["IndiGo", "Air India", "SpiceJet"],     "base": (3800,  7500),  "dur": "1h 45m"},
    ("DEL", "GOI"): {"airlines": ["IndiGo", "Vistara",  "Air India"],     "base": (4500,  9000),  "dur": "2h 10m"},
    ("BOM", "GOI"): {"airlines": ["IndiGo", "GoAir",    "SpiceJet"],      "base": (2500,  5500),  "dur": "1h 05m"},
    ("DEL", "BOM"): {"airlines": ["IndiGo", "Vistara",  "Air India"],     "base": (3200,  8000),  "dur": "2h 20m"},
    ("DEL", "BLR"): {"airlines": ["IndiGo", "Vistara",  "SpiceJet"],      "base": (3500,  7500),  "dur": "2h 50m"},
    ("DEL", "CCU"): {"airlines": ["IndiGo", "Air India","Vistara"],       "base": (3000,  7000),  "dur": "2h 10m"},
    ("BOM", "BLR"): {"airlines": ["IndiGo", "Air India","GoAir"],         "base": (2800,  6000),  "dur": "1h 20m"},
    ("DEL", "DXB"): {"airlines": ["Emirates","Air India","IndiGo"],        "base": (12000,28000),  "dur": "3h 30m"},
    ("BOM", "DXB"): {"airlines": ["Emirates","Air India","Vistara"],       "base": (9500, 22000),  "dur": "3h 00m"},
    ("DEL", "BKK"): {"airlines": ["Thai Airways","Air India","IndiGo"],    "base": (14000,35000),  "dur": "4h 30m"},
}

_IATA: dict[str, str] = {
    "IndiGo": "6E", "Air India": "AI", "SpiceJet": "SG",
    "Vistara": "UK", "GoAir":    "G8", "Emirates": "EK",
    "Thai Airways": "TG",
}

_DEP_HOURS = [6, 8, 10, 13, 16, 19, 21]


def _route_key(origin: str, dest: str) -> tuple | None:
    o, d = origin.upper()[:3], dest.upper()[:3]
    if (o, d) in _ROUTES: return (o, d)
    if (d, o) in _ROUTES: return (d, o)
    return None


def _mock_search(
    origin: str, destination: str, date: str,
    passengers: int = 1, budget_per_person: float | None = None,
) -> list[FlightOption]:
    """Generate deterministic mock flights for a route."""
    key = _route_key(origin, destination)
    if key:
        info = _ROUTES[key]
        airlines, (pmin, pmax), duration = info["airlines"], info["base"], info["dur"]
    else:
        airlines, pmin, pmax, duration = ["Air India", "IndiGo", "Emirates"], 8000, 35000, "5h 00m"

    random.seed(hash(date + origin.upper() + destination.upper()) % 9999)
    flights = []

    for i, airline in enumerate(airlines):
        code     = _IATA.get(airline, "XX")
        dep_hour = _DEP_HOURS[i % len(_DEP_HOURS)]
        dep_min  = random.choice([0, 15, 30, 45])
        price_pp = random.randint(pmin, pmax)

        dur_parts = duration.replace("h","").replace("m","").split()
        dur_mins  = int(dur_parts[0]) * 60 + int(dur_parts[1])
        arr_total = dep_hour * 60 + dep_min + dur_mins
        arr_hour, arr_min = (arr_total // 60) % 24, arr_total % 60

        flights.append(FlightOption(
            airline       = airline,
            flight_number = f"{code}{random.randint(100,999)}",
            origin        = origin.upper()[:3],
            destination   = destination.upper()[:3],
            depart_time   = f"{date} {dep_hour:02d}:{dep_min:02d}",
            arrive_time   = f"{date} {arr_hour:02d}:{arr_min:02d}",
            duration      = duration,
            stops         = 0 if price_pp > (pmin+pmax)//2 else random.choice([0,1]),
            price_inr     = price_pp * passengers,
            cabin         = "Economy",
            baggage       = "15 kg check-in included",
            refundable    = random.choice([True, False]),
        ))

    if budget_per_person:
        affordable = [f for f in flights if f.price_inr / passengers <= budget_per_person]
        flights = affordable or [min(flights, key=lambda f: f.price_inr)]

    return sorted(flights, key=lambda f: f.price_inr)


# Price estimates by airline (INR per person, no fare data available)
_PRICE_ESTIMATES: dict[str, tuple] = {
    "indigo":    (3500,  7000),
    "spicejet":  (3000,  6500),
    "goair":     (3200,  6000),
    "air india": (5000, 12000),
    "vistara":   (5500, 13000),
    "emirates":  (12000,30000),
    "thai":      (14000,32000),
    "default":   (4000, 10000),
}


def _estimate_price(airline_name: str, passengers: int) -> int:
    """Estimate ticket price by matching airline name to price tier."""
    name_lower = airline_name.lower()
    tier = next(
        (v for k, v in _PRICE_ESTIMATES.items() if k in name_lower),
        _PRICE_ESTIMATES["default"],
    )
    return random.randint(*tier) * passengers


def _parse_scheduled_time(iso_str: str, date: str) -> str:
    """
    Extract time from ISO datetime: "2025-06-15T06:15:00+00:00" → "2025-06-15 06:15"
    Falls back gracefully if string is malformed.
    """
    if not iso_str:
        return f"{date} 00:00"
    try:
        time_part = iso_str.split("T")[1][:5]
        return f"{date} {time_part}"
    except (IndexError, AttributeError):
        return f"{date} 00:00"


def _calc_duration(dep_iso: str, arr_iso: str) -> str:
    """Calculate flight duration from two ISO timestamps."""
    try:
        from datetime import datetime
        dep = datetime.fromisoformat(dep_iso.replace("+00:00",""))
        arr = datetime.fromisoformat(arr_iso.replace("+00:00",""))
        mins = int((arr - dep).total_seconds() / 60)
        if mins < 0:
            mins += 1440   # handle midnight crossing
        return f"{mins // 60}h {mins % 60:02d}m"
    except Exception:
        return "N/A"


def _aviationstack_search(
    origin: str, destination: str, date: str,
    passengers: int = 1, budget_per_person: float | None = None,
) -> list[FlightOption]:
    """
    Fetch real flight schedules from AviationStack API.
    Falls back to mock data if API returns no results.
    """
    if not AVIATIONSTACK_API_KEY:
        raise RuntimeError(
            "AVIATIONSTACK_API_KEY missing from .env\n"
            "→ Regenerate at aviationstack.com/dashboard\n"
            "→ Add to .env: AVIATIONSTACK_API_KEY=your_key"
        )

    params = {
        "access_key":  AVIATIONSTACK_API_KEY,
        "dep_iata":    origin.upper()[:3],
        "arr_iata":    destination.upper()[:3],
        "flight_date": date,
        "limit":       10,
    }

    try:
        resp = requests.get(
            f"{AVIATIONSTACK_BASE}/flights",
            params  = params,
            timeout = 10,
        )
        resp.raise_for_status()
        data = resp.json()

    except requests.exceptions.Timeout:
        print("  [AviationStack] Timeout — using mock data")
        return _mock_search(origin, destination, date, passengers, budget_per_person)
    except requests.exceptions.RequestException as e:
        print(f"  [AviationStack] Request error: {e} — using mock data")
        return _mock_search(origin, destination, date, passengers, budget_per_person)

    # AviationStack API-level errors come back in the JSON body
    if "error" in data:
        err = data["error"]
        code, msg = err.get("code",""), err.get("message","unknown")
        raise RuntimeError(f"AviationStack API error {code}: {msg}")

    flights_raw = data.get("data", [])

    # No flights found for this route/date → fall back silently
    if not flights_raw:
        print(f"  [AviationStack] No flights for {origin}→{destination} on {date} — using mock")
        return _mock_search(origin, destination, date, passengers, budget_per_person)

    # Parse each flight record
    flights: list[FlightOption] = []
    for raw in flights_raw:
        try:
            airline_name  = raw.get("airline",   {}).get("name", "Unknown")
            flight_iata   = raw.get("flight",    {}).get("iata", "XX000")
            dep_iata      = raw.get("departure", {}).get("iata", origin.upper()[:3])
            arr_iata      = raw.get("arrival",   {}).get("iata", destination.upper()[:3])
            dep_sched     = raw.get("departure", {}).get("scheduled", "")
            arr_sched     = raw.get("arrival",   {}).get("scheduled", "")

            price_inr = _estimate_price(airline_name, passengers)

            # Apply budget filter
            if budget_per_person and price_inr / passengers > budget_per_person:
                continue

            flights.append(FlightOption(
                airline       = airline_name,
                flight_number = flight_iata,
                origin        = dep_iata,
                destination   = arr_iata,
                depart_time   = _parse_scheduled_time(dep_sched, date),
                arrive_time   = _parse_scheduled_time(arr_sched, date),
                duration      = _calc_duration(dep_sched, arr_sched),
                stops         = 0,   # /flights returns direct legs only
                price_inr     = price_inr,
                cabin         = "Economy",
                baggage       = "15 kg check-in included",
                refundable    = False,
            ))
        except Exception:
            continue   # skip malformed entries — never crash

    # If budget filter eliminated everything, return cheapest
    if not flights and flights_raw:
        raw = flights_raw[0]
        flights = [FlightOption(
            airline       = raw.get("airline",{}).get("name","Air India"),
            flight_number = raw.get("flight",{}).get("iata","AI000"),
            origin        = origin.upper()[:3],
            destination   = destination.upper()[:3],
            depart_time   = _parse_scheduled_time(raw.get("departure",{}).get("scheduled",""), date),
            arrive_time   = _parse_scheduled_time(raw.get("arrival",{}).get("scheduled",""), date),
            duration      = "N/A",
            stops         = 0,
            price_inr     = _estimate_price("default", passengers),
            cabin         = "Economy",
            baggage       = "15 kg check-in included",
            refundable    = False,
        )]

    return sorted(flights, key=lambda f: f.price_inr)

# PART D — Public interface (the only function agents ever call)


def search_flights(
    origin:            str,
    destination:       str,
    date:              str,
    passengers:        int         = 1,
    budget_per_person: float | None = None,
) -> list[dict]:
    """
    Search for flights. Returns list of up to 4 flight option dicts.

    Routes to mock or AviationStack based on USE_MOCK_APIS in .env.
    Agents are completely unaware of which source is active.

    RETURNS list of dicts with keys:
        airline, flight_number, origin, destination,
        depart_time, arrive_time, duration, stops,
        price_inr, cabin, baggage, refundable
    """
    if USE_MOCK_APIS:
        options = _mock_search(origin, destination, date, passengers, budget_per_person)
    else:
        options = _aviationstack_search(origin, destination, date, passengers, budget_per_person)

    return [f.to_dict() for f in options[:4]]



# PART E — Self-test


if __name__ == "__main__":
    print("=" * 55)
    print("  flight_api.py — self test")
    print(f"  Mode: {'MOCK' if USE_MOCK_APIS else 'REAL — AviationStack'}")
    if not USE_MOCK_APIS:
        masked = AVIATIONSTACK_API_KEY[:6] + "..." if AVIATIONSTACK_API_KEY else "NOT SET"
        print(f"  Key : {masked}")
    print("=" * 55)

    tests = [
        ("AMD", "GOI", "2025-06-15", 2, None,  "AMD → GOI, 2 pax, no limit"),
        ("DEL", "BOM", "2025-06-20", 1, 5000,  "DEL → BOM, 1 pax, ₹5k budget"),
        ("DEL", "DXB", "2025-07-10", 2, None,  "DEL → DXB, international"),
    ]

    for origin, dest, date, pax, budget, label in tests:
        print(f"\n  [{label}]")
        try:
            results = search_flights(origin, dest, date, pax, budget)
            if not results:
                print("    No results returned")
                continue
            for f in results:
                stops = "Non-stop" if f["stops"] == 0 else "1 stop"
                print(f"    {f['airline']:22s} {f['flight_number']:7s} | "
                      f"{f['depart_time'][-5:]} → {f['arrive_time'][-5:]} | "
                      f"{stops:8s} | ₹{f['price_inr']:,}")
        except RuntimeError as e:
            print(f" {e}")

    # Determinism check (mock mode only)
    if USE_MOCK_APIS:
        r1 = search_flights("AMD", "GOI", "2025-06-15", 2)
        r2 = search_flights("AMD", "GOI", "2025-06-15", 2)
        assert r1 == r2, "Mock results must be deterministic!"
        print("\n  Deterministic — same query always returns same results")

    print("\n" + "=" * 55)
    print("  Done. Next → Part 4 (agents).")
    print("=" * 55)
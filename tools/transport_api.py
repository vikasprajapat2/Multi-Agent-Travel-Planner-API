import os
import sys
import random
import requests
from dataclasses import dataclass, asdict, field
from dotenv import load_dotenv
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
 
from config import USE_MOCK_APIS
 
RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY",  "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "booking-com15.p.rapidapi.com")
IRCTC_RAPIDAPI_KEY = os.getenv("IRCTC_RAPIDAPI_KEY",  "") or os.getenv("RAPIDAPI_KEY", "")
IRCTC_RAPIDAPI_HOST= os.getenv("IRCTC_RAPIDAPI_HOST", "irctc1.p.rapidapi.com")

# Data classes

@dataclass
class TrainOption:
    train_name:    str
    train_number:  str
    origin:        str
    destination:   str
    depart_time:   str
    arrive_time:   str
    duration:      str
    distance_km:   int
    travel_class:  str    # SL | 3A | 2A | 1A
    price_inr:     int    # total for all passengers
    availability:  str    # "Available" | "Waitlist" | "RAC"
    days_of_run:   str    # "Daily" | "Mon,Wed,Fri" etc.
    class_prices:  dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
 
    def summary(self) -> str:
        return (
            f"{self.train_name} ({self.train_number}) | "
            f"{self.depart_time} → {self.arrive_time} ({self.duration}) | "
            f"{self.travel_class} | Rs.{self.price_inr:,}"
        )

@dataclass
class BusOption:
    operator:      str
    bus_type:      str    # Sleeper | AC Sleeper | Volvo AC | Non-AC Seater
    origin:        str
    destination:   str
    depart_time:   str
    arrive_time:   str
    duration:      str
    price_inr:     int    # total for all passengers
    seats_left:    int
    amenities:     list   # ["USB Charging", "Blanket", "Water bottle"]
    rating:        float  # out of 5
 
    def to_dict(self) -> dict:
        return asdict(self)
 
    def summary(self) -> str:
        return (
            f"{self.operator} | {self.bus_type} | "
            f"{self.depart_time} → {self.arrive_time} ({self.duration}) | "
            f"Rs.{self.price_inr:,} | {self.seats_left} seats left"
        )
    
# Trin Route database
 
_TRAIN_ROUTES: dict[tuple, dict] = {
    # ── Gujarat routes ────────────────────────────────────────────────────────
    ("ADI", "GOA"): {
        "trains": [
            {"name":"Goa Express",      "number":"10103","dep":"22:30","arr":"16:45","dur":"18h 15m","dist":690},
            {"name":"Mandovi Express",  "number":"10103","dep":"08:15","arr":"06:40","dur":"22h 25m","dist":690},
        ],
        "prices": {"SL":485, "3A":1285, "2A":1850, "1A":3100},
    },
    ("ADI", "DEL"): {
        "trains": [
            {"name":"Rajdhani Express", "number":"12957","dep":"19:55","arr":"09:55","dur":"14h 00m","dist":934},
            {"name":"Shatabdi Express", "number":"12009","dep":"06:25","arr":"14:05","dur":"07h 40m","dist":934},
            {"name":"Gujarat Mail",     "number":"12901","dep":"23:00","arr":"13:35","dur":"14h 35m","dist":934},
        ],
        "prices": {"SL":550, "3A":1450, "2A":2100, "1A":3500},
    },
    ("ADI", "BOM"): {
        "trains": [
            {"name":"August Kranti Raj","number":"12953","dep":"17:40","arr":"23:35","dur":"05h 55m","dist":491},
            {"name":"Shatabdi Express", "number":"12009","dep":"06:25","arr":"12:15","dur":"05h 50m","dist":491},
            {"name":"Gujarat Express",  "number":"19011","dep":"21:30","arr":"05:15","dur":"07h 45m","dist":491},
        ],
        "prices": {"SL":265, "3A":720,  "2A":1020, "1A":1700},
    },
    # ── Delhi routes ──────────────────────────────────────────────────────────
    ("DEL", "BOM"): {
        "trains": [
            {"name":"Rajdhani Express", "number":"12951","dep":"16:55","arr":"08:35","dur":"15h 40m","dist":1384},
            {"name":"August Kranti Raj","number":"12953","dep":"17:25","arr":"10:55","dur":"17h 30m","dist":1384},
            {"name":"Punjab Mail",      "number":"12137","dep":"19:18","arr":"15:25","dur":"20h 07m","dist":1384},
        ],
        "prices": {"SL":650, "3A":1720, "2A":2480, "1A":4150},
    },
    ("DEL", "GOA"): {
        "trains": [
            {"name":"Goa Express",      "number":"12779","dep":"15:00","arr":"09:45","dur":"42h 45m","dist":1869},
            {"name":"Mandovi Express",  "number":"10103","dep":"07:30","arr":"02:25","dur":"42h 55m","dist":1869},
        ],
        "prices": {"SL":780, "3A":2050, "2A":2960, "1A":4950},
    },
    ("DEL", "JAI"): {
        "trains": [
            {"name":"Ajmer Shatabdi",   "number":"12015","dep":"06:05","arr":"10:35","dur":"04h 30m","dist":308},
            {"name":"Double Decker",    "number":"12985","dep":"17:30","arr":"21:20","dur":"03h 50m","dist":308},
            {"name":"Pink City Express","number":"12455","dep":"05:50","arr":"10:40","dur":"04h 50m","dist":308},
        ],
        "prices": {"SL":195, "3A":510,  "2A":735,  "1A":1225},
    },
    ("DEL", "MAS"): {
        "trains": [
            {"name":"GT Express",       "number":"12615","dep":"19:30","arr":"06:05","dur":"34h 35m","dist":2182},
            {"name":"Tamil Nadu Exp",   "number":"12621","dep":"22:30","arr":"07:45","dur":"33h 15m","dist":2182},
        ],
        "prices": {"SL":820, "3A":2160, "2A":3120, "1A":5220},
    },
    # ── Mumbai routes ─────────────────────────────────────────────────────────
    ("BOM", "GOA"): {
        "trains": [
            {"name":"Mandovi Express",  "number":"10103","dep":"07:10","arr":"18:05","dur":"10h 55m","dist":581},
            {"name":"Konkan Kanya",     "number":"10111","dep":"22:55","arr":"09:00","dur":"10h 05m","dist":581},
            {"name":"Jan Shatabdi",     "number":"12051","dep":"05:25","arr":"15:30","dur":"10h 05m","dist":581},
        ],
        "prices": {"SL":320, "3A":845,  "2A":1220, "1A":2040},
    },
    ("BOM", "BLR"): {
        "trains": [
            {"name":"Udyan Express",    "number":"11301","dep":"08:05","arr":"01:30","dur":"17h 25m","dist":1013},
            {"name":"Rajdhani Express", "number":"12429","dep":"20:45","arr":"11:50","dur":"15h 05m","dist":1013},
        ],
        "prices": {"SL":455, "3A":1200, "2A":1730, "1A":2890},
    },
}
 
# ── Bus route database ────────────────────────────────────────────────────────
 
_BUS_ROUTES: dict[tuple, dict] = {
    ("ADI", "GOA"):  {"dur":"20h",  "dist":770,  "base":(800,  1800), "operators":["VRL Travels","SRS Travels","Patel Travels"]},
    ("ADI", "BOM"):  {"dur":"8h",   "dist":530,  "base":(400,  900),  "operators":["GSRTC","Orange Travels","Neeta Travels"]},
    ("ADI", "DEL"):  {"dur":"15h",  "dist":940,  "base":(700,  1500), "operators":["GSRTC Volvo","Hans Travels","Shrinath"]},
    ("DEL", "JAI"):  {"dur":"5h",   "dist":280,  "base":(300,  700),  "operators":["RSRTC","Raj Travels","Mandal Travels"]},
    ("DEL", "MNL"):  {"dur":"12h",  "dist":540,  "base":(600,  1400), "operators":["HRTC","Himachal Travels","Volvo HRTC"]},
    ("BOM", "GOA"):  {"dur":"12h",  "dist":600,  "base":(500,  1200), "operators":["Neeta Travels","VRL","Paulo Travels"]},
    ("BOM", "PNQ"):  {"dur":"4h",   "dist":150,  "base":(200,  500),  "operators":["MSRTC","Shivshahi","Parivartan"]},
    ("DEL", "GOA"):  {"dur":"26h",  "dist":1900, "base":(1200, 2500), "operators":["SRS Travels","VRL Travels","Chartered Bus"]},
    ("default",""):  {"dur":"8h",   "dist":400,  "base":(400,  1000), "operators":["State Bus","Private Travels","Volvo Services"]},
}
 
_BUS_TYPES = [
    {"type":"AC Sleeper",      "multiplier":1.4, "amenities":["AC","Blanket","USB Charging","Water Bottle"]},
    {"type":"Non-AC Sleeper",  "multiplier":1.0, "amenities":["Blanket","Reading Light"]},
    {"type":"Volvo AC Seater", "multiplier":1.2, "amenities":["AC","Reclining Seats","USB Charging"]},
    {"type":"Non-AC Seater",   "multiplier":0.7, "amenities":["Fan"]},
]
 
_AVAILABILITY = ["Available", "Available", "Available", "RAC", "Waitlist"]
_DAYS_OF_RUN  = ["Daily", "Daily", "Mon,Wed,Fri,Sun", "Tue,Thu,Sat"]
 

# Routes key helper

def _train_route_key(origin: str, dest: str) -> tuple | None:
    """Find route key — tries both directions."""
    o = origin.upper()[:3]
    d = dest.upper()[:3]
    if (o, d) in _TRAIN_ROUTES: return (o, d)
    if (d, o) in _TRAIN_ROUTES: return (d, o)
    return None
 
 
def _bus_route_key(origin: str, dest: str) -> tuple:
    """Find bus route key — falls back to default."""
    o = origin.upper()[:3]
    d = dest.upper()[:3]
    if (o, d) in _BUS_ROUTES: return (o, d)
    if (d, o) in _BUS_ROUTES: return (d, o)
    return ("default", "")
 

#mock train search
 
def _mock_trains(
    origin:       str,
    destination:  str,
    date:         str,
    passengers:   int  = 1,
    travel_class: str  = "3A",
) -> list[TrainOption]:
    """Generate realistic mock train options."""
    key = _train_route_key(origin, destination)
 
    if key:
        route   = _TRAIN_ROUTES[key]
        trains  = route["trains"]
        prices  = route["prices"]
    else:
        # Generic fallback for unlisted routes
        trains = [{"name":"Express Train","number":"12000",
                   "dep":"08:00","arr":"20:00","dur":"12h 00m","dist":600}]
        prices = {"SL":400,"3A":1050,"2A":1520,"1A":2540}
 
    random.seed(hash(date + origin + destination) % 9999)
 
    valid_class = travel_class if travel_class in prices else "3A"
    price_pp    = prices[valid_class]
    class_prices = {k: v * passengers for k, v in prices.items()}
 
    options = []
    for t in trains:
        options.append(TrainOption(
            train_name   = t["name"],
            train_number = t["number"],
            origin       = origin.upper()[:3],
            destination  = destination.upper()[:3],
            depart_time  = f"{date} {t['dep']}",
            arrive_time  = f"{date} {t['arr']}",
            duration     = t["dur"],
            distance_km  = t["dist"],
            travel_class = valid_class,
            price_inr    = price_pp * passengers,
            availability = random.choice(_AVAILABILITY),
            days_of_run  = random.choice(_DAYS_OF_RUN),
            class_prices = class_prices,
        ))
 
    return options

#Mock bus search
def _mock_buses(
    origin:      str,
    destination: str,
    date:        str,
    passengers:  int = 1,
) -> list[BusOption]:
    """Generate realistic mock bus options."""
    key   = _bus_route_key(origin, destination)
    route = _BUS_ROUTES[key]
 
    random.seed(hash(date + origin + destination + "bus") % 9999)
 
    options = []
    dep_hours = [6, 8, 18, 20, 22]
 
    for i, operator in enumerate(route["operators"]):
        bus_type_data = _BUS_TYPES[i % len(_BUS_TYPES)]
        dep_h = dep_hours[i % len(dep_hours)]
        dep_m = random.choice([0, 15, 30, 45])
 
        # Parse duration
        dur_h = int(route["dur"].replace("h","").strip())
        arr_h = (dep_h + dur_h) % 24
        arr_m = dep_m
 
        pmin, pmax = route["base"]
        price_pp   = int(random.randint(pmin, pmax) * bus_type_data["multiplier"])
 
        options.append(BusOption(
            operator    = operator,
            bus_type    = bus_type_data["type"],
            origin      = origin,
            destination = destination,
            depart_time = f"{date} {dep_h:02d}:{dep_m:02d}",
            arrive_time = f"{date} {arr_h:02d}:{arr_m:02d}",
            duration    = route["dur"],
            price_inr   = price_pp * passengers,
            seats_left  = random.randint(2, 35),
            amenities   = bus_type_data["amenities"],
            rating      = round(random.uniform(3.2, 4.8), 1),
        ))
 
    return sorted(options, key=lambda b: b.price_inr)

# Real IRCTC API via RapidAPI

_CITY_TO_STATION: dict[str, str] = {
    # Gujarat
    "ahmedabad": "ADI", "amd": "ADI", "adi": "ADI",
    "surat":     "ST",  "vadodara": "BRC", "rajkot": "RJT",
    # Maharashtra
    "mumbai":    "CSTM","bom": "CSTM","bombay": "CSTM",
    "pune":      "PUNE","nagpur": "NGP",
    # Delhi/NCR
    "delhi":     "NDLS","del": "NDLS","new delhi": "NDLS",
    "ndls":      "NDLS",
    # South
    "bangalore": "SBC", "bengaluru": "SBC", "blr": "SBC",
    "chennai":   "MAS", "hyderabad": "SC",  "kochi": "ERS",
    "kerala":    "TVC",
    # North
    "jaipur":    "JP",  "jai": "JP",
    "lucknow":   "LKO", "varanasi": "BSB", "agra": "AGC",
    "amritsar":  "ASR",
    # East
    "kolkata":   "HWH", "ccu": "HWH", "patna": "PNBE",
    "bhubaneswar":"BBS",
    # Goa
    "goa":       "MAO", "panaji": "MAO", "madgaon": "MAO",
    "vasco":     "VSG",
    # Hills
    "manali":    "PGH", # nearest: Pathankot — Manali has no railway
    "shimla":    "SML", "darjeeling": "NJP",
    # International (no train)
    "dubai":     None,  "bangkok": None, "singapore": None,
    "maldives":  None,  "bangkok": None,
}
 
 
def _city_to_code(city: str) -> str | None:
    """Convert city name or code to IRCTC station code."""
    key = city.lower().strip()
    # Direct lookup
    if key in _CITY_TO_STATION:
        return _CITY_TO_STATION[key]
    # Try first 3 chars as station code
    if len(key) >= 3:
        code = key[:3].upper()
        return code
    return None
 
 
def _parse_run_days(run_on: dict) -> str:
    """Convert {mon:1, tue:0, ...} to human-readable string."""
    days = {"mon":"Mon","tue":"Tue","wed":"Wed","thu":"Thu",
            "fri":"Fri","sat":"Sat","sun":"Sun"}
    active = [v for k, v in days.items() if run_on.get(k, 0) == 1]
    if len(active) == 7:
        return "Daily"
    if len(active) == 0:
        return "Check schedule"
    return ", ".join(active)
 
 
def _irctc_search(
    origin:       str,
    destination:  str,
    date:         str,
    passengers:   int = 1,
    travel_class: str = "3A",
) -> list[TrainOption]:
    """
    Fetch real train schedules from IRCTC API via RapidAPI.
    Returns TrainOption list. Falls back to mock on any error.
 
    PRICE NOTE:
        IRCTC free API returns schedules, not fares.
        We estimate fares using our _TRAIN_ROUTES price table.
        This gives realistic prices even with real train data.
    """
    if not IRCTC_RAPIDAPI_KEY:
        print("  [IRCTC] No API key — using mock data")
        return []
 
    from_code = _city_to_code(origin)
    to_code   = _city_to_code(destination)
 
    # If either city has no train station (e.g. Dubai), skip
    if not from_code or not to_code:
        print(f"  [IRCTC] No station code for {origin} or {destination} — using mock")
        return []
 
    # IRCTC API needs date in DD-MM-YYYY format
    try:
        y, m, d  = date.split("-")
        irctc_date = f"{d}-{m}-{y}"
    except ValueError:
        irctc_date = date
 
    url     = f"https://{IRCTC_RAPIDAPI_HOST}/api/v3/trainBetweenStations"
    headers = {
        "x-rapidapi-key":  IRCTC_RAPIDAPI_KEY,
        "x-rapidapi-host": IRCTC_RAPIDAPI_HOST,
    }
    params  = {
        "fromStationCode": from_code,
        "toStationCode":   to_code,
        "dateOfJourney":   irctc_date,
    }
 
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        print("  [IRCTC] Timeout — using mock data")
        return []
    except requests.exceptions.RequestException as e:
        print(f"  [IRCTC] Request error: {e} — using mock data")
        return []
 
    if not data.get("status") or not data.get("data"):
        print(f"  [IRCTC] No trains found for {from_code}→{to_code} — using mock")
        return []
 
    # Get price estimates from our table
    key = _train_route_key(from_code, to_code)
    prices = _TRAIN_ROUTES[key]["prices"] if key else {"SL":400,"3A":1050,"2A":1520,"1A":2540}
    valid_class = travel_class if travel_class in prices else "3A"
    price_pp    = prices[valid_class]
 
    options: list[TrainOption] = []
 
    for t in data["data"][:5]:   # parse top 5 results
        try:
            train_name   = t.get("trainName", "Unknown Train").title()
            train_number = str(t.get("trainNo", "00000"))
            dep_time     = t.get("departureTime", "00:00")
            arr_time     = t.get("arrivalTime",   "00:00")
            duration_raw = t.get("duration", "0:0")   # "18:25" format (h:mm)
            distance     = int(t.get("distance", 0))
            run_on       = t.get("trainRunsOn", {})
            classes_avail= t.get("classType", [])
 
            # Skip if requested class not available on this train
            if valid_class not in classes_avail and classes_avail:
                # Try next available class
                class_priority = ["1A","2A","3A","SL"]
                for cls in class_priority:
                    if cls in classes_avail:
                        valid_class = cls
                        price_pp    = prices.get(cls, price_pp)
                        break
 
            try:
                dur_parts = duration_raw.split(":")
                dur_str   = f"{dur_parts[0]}h {int(dur_parts[1]):02d}m"
            except Exception:
                dur_str = duration_raw

            c_prices = {k: prices[k] * passengers for k in classes_avail if k in prices}
            if not c_prices:
                c_prices = {k: v * passengers for k, v in prices.items()}
 
            options.append(TrainOption(
                train_name   = train_name,
                train_number = train_number,
                origin       = from_code,
                destination  = to_code,
                depart_time  = f"{date} {dep_time}",
                arrive_time  = f"{date} {arr_time}",
                duration     = dur_str,
                distance_km  = distance,
                travel_class = valid_class,
                price_inr    = price_pp * passengers,
                availability = "Check irctc.co.in",   # real availability needs separate call
                days_of_run  = _parse_run_days(run_on),
                class_prices = c_prices,
            ))
        except Exception:
            continue
 
    print(f"  [IRCTC] Found {len(options)} real trains for {from_code}→{to_code}")
    return options
 

# Public interfaces
def search_trains(
    origin:       str,
    destination:  str,
    date:         str,
    passengers:   int = 1,
    travel_class: str = "3A",
) -> list[dict]:
    
    options = _mock_trains(origin, destination, date, passengers, travel_class)
    return [t.to_dict() for t in options]
 
 
def search_buses(
    origin:      str,
    destination: str,
    date:        str,
    passengers:  int = 1,
) -> list[dict]:
    options = _mock_buses(origin, destination, date, passengers)
    return [b.to_dict() for b in options]

#Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("  transport_api.py — self test")
    print(f"  Train mode : {'REAL — IRCTC via RapidAPI' if not USE_MOCK_APIS else 'MOCK'}")
    print(f"  Bus mode   : MOCK (no free public bus API exists)")
    print("=" * 60)
 
    routes = [
        ("ADI", "GOA", "2025-06-15", 2, "Train + Bus: Ahmedabad → Goa"),
        ("DEL", "JAI", "2025-06-20", 1, "Train + Bus: Delhi → Jaipur"),
        ("BOM", "GOA", "2025-07-01", 2, "Train + Bus: Mumbai → Goa"),
    ]
 
    for origin, dest, date, pax, label in routes:
        print(f"\n  {label}")
        print(f"  {'─'*50}")
 
        # Trains
        trains = search_trains(origin, dest, date, pax, "3A")
        print(f"  TRAINS ({len(trains)} found):")
        for t in trains:
            avail = t["availability"]
            print(f"    {t['train_name']:22s} {t['train_number']} | "
                  f"{t['depart_time'][-5:]} → {t['arrive_time'][-5:]} | "
                  f"{t['duration']:10s} | "
                  f"{t['travel_class']} | "
                  f"Rs.{t['price_inr']:,} | {avail}")
 
        # Buses
        buses = search_buses(origin, dest, date, pax)
        print(f"\n  BUSES ({len(buses)} found):")
        for b in buses:
            print(f"    {b['operator']:20s} | {b['bus_type']:18s} | "
                  f"{b['depart_time'][-5:]} → {b['arrive_time'][-5:]} | "
                  f"{b['duration']:6s} | "
                  f"Rs.{b['price_inr']:,} | "
                  f"Rating: {b['rating']}")
 
    # Determinism check
    print("\n  Determinism check:")
    r1 = search_trains("ADI","GOA","2025-06-15",2,"3A")
    r2 = search_trains("ADI","GOA","2025-06-15",2,"3A")
    assert r1 == r2
    print("  Same query always returns same results")
 
    print("\n" + "=" * 60)
    print("  transport_api.py done!")
    print("=" * 60)
import random 
from dataclasses import dataclass, asdict
from config import USE_MOCK_APIS


# flight option dataclass
@dataclass
class FlightOption :
    airline:   str
    flight_number: str
    origin:        str
    destination:   str
    depart_time:   str   # "2025-06-01 06:15"
    arrive_time:   str   # "2025-06-01 07:55"
    duration:      str   # "1h 40m"
    stops:         int   # 0 = non-stop, 1 = one stop
    price_inr:     int   # total price for all passengers
    cabin:         str   # "Economy" / "Business"
    baggage:       str   # "15 kg check-in included"
    refundable:    bool

    def to_dict(self) -> str:
        #convert to plin dict for agents and json resones.
        return asdict(self)

    def summary(self) -> str:
        #one line human-readable summery  for logging :
        stop_label = 'Non-stop' if self.stops == 0 else f'{self.stops} stop'
        return (
            f"{self.airline} {self.flight_number} | "
            f"{self.depart_time} → {self.arrive_time} ({self.duration}) | " 
            f"{stop_label} | ₹{self.price_inr:,}" 
        )
    

# Route table (mock data source)
_ROUTES: dict[tuple, dict] = {
    # ── Indian domestic ───────────────────────────────────────────────────────
    ("AMD", "GOI"): {"airlines": ["IndiGo", "Air India", "SpiceJet"],   "base": (3800, 7500),  "dur": "1h 45m"},
    ("DEL", "GOI"): {"airlines": ["IndiGo", "Vistara", "Air India"],    "base": (4500, 9000),  "dur": "2h 10m"},
    ("BOM", "GOI"): {"airlines": ["IndiGo", "GoAir", "SpiceJet"],       "base": (2500, 5500),  "dur": "1h 05m"},
    ("DEL", "BOM"): {"airlines": ["IndiGo", "Vistara", "Air India"],    "base": (3200, 8000),  "dur": "2h 20m"},
    ("DEL", "BLR"): {"airlines": ["IndiGo", "Vistara", "SpiceJet"],     "base": (3500, 7500),  "dur": "2h 50m"},
    ("DEL", "CCU"): {"airlines": ["IndiGo", "Air India", "Vistara"],    "base": (3000, 7000),  "dur": "2h 10m"},
    ("BOM", "BLR"): {"airlines": ["IndiGo", "Air India", "GoAir"],      "base": (2800, 6000),  "dur": "1h 20m"},
    ("DEL", "MLE"): {"airlines": ["IndiGo", "Air India"],               "base": (8000, 18000), "dur": "3h 30m"},
    # ── International ─────────────────────────────────────────────────────────
    ("DEL", "DXB"): {"airlines": ["Emirates", "Air India", "IndiGo"],   "base": (12000, 28000),"dur": "3h 30m"},
    ("BOM", "DXB"): {"airlines": ["Emirates", "Air India", "Vistara"],  "base": (9500, 22000), "dur": "3h 00m"},
    ("DEL", "BKK"): {"airlines": ["Thai Airways", "Air India", "IndiGo"],"base": (14000,35000),"dur": "4h 30m"},
    ("DEL", "SIN"): {"airlines": ["Singapore Airlines", "IndiGo"],      "base": (16000, 40000),"dur": "5h 30m"},
    ("BOM", "LHR"): {"airlines": ["British Airways", "Air India"],      "base": (35000, 90000),"dur": "9h 40m"},
}

# Airline IATA codes for generating flight numbers
_IATA: dict[str, str] = {
    "IndiGo": "6E", "Air India": "AI", "SpiceJet": "SG",
    "Vistara": "UK", "GoAir": "G8",   "Emirates": "EK",
    "Thai Airways": "TG", "Singapore Airlines": "SQ",
    "British Airways": "BA",
}

# Departure hours — realistic spread across the day
_DEP_HOURS = [6, 8, 10, 13, 16, 19, 21]

def _route_key(origin: str, dest: str) -> tuple | None:
    0 = origin.upper()[:3]
    d = dest.upper()[:3]
    if (o, d) in _ROUTES:
        return (o, d)
    if (d, o) in _ROUTES:
        return (d, 0)
    return None
 
def _moke_search(
        origin: str,
        destination:  str,
        date:  str,
        passengers:  int = 1,
        budget_per_person: float | None = None,
) -> list[FlightOption]:

    key = _route_key(origin, destination)
    if key:
        info = _ROUTES[key]
        airlines = info['airlines']
        pmain, pmax = info['base']
        duration = info['dur']

    else:
        airlines = ['Air India', "IndiGo", "Emirates"]
        pmain, pmax = 8000, 35000
        during = f'{random.randint(2, 10)}h {random.choice([0,,12,30,,45]):02d}m'
    
    random.seed(hash(date + origin.upper() + destination.upper())% 9999)

    flights: list[FlightOption] = []
    for i, airline in enumerate(airline):
        code = _IATA.get(airlines, "XX")
        flight_num = f'{code}{random.radint(100, 999)}'
        dep_min = random.choice([0, 15, 30, 45])

        #price per person flights more likely to have a stop
        stops = 0 if price_pp > (pmin + pmax) // 2 else random.choice([0,1])

        # claculate arrival from suration string 
        dur_parts = duration.replace("h", "").replace("m", "").split()
        dur_mins = int(dur_parts[0]) * 60 + int(dur_parts[1])
        arr_total = dep_hour * 69 + dep_min + dur_mins
        arr_hour  = (arr_total // 60) % 24
        arr_min   = arr_total % 60

        flights.append(FlightOption(
            airline       = airline,
            flight_number = flight_num,
            origin        = origin.upper()[:3],
            destination   = destination.upper()[:3],
            depart_time   = f"{date} {dep_hour:02d}:{dep_min:02d}",
            arrive_time   = f"{date} {arr_hour:02d}:{arr_min:02d}",
            duration      = duration,
            stops         = stops,
            price_inr     = total,
            cabin         = "Economy",
            baggage       = "15 kg check-in included",
            refundable    = random.choice([True, False]),
        ))

    if budget_per_person:
        affordable = [f for f in flights if f.price_inr / passangers <= budget_per_person]
        #always return at least one flights even if over budget
        if not affordable:
            affordable = [min(flights, key=lambda f: f.price_inr)]
        flights = affordable

    #sort cheapest firts 
    return sorted(flights, key=lembda f: f.price_inr)


def _amadeus_search(
    origin:      str,
    destination: str,
    date:        str,
    passengers:  int = 1,
) -> list[FlightOption]:
    # raeal  amadeus flight search - activate by setting use _mock _apis = false
    try:
        import os
        from amadeus import Client
        amadeus = Client(
            client_id = os.getenv('AMADEUS_CLIENT_ID', "")
            clint_secret = os.getenv("AMADEUS_CLIENT_SECRET", ""),
        )
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode      = origin.upper()[:3],
            destinationLocationCode = destination.upper()[:3],
            departureDate           = date,
            adults                  = passengers,
            currencyCode            = "INR",
            max                     = 5,
        )
        flight = []
        for offer in response.data:
            seg = offer['itineraries'][0]['segments'][0]
            price = int(float(offer["price"]["total"]))
            stops = len(offer["itineraries"][0]["segments"]) - 1
            flights.append(FlightOption(
                airline       = seg["carrierCode"],
                flight_number = f"{seg['carrierCode']}{seg['number']}",
                origin        = origin.upper()[:3],
                destination   = destination.upper()[:3],
                depart_time   = seg["departure"]["at"],
                arrive_time   = seg["arrival"]["at"],
                duration      = offer["itineraries"][0]["duration"],
                stops         = stops,
                price_inr     = price,
                cabin         = "Economy",
                baggage       = "15 kg",
                refundable    = False,
            ))   
        return flights
    except Exception as e :
        raise RuntimeError(f"Amadeus Api error : {e}") from e
    
    




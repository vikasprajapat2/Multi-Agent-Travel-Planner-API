# Travel AI - Multi-Agent Travel Planner

An AI-powered travel planning system that uses multiple specialist agents to create personalized trip itineraries, book flights and hotels, and manage budgets for Indian travelers.

## Features

✨ **Multi-Agent System**
- **FlightAgent**: Finds best flights within budget
- **TrainAgent**: Finds optimal train routes and schedules
- **BusAgent**: Provides bus transportation options
- **HotelAgent**: Recommends accommodations by area and price
- **ItineraryAgent**: Creates day-by-day activity plans
- **JourneyAgent**: Generates seamless multi-modal routing and day-by-day transport
- **BudgetAgent**: Tracks costs and manages spending
- **ContextAgent**: Provides weather, safety, and packing tips

🎯 **AI-Powered Planning**
- Natural language input: "Plan a 5-day trip to Goa under ₹30,000"
- Groq LLM integration (Llama 3.3-70B)
- Session-based conversation history
- Real-time plan generation with LLM reasoning

💰 **Budget Management**
- Automatic cost tracking
- Per-person and per-day breakdown
- Smart budget allocation across flights, hotels, activities
- Surplus/deficit alerts
- Multiple budget scenarios

🗺️ **Smart Routing**
- Flight API integration (AviationStack)
- Comprehensive Transport API for Train and Bus routing
- Hotel booking API (Booking.com via RapidAPI)
- Multi-modal transport plans including day-by-day transit
- Real destination data
- Travel time calculations

🔄 **Plan Management & Versioning**
- Create initial plan from natural language input
- Select preferred transport mode (Flight, Train, Bus) *after* generation
- Modify existing plans with `/replan` endpoint
- Compare multiple plan versions side-by-side
- Label and track different plan iterations
- Export plans as formatted text for sharing

🔐 **Session Management**
- Persistent user sessions with conversation history
- Multi-version plan storage within sessions
- Automatic session timeout (configurable TTL)
- Session health monitoring via `/health` endpoint

📤 **Plan Export & Sharing**
- Export formatted travel itineraries as plain text
- Share via WhatsApp, email, or notes
- Structured output with flights, hotels, daily schedules, and budget breakdown

## Screenshots

### 1. Trip Planning Interface
The main dashboard where users input their travel preferences:
- Destination selection
- Origin city
- Budget allocation
- Trip duration
- Travel type (solo, couple, family, group)
- Interest selection

![Trip Planning](./screenshot/Screenshot%202026-04-03%20110209.png)

### 2. Context & Safety Information
Comprehensive travel context with weather, safety tips, and local insights:
- Current weather conditions
- Safety recommendations
- Must-try local food with pricing
- Local events and festivals
- Packing essentials
- Insider travel tips

![Context Info](./screenshot/Screenshot%202026-04-03%20110458.png)

### 3. Generated Trip Overview
Complete trip summary showing all details:
- Destination and dates
- Duration and passenger count
- Travel type
- Total cost overview
- Tabs for Flights, Itinerary, Budget, Context, and Chat

### 4. Budget Breakdown
Detailed budget analysis with cost allocation:
- Total cost vs. allocated budget
- Per-day spending analysis
- Per-person cost calculation
- Cost breakdown by category (flights, hotels, activities)
- Visual representation of expense distribution
- Budget status (within/over budget)

![Budget Breakdown](./screenshot/Screenshot%202026-04-03%20110440.png)

### 5. Day-by-Day Itinerary
Detailed daily activities and schedule:
- Highlights for the trip
- Travel tips and logistics
- Daily breakdown with timings
- Activity descriptions and hints
- Meal recommendations
- Cost per activity

![Itinerary](./screenshot/Screenshot%202026-04-03%20110405.png)

### 6. Flexible Transport & Hotel Recommendations
Smart recommendations for transportation and accommodation:
- **Post-Generation Choice**: Flexibly choose between Train, Flight, and Bus options *after* the initial plan is generated.
- Recommended flights, trains, and buses with duration and amenities
- Recommended hotels with ratings
- Room prices and total cost
- Amenities and facilities
- Value indicators ("best price available", "best rated option within budget")

![Flights & Hotels](./screenshot/Screenshot%202026-04-03%20110330.png)

## Prerequisites

- Python 3.10+
- Virtual environment manager (venv/conda)
- API Keys:
  - `GROQ_API_KEY` - [Get from Groq](https://console.groq.com)
  - `AVIATIONSTACK_API_KEY` - [Get from AviationStack](https://aviationstack.com)
  - `RAPIDAPI_KEY` - [Get from RapidAPI](https://rapidapi.com)

## Installation

### 1. Clone & Setup

```bash
cd d:\travel-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in project root:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
ORCHESTRATOR_MODEL=llama-3.3-70b-versatile

AVIATIONSTACK_API_KEY=your_aviation_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=booking-com15.p.rapidapi.com

USE_MOCK_APIS=false
DEFAULT_CURRENCY=INR
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 4. Start Server

```bash
python main.py
```

Server runs at `http://localhost:8000`

## Quick Start with UI

Run both the backend and frontend in separate terminals:

**Terminal 1 — FastAPI backend (keep this running)**
```bash
cd D:\travel-ai
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — Streamlit UI**
```bash
cd D:\travel-ai
.venv\Scripts\python.exe -m streamlit run ui\app.py
```

Then open **http://localhost:8501** in your browser.

### What You'll See

```
✈️ AI Travel Planner
─────────────────────────────────────────
[Sidebar]                [Main area]
Destination: Goa         💬 Chat input
From: Ahmedabad          (for custom queries)
Budget: ₹30,000          
Days: 5                  💡 Example queries:
Type: couple             • 5-day Goa trip
Interests: beach,food    • Kerala family 7d
                         • Solo Manali 6d
[🗺️ Plan My Trip] ← Click this!
```

**Two ways to generate a plan:**

1. **Quick Form (Recommended):**
   - Fill destination, budget, travel type in sidebar
   - Click "🗺️ Plan My Trip"
   - No manual typing needed!

2. **Custom Query:**
   - Type a query in the chat input
   - Or click an example below the chat input
   - "5-day Goa trip for couple under ₹30,000"

| Tab | Shows |
|---|---|
| ✈️ Flights & Hotel | Recommended flight + hotel with alternatives |
| 🚌 Transport | Train & bus options + recommendations |
| 📍 Itinerary | Day-by-day expandable schedule with meals |
| 💰 Budget | Progress bars per category + money tips |
| 🌦️ Context | Weather, food, safety, etiquette, packing |
| 💬 Chat | Full conversation history + plan comparison |

## API Endpoints

### Session Management

**Create Session**
```bash
POST /session
```
Response: `{ "session_id": "abc123..." }`

**Get Session Health**
```bash
GET /health
```
Response: `{ "status": "ok", "active_sessions": 5 }`

### Trip Planning

**Generate Travel Plan**
```bash
POST /plan
Content-Type: application/json

{
  "query": "Plan a 5 day trip to Goa from Ahmedabad under 30000 for couple",
  "session_id": "abc123..." (optional)
}
```
Response: Complete trip plan with flights, hotels, itinerary, budget, context

**Update Existing Plan**
```bash
POST /replan
Content-Type: application/json

{
  "session_id": "abc123...",
  "change": "reduce budget to ₹20,000",
  "label": "Budget Variant" (optional)
}
```

**Get Latest Plan**
```bash
GET /plan/{session_id}
```

**Compare Plan Versions**
```bash
GET /compare/{session_id}
```

**Export Plan as Text**
```bash
GET /export/{session_id}
```

### History

**Get Chat History**
```bash
GET /history/{session_id}
```

## Usage Examples

### PowerShell

```powershell
# Create session
$session = Invoke-RestMethod -Uri "http://localhost:8000/session" -Method POST
$sid = $session.session_id

# Generate plan
$body = @{ 
  query = "5 day Goa trip 30k couple loves beach and food"
  session_id = $sid
} | ConvertTo-Json

$plan = Invoke-RestMethod -Uri "http://localhost:8000/plan" -Method POST `
  -Body $body -ContentType "application/json"

Write-Host "Trip: $($plan.plan.trip_title)"
Write-Host "Cost: ₹$($plan.plan.budget.total_cost)"
```

### cURL

```bash
# Create session
SESSION=$(curl -X POST http://localhost:8000/session | jq -r '.session_id')

# Generate plan
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{
    "query": "5 day Goa trip under 30000 for couple",
    "session_id": "'$SESSION'"
  }'
```

### Python

```python
import requests

# Create session
session = requests.post("http://localhost:8000/session").json()
sid = session["session_id"]

# Generate plan
plan = requests.post(
    "http://localhost:8000/plan",
    json={
        "query": "Plan a trip to Goa for 5 days, ₹30,000 budget",
        "session_id": sid
    }
).json()

print(f"Trip: {plan['plan']['trip_title']}")
print(f"Cost: ₹{plan['plan']['budget']['total_cost']:,}")
```

## Advanced Features

### Plan Comparison & Versioning

Create multiple plan variations and compare them:

```python
import requests

sid = "your_session_id"

# Original plan
plan1 = requests.post("http://localhost:8000/plan", json={
    "query": "5-day Goa trip, ₹30,000 budget, couple",
    "session_id": sid
}).json()

# Budget variant
replan = requests.post("http://localhost:8000/replan", json={
    "session_id": sid,
    "change": "reduce budget to ₹15,000",
    "label": "Budget Variant"
}).json()

# Luxury variant
replan_lux = requests.post("http://localhost:8000/replan", json={
    "session_id": sid,
    "change": "increase budget to ₹75,000, add premium hotels",
    "label": "Luxury Variant"
}).json()

# Compare all versions
comparison = requests.get(f"http://localhost:8000/compare/{sid}").json()
print("All plan versions:")
for version in comparison:
    print(f"  {version['label']} - ₹{version['total_cost']:,}")
```

### Export Plans for Sharing

Export your travel itinerary as formatted text for sharing via WhatsApp, email, or notes:

```python
import requests

sid = "your_session_id"

# Export plan as text
export = requests.get(f"http://localhost:8000/export/{sid}").json()

# Print formatted itinerary
print(export["text"])

# Or save to file
with open("my_trip.txt", "w") as f:
    f.write(export["text"])
```

**Sample Export Output:**
```
==================================================
  GOA ADVENTURE - 5 DAYS
==================================================
Destination : Goa
From        : Ahmedabad
Duration    : 5 days
Dates       : 2026-04-20 to 2026-04-25
Travel type : Couple

✈  FLIGHT
   SpiceJet SG7312 | 09:00 → 11:30 | ₹8,500

🏨  HOTEL
   Taj Holiday Village ★★★★ | Calangute | ₹4,500/night

📍  ITINERARY

  Day 1: Arrival & Beach
   09:00  Check-in to hotel — Calangute Beach
   11:30  Beach time & relaxation — Calangute Beach
   Lunch : Seafood thali at Florentine
   Dinner: Dinner cruise

💰  BUDGET
   Flights            ₹8,500
   Hotel              ₹22,500
   Activities         ₹9,200
   Meals              ₹5,800
   ─────────────────────────────
   Total              ₹46,000
   Budget             ₹30,000
```

### Get Session History

Retrieve chat history and plan versions:

```python
import requests

sid = "your_session_id"

history = requests.get(f"http://localhost:8000/history/{sid}").json()
print(f"Chat messages: {len(history['messages'])}")
print(f"Plan versions: {history['plan_count']}")
```

## Project Structure

```
D:\travel-ai\
├── config.py              Part 1 ✅
├── llm_client.py          Part 1 ✅
├── main.py                Part 6 ✅
├── requirements.txt
├── .env                   (API keys - not in git)
├── .env.example
│
├── agents/
│   ├── planner.py         Part 5 ✅
│   ├── fllight_agent.py   Part 4 ✅
│   ├── train_agent.py     Part 4 ✅
│   ├── bus_agent.py       Part 4 ✅
│   ├── hotel_agent.py     Part 4 ✅
│   ├── itinerary_agent.py Part 4 ✅
│   ├── journey_agent.py   Part 4 ✅
│   ├── budget_agent.py    Part 4 ✅
│   └── context_agent.py   Part 4 ✅
│
├── tools/
│   ├── flight_api.py      Part 3 ✅
│   ├── transport_api.py   Part 3 ✅
│   ├── hotel_api.py       Part 3 ✅
│   └── weather_api.py     Part 3 ✅
│
├── memory/
│   └── Session_store.py   Part 2 ✅
│
└── ui/
    └── app.py             Part 7 ✅
```

## Configuration

### Models

Change in `.env`:
- `llama-3.3-70b-versatile` (recommended)
- `mixtral-8x7b-32768` (no longer supported)
- Other Groq models available

### Mock Mode

Set `USE_MOCK_APIS=true` in `.env` to use simulated flight/hotel data for testing.

## API Response Structure

### Plan Response Format

Every `/plan` and `/replan` response contains:

```json
{
  "session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "plan": {
    "trip_title": "Goa Adventure - 5 Days",
    "destination": "Goa",
    "origin": "Ahmedabad",
    "duration": "5 days",
    "dates": "2026-04-20 to 2026-04-25",
    "travel_type": "couple",
    "passengers": 2,
    "flights": {
      "recommended": {...},
      "alternatives": [...],
      "round_trip_cost": 8500
    },
    "hotel": {
      "recommended": {...},
      "alternatives": [...],
      "per_night_cost": 4500
    },
    "transport": {
      "flights": [...],
      "trains": [...],
      "buses": [...]
    },
    "itinerary": {
      "highlights": [...],
      "tips": [...],
      "days": [
        {
          "day": 1,
          "title": "Arrival & Beach",
          "schedule": [...],
          "meals": {...}
        }
      ]
    },
    "budget": {
      "total_cost": 46000,
      "total_budget": 30000,
      "surplus_or_deficit": -16000,
      "breakdown": {
        "flights": {"cost": 8500},
        "hotel": {"cost": 22500},
        "activities": {"cost": 9200},
        "meals": {"cost": 5800}
      }
    },
    "context": {
      "weather": {...},
      "safety": {...},
      "local_food": [...],
      "events": [...],
      "packing_list": [...],
      "tips": [...]
    }
  }
}
```

## Testing

### Unit Test - Planner Agent

```bash
python agents/planner.py
```

Runs full end-to-end pipeline:
1. Parse natural language → Trip structure
2. Run 5 agents in parallel
3. Merge results into final plan
4. Test replan functionality
5. Compare plan versions

## Error Handling

The system gracefully handles:
- **JSON parsing failures**: Falls back to default values
- **API timeouts**: Uses mock data
- **Missing fields**: Applied safe defaults
- **Budget overflow**: Shows deficit warnings

## Performance

- **Endpoint response time**: 10-30 seconds (includes LLM calls)
- **Concurrent sessions**: Limited by Groq rate limits (500 RPM)
- **Memory usage**: ~100MB per session

## Troubleshooting

**Error: "GROQ_API_KEY not found"**
- Check `.env` file exists in project root
- Verify key is correct from [Groq Console](https://console.groq.com)

**Error: "The model is decommissioned"**
- Update model name in `.env` to `llama-3.3-70b-versatile`

**Error: "500 on /plan endpoint"**
- Check server logs for agent-specific errors
- Verify all 5 agents are importing correctly
- Try with `USE_MOCK_APIS=true` first

**Session expired or not found**
- Sessions expire after `SESSION_TTL_SECONDS` (default: 3600s/1 hour)
- Create a new session with `POST /session` if expired
- Use `/health` endpoint to check active sessions count

**Plan comparison returns empty**
- Ensure you've called `/replan` at least once after the initial `/plan`
- Check session ID is valid with `/health` endpoint

**Export endpoint returns "No plan found"**
- Verify you've successfully generated a plan first
- Check correct session ID is being used
- Ensure session hasn't expired

**API rate limiting from Groq**
- Request limit: 500 RPM (requests per minute)
- Space out requests if sending many plans in succession
- Consider using `USE_MOCK_APIS=true` for load testing

**Unicode encoding error on Windows**
- Windows CMD may have encoding issues with special characters
- Use PowerShell instead: `.venv\Scripts\Activate.ps1`
- Or set PYTHONIOENCODING: `$env:PYTHONIOENCODING="utf-8"`

## Performance Optimization

**Faster Response Times:**
- Use `USE_MOCK_APIS=true` to respond in <1 second (for testing)
- Cache session data locally to avoid repeated API calls
- Batch multiple plan requests into parallel sessions

**Monitor API Usage:**
```bash
curl http://localhost:8000/health
# Response: { "status": "ok", "active_sessions": 5 }
```

**Memory Management:**
- Sessions automatically expire after 1 hour of inactivity
- Manually delete old sessions if needed
- Each session uses ~100MB of memory

## Development

### Add New Agent

1. Create file: `agents/new_agent.py`
2. Implement `run(request: TravelRequest) -> dict`
3. Import in `planner.py`
4. Add to `__init__`: `self.new_agent = NewAgent()`

### Modify System Prompts

Edit system prompts at top of each agent file to customize behavior.

## Real-World Use Cases & Workflows

### Use Case 1: Family Planning with Budget Variants

A family wants to explore 3 different budget options for a Kerala trip:

```python
import requests

# Session for the family
sid = requests.post("http://localhost:8000/session").json()["session_id"]

# Budget option 1: Economical
budget1 = requests.post("http://localhost:8000/plan", json={
    "query": "7-day Kerala family trip, 4 people, ₹60,000 total budget",
    "session_id": sid
}).json()

# Budget option 2: Mid-range (replan)
budget2 = requests.post("http://localhost:8000/replan", json={
    "session_id": sid,
    "change": "upgrade to mid-range hotels and add premium activities",
    "label": "Mid-Range Option"
}).json()

# Budget option 3: Luxury (replan)
budget3 = requests.post("http://localhost:8000/replan", json={
    "session_id": sid,
    "change": "luxury resort stay with water sports and spa services",
    "label": "Luxury Option"
}).json()

# Compare all three
comparison = requests.get(f"http://localhost:8000/compare/{sid}").json()
# Family can now easily compare costs and features of each option
```

### Use Case 2: Transport Mode Selection

A solo traveler wants to explore different travel modes:

```python
import requests

sid = requests.post("http://localhost:8000/session").json()["session_id"]

# Initial plan
plan = requests.post("http://localhost:8000/plan", json={
    "query": "5-day Manali trip solo traveler ₹25,000",
    "session_id": sid
}).json()

# Compare travel modes by replanning
flight_plan = requests.post("http://localhost:8000/replan", json={
    "session_id": sid,
    "change": "prioritize flights over train",
    "label": "Fastest (Flight)"
}).json()

train_plan = requests.post("http://localhost:8000/replan", json={
    "session_id": sid,
    "change": "use train instead of flight for scenic journey",
    "label": "Scenic (Train)"
}).json()

# Now compare flight vs train journey times and costs
comparison = requests.get(f"http://localhost:8000/compare/{sid}").json()
```

### Use Case 3: Quick Sharing & Social Media

Generate a plan and instantly share with friends:

```python
import requests

# Generate plan
sid = requests.post("http://localhost:8000/session").json()["session_id"]
plan = requests.post("http://localhost:8000/plan", json={
    "query": "Girls trip to Jaipur 4 days ₹40,000"
}).json()

# Export as shareable text
export = requests.get(f"http://localhost:8000/export/{sid}").json()

# Share via WhatsApp, email, or posts
itinerary_text = export["text"]
# Paste directly into WhatsApp group chat
```

## License

MIT

## Support

For issues and questions:
1. Check [Groq Docs](https://console.groq.com/docs)
2. Review agent-specific logs
3. Test with mock APIs enabled
4. Review the [API Examples](#advanced-features) section

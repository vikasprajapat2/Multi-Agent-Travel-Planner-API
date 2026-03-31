import time 
from dataclasses import dataclass, asdict
from typing import Any
import uuid
from config import SESSION_TTL_SECONDS, TravelRequest

@dataclass
class PlanVersion:
    """One saved snapshot of a travel plane """

    version_id: str  # short unique ID like "a3f8b2c1"
    label: str # human-readable: "budget plan", 'Luxury plan
    created_at: float # unix timestamp - time()
    request : dict # travelRequest converted to dict via asdict()
    result : dict # full plan output form plannerAgent
    total_cost: float # extracted from result['budget"]["total_cost"]

class SessionStore:
    _store: dict[str, dict] = {}

    @classmethod
    def create(cls) -> str:
        session_id = str(uuid.uuid4())

        cls._store[session_id] = {
            'created_at': time.time(),
            'updated_at': time.time(),
            'messages': [],
            'request': None,
            'plan_result': None,
            'plan_versions': [],
            'preferences': {},
        }

        return session_id
    
    @classmethod
    def get(cls, session_id: str)-> dict | None:
        data = cls._store.get(session_id)
        if data is None:
            return None
        
     # TTL check — has the session been idle for too long?
        idle_seconds = time.time() - data['updated_at']
        if idle_seconds > SESSION_TTL_SECONDS:
        # Clean up expired session to free memory
            del cls._store[session_id]
            return None

        return data
    
    @classmethod
    def touch(cls, session_id: str) -> None:
        if session_id in cls._store:
            cls._store[session_id]["updated_at"] = time.time()

    @classmethod
    def delete(cls, session_id: str)-> None:
        cls._store.pop(session_id, None)

    @classmethod
    def active_count(cls) -> int:
        now = time.time()
        return sum(
            1 for s in cls._store.values()
            if now - s["updated_at"] <= SESSION_TTL_SECONDS
        )
    
    # CONVERSATION HISTORY
    @classmethod
    def add_message(cls, session_id: str, role: str, content: str) -> None:
        session = cls.get(session_id)
        if not session:
            return
    
        session['messages'].append({
            'role': role,
            'content': content,
            'timestamp': time.time(),
        })

        cls.touch(session_id)

    @classmethod
    def get_messages(cls, session_id: str) -> list[dict]:
        '''return full convertion history for a session'''
        session = cls.get(session_id)
        return session['messages'] if session else []
    

    @classmethod
    def clear_messages(cls, session_id: str) -> None:
        #clear convertion hisory but keep the session alive
        session = cls.get(session_id)
        if session:
            session['messages'] = []
            cls.touch(session_id)

    #plane storage
    @classmethod
    def save_plan(
        cls,
        session_id: str,
        request: TravelRequest,
        result: dict,
        label: str = '',
    ) -> str:
        
        session = cls.get(session_id)
        if not session:
            return ''
        
        version_id =  str(uuid.uuid4())[:8]

        if not label:
            n = len(session['plan_versions']) + 1
            label = f'plan v {n}'

        total_cost = result.get('budget', {}).get('total_cost', 0) or 0 

        version = PlanVersion(
            version_id = version_id,
            label      = label,
            created_at = time.time(),
            request    = asdict(request),   # TravelRequest → plain dict
            result     = result,
            total_cost = float(total_cost),
        )       
        
        #append version history 
        session['plan_versions'].append(version)

        # also update the lestest pointer for quick access
        session['plan_result'] = result
        session['request'] = asdict(request)

        cls.touch(session_id)
        return version_id

    @classmethod
    def get_latest_plan(cls, session_id:str) -> dict| None:
        # return the most recently generated plan , or None 
        session = cls.get(session_id)
        return session['plan_result'] if session else None
    
    @classmethod
    def get_latest_request(cls, session_id: str) -> dict | None:
        # return the most recently saved TravelRequest (as dict)
        session = cls.get(session_id)
        return session['request'] if session else None
    
    @classmethod
    def get_plan_versions(cls, session_id: str) -> list[PlanVersion]:
        #return all save plan versions for a session 
        # used by the compare plan feature in the streamlit UI

        session = cls.get(session_id)
        return session['plan_versions'] if session else []
    
    @classmethod
    def update_preferences(cls, session_id:str, prefs: dict) -> None:
        session = cls.get(session_id)
        if session:
            session['preferences'].update(prefs)
            cls.touch(session_id)

    @classmethod
    def get_preferences(cls, session_id: str) -> dict:
        # return all stored user preferences for a session 
        session = cls.get(session_id)
        return session['preferences'] if session else {}
    

if __name__ == "__main__":
    print("=" * 55)
    print("  session_store.py — self test")
    print("=" * 55)
 
    # ── Test 1: Create a session ──────────────────────────────────────────────
    print("\n[Test 1]  Create a session")
    sid = SessionStore.create()
    print(f"  session_id : {sid}")
    print(f"  active sessions : {SessionStore.active_count()}")
    assert SessionStore.get(sid) is not None, "Session should exist"
    print("  Session created and retrieved")
 
    # ── Test 2: Add messages ──────────────────────────────────────────────────
    print("\n[Test 2]  Add conversation messages")
    SessionStore.add_message(sid, "user",      "Plan a 5-day trip to Goa under ₹30,000")
    SessionStore.add_message(sid, "assistant", "Planning your Goa trip...")
    SessionStore.add_message(sid, "assistant", "Plan ready! Here is your itinerary.")
 
    messages = SessionStore.get_messages(sid)
    print(f"  Stored {len(messages)} messages:")
    for m in messages:
        ts = time.strftime("%H:%M:%S", time.localtime(m["timestamp"]))
        print(f"    [{ts}] {m['role']:10s} → {m['content'][:50]}")
    assert len(messages) == 3
    print("  Messages stored and retrieved correctly")
 
    # ── Test 3: Save a plan (v1 — budget trip) ────────────────────────────────
    print("\n[Test 3]  Save plan version 1 (budget trip)")
 
    req_v1 = TravelRequest(
        destination   = "Goa",
        origin        = "Ahmedabad",
        budget        = 30000,
        duration_days = 5,
        travel_type   = "couple",
        preferences   = ["beach", "food"],
        passengers    = 2,
    )
 
    # Simulate a plan result (normally produced by PlannerAgent)
    plan_v1 = {
        "trip_title": "Goa 5-Day Couple Trip",
        "destination": "Goa",
        "budget": {
            "total_cost": 27500,
            "total_budget": 30000,
            "surplus_or_deficit": 2500,
            "status": "within_budget",
        },
    }
 
    vid1 = SessionStore.save_plan(sid, req_v1, plan_v1, label="Budget Plan")
    print(f"  version_id : {vid1}")
    print(f"  label      : Budget Plan")
    print(f"  total_cost : ₹{plan_v1['budget']['total_cost']:,}")
    assert SessionStore.get_latest_plan(sid) == plan_v1
    print("  Plan v1 saved and retrieved")
 
    # ── Test 4: Save plan v2 (luxury upgrade) ─────────────────────────────────
    print("\n[Test 4]  Save plan version 2 (luxury upgrade)")
 
    req_v2 = TravelRequest(
        destination   = "Goa",
        origin        = "Ahmedabad",
        budget        = 80000,
        duration_days = 5,
        travel_type   = "couple",
        preferences   = ["beach", "luxury"],
        passengers    = 2,
    )
    plan_v2 = {
        "trip_title": "Goa 5-Day Luxury Couple Trip",
        "destination": "Goa",
        "budget": {
            "total_cost": 74000,
            "total_budget": 80000,
            "surplus_or_deficit": 6000,
            "status": "within_budget",
        },
    }
 
    vid2 = SessionStore.save_plan(sid, req_v2, plan_v2, label="Luxury Plan")
    print(f"  version_id : {vid2}")
    assert vid1 != vid2, "Version IDs must be unique"
    print(" Plan v2 saved with different version_id")
 
    # ── Test 5: Compare plan versions ─────────────────────────────────────────
    print("\n[Test 5]  Compare plan versions")
    versions = SessionStore.get_plan_versions(sid)
    print(f"  Found {len(versions)} plan versions:")
    for v in versions:
        ts = time.strftime("%H:%M:%S", time.localtime(v.created_at))
        print(f"    [{ts}] {v.version_id}  {v.label:15s}  ₹{v.total_cost:,.0f}")
    assert len(versions) == 2
    print("  Both versions returned for comparison")
 
    # ── Test 6: User preferences ──────────────────────────────────────────────
    print("\n[Test 6]  User preferences")
    SessionStore.update_preferences(sid, {"home_city": "Ahmedabad", "currency": "INR"})
    SessionStore.update_preferences(sid, {"last_destination": "Goa"})   # second call merges
    prefs = SessionStore.get_preferences(sid)
    print(f"  Stored preferences: {prefs}")
    assert prefs["home_city"] == "Ahmedabad"
    assert prefs["last_destination"] == "Goa"
    assert "currency" in prefs        # first call's data still there
    print("  Preferences merged across two update() calls")
 
    # ── Test 7: Session expiry ────────────────────────────────────────────────
    print("\n[Test 7]  TTL expiry simulation")
    expired_sid = SessionStore.create()
 
    # Manually backdate updated_at to simulate an idle session
    SessionStore._store[expired_sid]["updated_at"] -= (SESSION_TTL_SECONDS + 10)
    result = SessionStore.get(expired_sid)
 
    print(f"  Expired session returns: {result}")
    assert result is None, "Expired session should return None"
    assert expired_sid not in SessionStore._store, "Expired session should be cleaned up"
    print(" Expired session correctly returned None and was cleaned up")
 
    # ── Test 8: get_latest_request() — for re-planning ────────────────────────
    print("\n[Test 8]  get_latest_request() — for re-planning")
    latest_req = SessionStore.get_latest_request(sid)
    print(f"  Latest request: destination={latest_req['destination']}, budget={latest_req['budget']}")
    assert latest_req["destination"] == "Goa"
    assert latest_req["budget"] == 80000    # should be v2 (latest)
    print(" Returns the most recent TravelRequest for re-planning")
 
    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  Part 2 complete — all 8 tests passed!")
    print()
    print("  You now have:")
    print("    PlanVersion dataclass   — snapshot of one plan")
    print("    SessionStore.create()   — start a new session")
    print("    SessionStore.add_message()  — conversation history")
    print("    SessionStore.save_plan()    — plan versioning")
    print("    SessionStore.get_plan_versions() — compare plans")
    print("    SessionStore.update_preferences() — user memory")
    print("    TTL expiry — sessions auto-clean after 1 hour")
    print()
    print("  Next → Part 3: Mock tools (flight, hotel, weather APIs)")
    print("  Say 'Part 3' to continue.")
    print("=" * 55)
 
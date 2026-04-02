

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json
import time

# Page config + styling

st.set_page_config(
    page_title = "AI Travel Planner",
    page_icon  = "✈️",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

st.markdown("""
<style>
.metric-box {
    background: var(--background-color);
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
}
.day-card {
    border-left: 3px solid #4f7cff;
    padding-left: 1rem;
    margin: 0.75rem 0;
}
.tip-box {
    background: rgba(255,193,7,0.1);
    border-left: 3px solid #ffc107;
    padding: 0.5rem 0.75rem;
    border-radius: 0 6px 6px 0;
    margin: 0.3rem 0;
    font-size: 0.88rem;
}
.status-ok  { color: #16a34a; font-weight: 600; }
.status-bad { color: #dc2626; font-weight: 600; }
.status-tight { color: #d97706; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


#  Session state + API config


API_BASE = "http://localhost:8000"

if "session_id"     not in st.session_state: st.session_state.session_id     = None
if "plan"           not in st.session_state: st.session_state.plan           = None
if "chat_history"   not in st.session_state: st.session_state.chat_history   = []
if "plan_versions"  not in st.session_state: st.session_state.plan_versions  = []
if "is_loading"     not in st.session_state: st.session_state.is_loading     = False


#API helpers


def api_create_session() -> str | None:
    """Create a new session via FastAPI. Returns session_id or None."""
    try:
        r = requests.post(f"{API_BASE}/session", timeout=5)
        if r.status_code == 200:
            return r.json()["session_id"]
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure FastAPI is running:\n"
                 "`.venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000`")
    return None


def api_plan(query: str, session_id: str) -> dict | None:
    """Call POST /plan. Returns plan dict or None on failure."""
    try:
        r = requests.post(
            f"{API_BASE}/plan",
            json    = {"query": query, "session_id": session_id},
            timeout = 120,   # agents take 20-40 seconds
        )
        if r.status_code == 200:
            return r.json().get("plan")
        st.error(f"API error {r.status_code}: {r.json().get('detail','Unknown error')}")
    except requests.exceptions.ConnectionError:
        st.error("Lost connection to API server.")
    except requests.exceptions.Timeout:
        st.error(" Request timed out. The agents are taking too long — try again.")
    return None


def api_replan(session_id: str, change: str) -> dict | None:
    """Call POST /replan. Returns updated plan dict or None."""
    try:
        r = requests.post(
            f"{API_BASE}/replan",
            json    = {"session_id": session_id, "change": change},
            timeout = 120,
        )
        if r.status_code == 200:
            return r.json().get("plan")
        st.error(f"Re-plan failed: {r.json().get('detail','')}")
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def api_export(session_id: str) -> str:
    """Call GET /export/{session_id}. Returns plain text."""
    try:
        r = requests.get(f"{API_BASE}/export/{session_id}", timeout=10)
        if r.status_code == 200:
            return r.json().get("text", "")
    except Exception:
        pass
    return ""


def ensure_session():
    """Create a session if we don't have one yet."""
    if not st.session_state.session_id:
        sid = api_create_session()
        if sid:
            st.session_state.session_id = sid


def fmt_inr(val) -> str:
    """Format a number as Indian Rupees."""
    try:
        return f"₹{int(val):,}"
    except (TypeError, ValueError):
        return "₹0"

#  Sidebar

with st.sidebar:
    st.markdown("##Travel Planner")
    st.markdown("---")

    # ── Quick fill form ───────────────────────────────────────────────────────
    st.markdown("### Plan a Trip")
    destination  = st.text_input("Destination",    "Goa")
    origin       = st.text_input("From city",      "Ahmedabad")
    budget       = st.number_input("Budget (₹)",   min_value=5000,
                                   max_value=500000, value=30000, step=1000)
    days         = st.slider("Duration (days)",    2, 21, 5)
    travel_type  = st.selectbox("Travel type",
                                ["couple","solo","family","honeymoon","group"])
    prefs        = st.multiselect("Interests",
                                  ["beach","adventure","food","culture",
                                   "luxury","nature","shopping","spiritual"])

    if st.button("Plan My Trip", use_container_width=True, type="primary"):
        pref_str = ", ".join(prefs) if prefs else ""
        query    = (
            f"Plan a {days}-day trip to {destination} from {origin} "
            f"under ₹{budget:,} for {travel_type}"
            f"{' who loves ' + pref_str if pref_str else ''}"
        )
        st.session_state._pending_query = query

    st.markdown("---")

    if st.session_state.plan:
        st.markdown("### Update Plan")
        change_input = st.text_input(
            "What to change?",
            placeholder="e.g. luxury hotel, cut budget to 20k"
        )
        if st.button("Update", use_container_width=True):
            if change_input.strip():
                st.session_state._pending_replan = change_input

        st.markdown("---")

        # Quick re-plan buttons
        st.markdown("### Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💰 Budget", use_container_width=True):
                st.session_state._pending_replan = (
                    f"reduce budget to ₹{int(budget*0.6):,} "
                    "and find cheapest options"
                )
        with col2:
            if st.button("👑 Luxury", use_container_width=True):
                st.session_state._pending_replan = (
                    f"upgrade to luxury with budget ₹{int(budget*2):,}"
                )

        st.markdown("---")

        # Export button
        if st.button("📄 Export Plan", use_container_width=True):
            ensure_session()
            text = api_export(st.session_state.session_id)
            if text:
                st.download_button(
                    label     = "⬇Download",
                    data      = text,
                    file_name = f"travel_plan_{destination.lower()}.txt",
                    mime      = "text/plain",
                )

    st.markdown("---")
    if st.button("🆕 New Trip", use_container_width=True):
        for key in ["session_id","plan","chat_history","plan_versions"]:
            st.session_state[key] = None if key != "chat_history" \
                                    and key != "plan_versions" else []
        st.rerun()


# Handle pending actions

#
# STREAMLIT CONCEPT — pending actions pattern:
#   Buttons set a flag in session_state (_pending_query, _pending_replan).
#   We check those flags at the top of the main area and process them.
#   This pattern avoids running expensive operations inside button callbacks.

if hasattr(st.session_state, "_pending_query"):
    query = st.session_state._pending_query
    del st.session_state._pending_query
    ensure_session()

    with st.spinner("🤖 Planning your trip... (20-40 seconds)"):
        plan = api_plan(query, st.session_state.session_id)

    if plan:
        st.session_state.plan = plan
        st.session_state.chat_history.append({"role":"user",    "content":query})
        st.session_state.chat_history.append({"role":"assistant",
                                               "content":f"Plan ready: {plan.get('trip_title','')}"})
        st.session_state.plan_versions.append({
            "label": plan.get("trip_title","Plan"),
            "cost":  plan.get("budget",{}).get("total_cost",0),
        })
    st.rerun()

if hasattr(st.session_state, "_pending_replan"):
    change = st.session_state._pending_replan
    del st.session_state._pending_replan
    ensure_session()

    with st.spinner(f"🔄 Updating plan: {change}..."):
        plan = api_replan(st.session_state.session_id, change)

    if plan:
        st.session_state.plan = plan
        st.session_state.chat_history.append({"role":"user",     "content":change})
        st.session_state.chat_history.append({"role":"assistant",
                                               "content":f"✅ Updated: {plan.get('trip_title','')}"})
        st.session_state.plan_versions.append({
            "label": plan.get("trip_title","Updated Plan"),
            "cost":  plan.get("budget",{}).get("total_cost",0),
        })
    st.rerun()


# PART F — Main content area

st.markdown("# AI Travel Planner")
st.caption("Multi-agent AI — flights, hotels, itinerary and budget in one go")

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input(
    "Describe your trip... e.g. '5-day Goa trip for couple under ₹30,000'"
)
if user_input:
    ensure_session()
    with st.spinner("🤖 Planning your trip... (20-40 seconds)"):
        plan = api_plan(user_input, st.session_state.session_id)
    if plan:
        st.session_state.plan = plan
        st.session_state.chat_history.append({"role":"user",     "content":user_input})
        st.session_state.chat_history.append({"role":"assistant",
                                               "content":f"✅ {plan.get('trip_title','')}"})
        st.session_state.plan_versions.append({
            "label": plan.get("trip_title","Plan"),
            "cost":  plan.get("budget",{}).get("total_cost",0),
        })
    st.rerun()


# PART G — Plan display (tabs)

if not st.session_state.plan:
    # ── No plan yet — show examples
    st.info("👆 Use the sidebar form or type a query above to plan your trip.")
    st.markdown("### 💡 Try these")
    examples = [
        "5-day Goa trip for couple under ₹30,000",
        "7-day Kerala family trip from Mumbai ₹80,000 with kids",
        "Solo Manali adventure 6 days under ₹20,000",
        "Luxury honeymoon Maldives 7 days ₹3,00,000",
        "Weekend Jaipur trip from Delhi 3 days ₹15,000",
    ]
    cols = st.columns(2)
    for i, ex in enumerate(examples):
        with cols[i % 2]:
            if st.button(ex, key=f"ex_{i}", use_container_width=True):
                ensure_session()
                st.session_state._pending_query = ex
                st.rerun()

else:
    plan = st.session_state.plan

    # ── Trip summary bar
    st.markdown(f"## {plan.get('trip_title','')}")
    st.caption(f"📅 {plan.get('dates','')}  |  "
               f"📍 {plan.get('origin','')} → {plan.get('destination','')}  |  "
               f"👥 {plan.get('passengers',2)} passengers")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Destination",  plan.get("destination",""))
    c2.metric("Duration",     plan.get("duration",""))
    c3.metric("Travel Type",  plan.get("travel_type","").title())
    c4.metric("Total Cost",   fmt_inr(plan.get("budget",{}).get("total_cost",0)))

    # ── Tabs 
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✈️ Flights & Hotel",
        "📍 Itinerary",
        "💰 Budget",
        "🌦️ Context",
        "💬 Chat",
    ])

    # ── TAB 1: Flights & Hotel 
    with tab1:
        col_f, col_h = st.columns(2)

        with col_f:
            st.markdown("#### ✈️ Recommended Flight")
            flights = plan.get("flights", {})
            rec_f   = flights.get("recommended") or {}
            if rec_f:
                stops_label = "Non-stop" if rec_f.get("stops",1)==0 else "🟡 1 stop"
                st.markdown(f"""
**{rec_f.get('airline','')}** {rec_f.get('flight_number','')}
- 🛫 {rec_f.get('depart_time','')} → {rec_f.get('arrive_time','')}
- ⏱️ {rec_f.get('duration','')} | {stops_label}
- 🧳 {rec_f.get('baggage','')}
- 💰 **{fmt_inr(flights.get('round_trip_cost',0))}** for {plan.get('passengers',2)} passengers

_{flights.get('best_deal_note','')}_
""")
                alts = flights.get("alternatives", [])
                if alts:
                    with st.expander("View alternatives"):
                        for a in alts:
                            st.markdown(
                                f"**{a.get('airline','')}** {a.get('flight_number','')} | "
                                f"{a.get('depart_time','')[-5:]} → {a.get('arrive_time','')[-5:]} | "
                                f"{fmt_inr(a.get('price_inr',0))}"
                            )
            else:
                st.info("No flight data available")

        with col_h:
            st.markdown("#### Recommended Hotel")
            hotel = plan.get("hotel", {})
            rec_h = hotel.get("recommended") or {}
            if rec_h:
                stars = "⭐" * rec_h.get("stars", 0)
                bkfst = "Breakfast included" if rec_h.get("breakfast") else "❌ No breakfast"
                amenities = ", ".join(rec_h.get("amenities", [])[:4])
                st.markdown(f"""
**{rec_h.get('name','')}** {stars}
- 📍 {rec_h.get('area','')}
- ⭐ Rating: {rec_h.get('rating','')}/10
- 🍳 {bkfst}
- 🏊 {amenities}
- 🔄 {rec_h.get('cancellation','')}
- 💰 **{fmt_inr(hotel.get('per_night_cost',0))}/night** | Total: **{fmt_inr(hotel.get('total_stay_cost',0))}**

_{hotel.get('recommendation_reason','')}_
""")
                alts_h = hotel.get("alternatives", [])
                if alts_h:
                    with st.expander("View alternatives"):
                        for h in alts_h:
                            s = "⭐" * h.get("stars",0)
                            st.markdown(
                                f"**{h.get('name','')}** {s} | "
                                f"{h.get('area','')} | "
                                f"{fmt_inr(h.get('price_per_night',0))}/night | "
                                f"Rating: {h.get('rating','')}"
                            )
            else:
                st.info("No hotel data available")

    # ── TAB 2: Itinerary ──────────────────────────────────────────────────────
    with tab2:
        itinerary = plan.get("itinerary", {})
        highlights = itinerary.get("highlights", [])
        transport  = itinerary.get("local_transport_advice", "")
        days_list  = itinerary.get("days", [])

        if highlights:
            st.markdown("**🌟 Highlights:** " +
                        " &nbsp;·&nbsp; ".join(f"`{h}`" for h in highlights))
        if transport:
            st.markdown(f"** Getting around:** {transport}")
        st.markdown("---")

        if not days_list:
            st.info("Itinerary not available.")
        else:
            for day in days_list:
                with st.expander(
                    f"Day {day['day']}: {day.get('title','')} — {day.get('theme','')}",
                    expanded=(day["day"] == 1)
                ):
                    schedule = day.get("schedule", [])
                    if schedule:
                        st.markdown("**Schedule:**")
                        for item in schedule:
                            cost = f" · {fmt_inr(item['cost_inr'])}" if item.get("cost_inr") else " · Free"
                            tip  = f"\n  > 💡 {item['tip']}" if item.get("tip") else ""
                            st.markdown(
                                f"**{item.get('time','')}** — {item.get('activity','')} "
                                f"_{item.get('location','')}_  "
                                f"`{item.get('duration','')}`{cost}{tip}"
                            )

                    meals = day.get("meals", {})
                    if any(meals.values()):
                        st.markdown("**🍽️ Meals:**")
                        for meal, desc in meals.items():
                            if desc:
                                st.markdown(f"- **{meal.title()}:** {desc}")

                    if day.get("transport"):
                        st.markdown(f"**🚌** {day['transport']}")
                    if day.get("estimated_daily_spend"):
                        st.caption(f"Est. daily spend: {fmt_inr(day['estimated_daily_spend'])}")

    # ── TAB 3: Budget ─────────────────────────────────────────────────────────
    with tab3:
        budget     = plan.get("budget", {})
        breakdown  = budget.get("breakdown", {})
        total_cost = budget.get("total_cost", 0)
        total_bgt  = budget.get("total_budget", 0)
        surplus    = budget.get("surplus_or_deficit", 0)
        status     = budget.get("status", "")

        # Summary metrics
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Total Cost",   fmt_inr(total_cost))
        b2.metric("Budget",       fmt_inr(total_bgt))
        b3.metric("Per Day",      fmt_inr(budget.get("per_day_spend",0)))
        b4.metric("Per Person",   fmt_inr(budget.get("per_person_total",0)))

        # Status badge
        if status == "within_budget":
            st.markdown(f'<p class="status-ok">✅ Within Budget  (+{fmt_inr(surplus)})</p>',
                        unsafe_allow_html=True)
        elif status == "tight":
            st.markdown(f'<p class="status-tight">⚠️ Tight Budget  (+{fmt_inr(surplus)})</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="status-bad">❌ Over Budget  ({fmt_inr(surplus)})</p>',
                        unsafe_allow_html=True)

        # Breakdown bars
        st.markdown("**Cost Breakdown:**")
        colors = {"flights":"🟦","hotel":"🟪","food":"🟨",
                  "activities":"🟩","local_transport":"🟥","shopping_misc":"⬜"}
        for cat, data in breakdown.items():
            cost = data.get("cost", 0)
            pct  = data.get("percentage", 0)
            icon = colors.get(cat, "⬜")
            label = cat.replace("_"," ").title()
            st.markdown(f"{icon} **{label}** — {fmt_inr(cost)} ({pct}%)")
            st.progress(min(pct / 100, 1.0))

        # Tips
        tips = budget.get("optimisation_tips", [])
        if tips:
            st.markdown("** Money-saving tips:**")
            for tip in tips:
                st.markdown(
                    f'<div class="tip-box"> {tip}</div>',
                    unsafe_allow_html=True
                )

        upgrade = budget.get("luxury_upgrade_cost", 0)
        if upgrade:
            st.caption(f"👑 Luxury upgrade estimated cost: {fmt_inr(upgrade)}")

    # ── TAB 4: Context ────────────────────────────────────────────────────────
    with tab4:
        ctx  = plan.get("context", {})
        cc1, cc2 = st.columns(2)

        with cc1:
            st.markdown("**🌤️ Weather**")
            st.markdown(f"""
- 🌡️ Temperature: **{ctx.get('temperature','')}**
- ☁️ {ctx.get('condition','')}
- 📅 Season: {ctx.get('season','').title()}
- ✅ {ctx.get('travel_advice','')}
""")
            dishes = ctx.get("local_dishes", [])
            if dishes:
                st.markdown("**🍛 Must-try food**")
                for d in dishes:
                    if isinstance(d, dict):
                        st.markdown(
                            f"- **{d.get('dish','')}** at _{d.get('where','')}_  "
                            f"`{d.get('price_range','')}`"
                        )
                    else:
                        st.markdown(f"- {d}")

            insider = ctx.get("insider_tip","")
            if insider:
                st.markdown(
                    f'<div class="tip-box">💰 <strong>Insider tip:</strong> {insider}</div>',
                    unsafe_allow_html=True
                )

        with cc2:
            safety = ctx.get("safety_tips", [])
            if safety:
                st.markdown("**🛡️ Safety tips**")
                for tip in safety:
                    st.markdown(
                        f'<div class="tip-box">🛡️ {tip}</div>',
                        unsafe_allow_html=True
                    )

            events = ctx.get("local_events", [])
            if events:
                st.markdown("**🎉 Local events**")
                for ev in events:
                    st.markdown(f"- {ev}")

            packing = ctx.get("packing_tips", [])
            if packing:
                st.markdown("**🎒 Pack this**")
                st.markdown(", ".join(packing))

            etiquette = ctx.get("etiquette", [])
            if etiquette:
                st.markdown("**🙏 Etiquette**")
                for tip in etiquette:
                    st.markdown(f"- {tip}")

    # ── TAB 5: Chat ───────────────────────────────────────────────────────────
    with tab5:
        st.markdown("**Conversation history**")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Plan comparison
        if len(st.session_state.plan_versions) > 1:
            st.markdown("---")
            st.markdown("**📊 Plan comparison**")
            cols = st.columns(len(st.session_state.plan_versions))
            for i, v in enumerate(st.session_state.plan_versions):
                with cols[i]:
                    st.metric(
                        label = v["label"][:25],
                        value = fmt_inr(v["cost"]),
                    )

        # Raw JSON for debugging
        with st.expander("🔧 Raw plan JSON"):
            st.json(plan)
class UserProfileAgent:
    def extract_preferences(self, query: str):
        query = query.lower()
        prefs = ()

    # budget detection 
        if 'cheap' in query or 'low budget' in query:
            prefs['budget_style'] = "low"
        elif 'luxu' in query:
            prefs['budget_style'] = 'luxury'
        
        # Food
        if 'vag' in query:
            prefs['food_type'] = "vag"
        elif "non vag" in query:
            prefs['food_type']= "non-vag"
        
        #travel prece
        if "relex" in query:
            prefs['travel_pace']= 'relaxed'
        elif 'full packed' in query:
            prefs['travel_pace'] = 'packed'
        
        return prefs
    
    def update_profile(self, profile, query, plan):
        prefs = self.extract_preferences(query)

        for k, v in prefs.items():
            if v:
                profile.preferaces[k] = v

        # save past trip
        profile.past_trips.append({
                        "destination": plan.get("destination"),
            "budget": plan.get("budget", {}).get("total_cost"),
            "interests": plan.get("itinerary", {}).get("highlights", [])
        })

        return profile
    
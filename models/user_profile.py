class UserProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.preferancess = {
            "budget_style" : None,  #low /medium/ high
            "food_type": None,  # vag/ non- vag
            "travel_pace": None, #realexed / packed
            'interests': []  #beach, mountains , nightlife
        }
        self.past_trips = []
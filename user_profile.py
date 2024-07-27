import json
import logging
from config import USER_PROFILES_FILE

logger = logging.getLogger(__name__)

def load_user_profile(username):
    try:
        with open(USER_PROFILES_FILE, 'r') as f:
            profiles = json.load(f)
        
        default_profile = {
            "past_trips": [],
            "upcoming_trips": [],
            "credit_cards": [],
            "preferences": {
                "dining": {
                    "favorite_cuisines": [],
                    "frequently_visited_restaurants": [],
                    "dietary_restrictions": []
                },
                "shopping": {
                    "preferred_stores": [],
                    "online_retailers": []
                },
                "entertainment": {
                    "streaming_services": [],
                    "hobbies": []
                },
                "travel": {
                    "preferred_airlines": [],
                    "hotel_chains": [],
                    "travel_style": []
                }
            }
        }
        
        user_profile = profiles.get(username, default_profile)
        
        # Ensure all keys are present in the user profile
        for key, value in default_profile.items():
            if key not in user_profile:
                user_profile[key] = value
        
        return user_profile
    
    except FileNotFoundError:
        logger.warning("User profiles file not found. Creating new file.")
        with open(USER_PROFILES_FILE, 'w') as f:
            json.dump({}, f)
        return default_profile
    
    except json.JSONDecodeError:
        logger.error("Error decoding user profiles file.")
        return default_profile

def load_user_profile_old(username):
    try:
        with open(USER_PROFILES_FILE, 'r') as f:
            profiles = json.load(f)
        return profiles.get(username, {"past_trips": [], "upcoming_trips": []})
    except FileNotFoundError:
        logger.warning("User profiles file not found. Creating new file.")
        with open(USER_PROFILES_FILE, 'w') as f:
            json.dump({}, f)
        return {"past_trips": [], "upcoming_trips": []}
    except json.JSONDecodeError:
        logger.error("Error decoding user profiles file.")
        return {"past_trips": [], "upcoming_trips": []}

def save_user_profile(username, profile):
    try:
        with open(USER_PROFILES_FILE, 'r') as f:
            profiles = json.load(f)
    except FileNotFoundError:
        profiles = {}
    except json.JSONDecodeError:
        logger.error("Error decoding user profiles file. Overwriting with new data.")
        profiles = {}
    
    profiles[username] = profile
    
    with open(USER_PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

def add_trip(trip_type, username, trip_data):
    user_profile = load_user_profile(username)
    user_profile[trip_type].append(trip_data)
    save_user_profile(username, user_profile)

def get_trips(username, trip_type):
    user_profile = load_user_profile(username)
    return user_profile.get(trip_type, [])

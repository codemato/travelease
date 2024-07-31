import folium
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import googlemaps
import logging
from config import USE_GOOGLE_MAPS, GOOGLE_MAPS_API_KEY, API_MODE, AWS_CLAUDE_MODEL_ID, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, CLAUDE_MODEL_ID
import boto3
import os
import anthropic  # New import for native Claude API

logger = logging.getLogger(__name__)

if USE_GOOGLE_MAPS:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

if API_MODE == 'bedrock':
    session = boto3.Session(
        # aws_access_key_id=AWS_ACCESS_KEY_ID,
        # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        # aws_session_token=AWS_SESSION_TOKEN,
        # region_name=AWS_REGION
    )
    bedrock_client = session.client('bedrock-runtime')

def extract_locations_llm(text, api_client):
    print("extract+locations+llm",text)
    prompt = f"""
    Extract the locations associated with establishments from the following list. Each location should be in a format suitable for 
    geocoding (e.g., "street name, city name, country"). Only extract locations that are specifically associated with establishments 
    such as hotels, monuments, restaurants, attractions, government offices, emergency services, public facilities, etc. 
    Do not extract any locations from past trips. Only consider the locations the user is currently in or planning to visit. 
    Also, do not extract locations that are merely a mention of a country, state, or city without specifying an establishment. 
    Return the result as a JSON array of strings and mo extra information should be added after JSON array (like strings or sentences). 
    If no locations are found, return an empty array.

    Text: {text}

    Response (JSON array of strings):
    """

    try:
        if API_MODE == 'bedrock':
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            response = bedrock_client.invoke_model(
                body=body,
                modelId=AWS_CLAUDE_MODEL_ID,
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            locations_json = response_body['content'][0]['text']
        elif API_MODE == 'huggingface':
            response = api_client.chat(prompt)
            locations_json = str(response)
        elif API_MODE == 'native_claude':
            response = api_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            locations_json = response.content[0].text

        locations_json = locations_json.strip()
        print("--locations_json--", locations_json)
        # if locations_json.startswith("```json"):
        #     locations_json = locations_json[7:-3]
        
        locations = json.loads(locations_json)
        print("--final_locations_json--", locations)
        return locations
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {locations_json}")
        if "<!DOCTYPE html>" in locations_json:
            logger.error("Received HTML response instead of JSON. API might be down or returning an error page.")
        return []
    except Exception as e:
        logger.error(f"Error extracting locations using LLM: {str(e)}")
        return []

def get_coordinates_google(location):
    print("get_coordinates_google+location", location)
    try:
        result = gmaps.geocode(location)
        if result:
            lat = result[0]['geometry']['location']['lat']
            lng = result[0]['geometry']['location']['lng']
            logger.info(f"Successfully geocoded location using Google Maps: {location}")
            print("coordinates",lat, lng)
            return lat, lng
        else:
            print("coordinates","None")
            logger.warning(f"Could not geocode location using Google Maps: {location}")
            return None
    except Exception as e:
        logger.error(f"Error geocoding location {location} with Google Maps: {str(e)}")
        return None

def get_coordinates_nominatim(location):
    geolocator = Nominatim(user_agent="voyage_travel_assistant")
    try:
        location_data = geolocator.geocode(location, timeout=10)
        if location_data:
            logger.info(f"Successfully geocoded location using Nominatim: {location}")
            return location_data.latitude, location_data.longitude
        else:
            logger.warning(f"Could not geocode location using Nominatim: {location}")
            return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.error(f"Error geocoding location {location} with Nominatim: {str(e)}")
        return None

def get_coordinates(location):
    logger.info(f"value of USE_GOOGLE_MAPS: {USE_GOOGLE_MAPS}")
    if USE_GOOGLE_MAPS:
        return get_coordinates_google(location)
    else:
        return get_coordinates_nominatim(location)

def create_map(locations):
    if not locations:
        logger.warning("No locations provided to create_map function")
        return None
    
    valid_coordinates = []
    for location in locations:
        coordinates = get_coordinates(location)
        if coordinates:
            valid_coordinates.append((coordinates, location))
            print(f"Location: {location}, Coordinates: {coordinates}")
    
    if not valid_coordinates:
        logger.warning("No valid coordinates found for any locations")
        return None
    print("---valid_coordinates---",valid_coordinates)
    first_location = valid_coordinates[0][0]
    m = folium.Map(location=first_location, zoom_start=4)
    
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
    #for coordinates, location in valid_coordinates:
    for i, (coordinates, location) in enumerate(valid_coordinates):
        marker = folium.Marker(
            coordinates, 
            popup=location,
            tooltip=location,
            icon=folium.Icon(color=colors[i % len(colors)], icon='info-sign')
        )
        marker.options = {'index': i}  # Add this line to set the index
        marker.add_to(m)
        print(f"Added marker {i}: Location: {location}, Coordinates: {coordinates}")
    
    marker_count = sum(1 for _ in m._children.values() if isinstance(_, folium.Marker))
    print(f"Total markers on map: {marker_count}")

    
    if len(valid_coordinates) > 1:
        sw = min(coord[0] for coord, _ in valid_coordinates), min(coord[1] for coord, _ in valid_coordinates)
        ne = max(coord[0] for coord, _ in valid_coordinates), max(coord[1] for coord, _ in valid_coordinates)
        m.fit_bounds([sw, ne])
    
    logger.info(f"Created map with {len(valid_coordinates)} markers")
    return m

def extract_place_info_llm(text, api_client):
    print("extract_place_info_llm", text)
    prompt = f"""
    Analyze the following text and extract information about places (locations) mentioned. For each place, determine:
    1. The name of the place
    2. Whether the user is currently interested in this place
    3. Whether the user wants to visit this place in the future
    4. Whether the user is simply checking details about this place

    Consider both specific locations (e.g., cities, countries) and general travel intentions. If the user expresses a desire to travel or plan a trip without mentioning a specific place, create an entry for the general travel intention.

    Return the result as a JSON array of objects, where each object has the following structure:
    {{
        "place_name": "Name of the place or 'General Travel Plan' if no specific place is mentioned",
        "current_interest": true/false,
        "future_visit": true/false,
        "checking_details": true/false
    }}

    If no relevant places or travel intentions are found, return an empty array.

    Text: {text}
    Response (JSON array of objects):
    """

    try:
        if API_MODE == 'bedrock':
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            response = bedrock_client.invoke_model(
                body=body,
                modelId=AWS_CLAUDE_MODEL_ID,
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            place_info_json = response_body['content'][0]['text']
        elif API_MODE == 'huggingface':
            response = api_client.chat(prompt)
            place_info_json = str(response)
        elif API_MODE == 'native_claude':
            response = api_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            place_info_json = response.content[0].text

        place_info_json = place_info_json.strip()
        print("--place_info_json--", place_info_json)
        place_info = json.loads(place_info_json)
        print("--final_place_info--", place_info)
        return place_info
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {place_info_json}")
        if "<!DOCTYPE html>" in place_info_json:
            logger.error("Received HTML response instead of JSON. API might be down or returning an error page.")
        return []
    except Exception as e:
        logger.error(f"Error extracting place information using LLM: {str(e)}")
        return []
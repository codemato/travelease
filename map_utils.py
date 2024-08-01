import folium
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging
from config import USE_GOOGLE_MAPS, GOOGLE_MAPS_API_KEY, API_MODE, AWS_CLAUDE_MODEL_ID, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, IS_PRODUCTION, AWS_LOCATION_SERVICE_PLACE_INDEX
import boto3
import os
import random
from config import IS_PRODUCTION, LOCAL_PHOTOS_DIR, GOOGLE_MAPS_API_KEY, AWS_LOCATION_SERVICE_MAP_NAME, AWS_MAP_API_KEY
import base64
import anthropic  # New import for native Claude API
import io
import math
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)

if not IS_PRODUCTION and USE_GOOGLE_MAPS:
    import googlemaps
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

if API_MODE == 'bedrock':
    session = boto3.Session()
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
    if IS_PRODUCTION:
        return get_coordinates_aws(location)
    elif USE_GOOGLE_MAPS:
        return get_coordinates_google(location)
    else:
        return get_coordinates_nominatim(location)

def get_coordinates_aws(location):
    try:
        session = boto3.Session()
        location_client = session.client('location')
        
        response = location_client.search_place_index_for_text(
            IndexName=AWS_LOCATION_SERVICE_PLACE_INDEX,
            Text=location
        )
        
        if response['Results']:
            coordinates = response['Results'][0]['Place']['Geometry']['Point']
            return coordinates[1], coordinates[0]  # Latitude, Longitude
        else:
            logger.warning(f"Could not find coordinates for location: {location}")
            return None
    except Exception as e:
        logger.error(f"Error getting coordinates from AWS Location Service: {str(e)}")
        return None
def get_random_local_photo():
    try:
        photos = [f for f in os.listdir(LOCAL_PHOTOS_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if photos:
            random_photo = random.choice(photos)
            with open(os.path.join(LOCAL_PHOTOS_DIR, random_photo), 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            logger.warning("No local photos found in the photos directory.")
            return None
    except Exception as e:
        logger.error(f"Error fetching local photo: {str(e)}")
        return None

def create_aws_location_map_embed(locations):
    try:
        session = boto3.Session()
        location_client = session.client('location')
        # Read local MapLibre GL JS files
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, 'static', 'maplibre-gl.js'), 'r') as js_file:
            maplibre_js = js_file.read()
        with open(os.path.join(current_dir, 'static', 'maplibre-gl.css'), 'r') as css_file:
            maplibre_css = css_file.read()
        # Get coordinates for all locations
        coordinates = [get_coordinates_aws(loc) for loc in locations if get_coordinates_aws(loc)]

        if not coordinates:
            logger.warning("No valid coordinates found for any locations")
            return None

        # Calculate the center point
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)

        # Get temporary credentials for the map
        #credentials = session.get_credentials()
        #aws_credentials = credentials.get_frozen_credentials()

        # Create a map configuration
        map_configuration = {
            "mapName": AWS_LOCATION_SERVICE_MAP_NAME,
            "center": [center_lon, center_lat],  # [longitude, latitude]
            "zoom": 10,  # Adjust this value as needed
        }

        # Generate markers for each location
        markers = []
        for i, (lat, lon) in enumerate(coordinates):
            markers.append({
                "point": [lon, lat],
                "label": f"Location {i+1}"
            })

        # Create the map embedding HTML
        map_html = f"""
        <html>
        <head>
            <script>{maplibre_js}</script>
            <style>{maplibre_css}</style>
        </head>
        <body style="margin:0;padding:0;">
            <div id="map" style="width:100%;height:400px;"></div>
            <script>
                const apiKey = "{AWS_MAP_API_KEY}";
                const region = "{AWS_REGION}";
                const mapName = "{AWS_LOCATION_SERVICE_MAP_NAME}";
                const style = `https://maps.geo.${{region}}.amazonaws.com/maps/v0/maps/${{mapName}}/style-descriptor?key=${{apiKey}}`;

                const map = new maplibregl.Map({{
                    container: 'map',
                    style: style,
                    center: {map_configuration['center']},
                    zoom: {map_configuration['zoom']}
                }});

                map.on('load', function () {{
                    const markers = {json.dumps(markers)};
                    markers.forEach(marker => {{
                        new maplibregl.Marker()
                            .setLngLat(marker.point)
                            .setPopup(new maplibregl.Popup().setHTML(marker.label))
                            .addTo(map);
                    }});
                }});
            </script>
        </body>
        </html>
        """

        return "text/html", map_html.encode('utf-8')

    except ClientError as e:
        logger.error(f"AWS client error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating AWS Location Service map: {str(e)}", exc_info=True)
        return None
    
def create_aws_location_map(locations):
    try:
        session = boto3.Session()
        location_client = session.client('location')

        # Get coordinates for all locations
        coordinates = [get_coordinates_aws(loc) for loc in locations if get_coordinates_aws(loc)]

        if not coordinates:
            logger.warning("No valid coordinates found for any locations")
            return None

        # Calculate the center point
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)

        logger.info(f"Calculated center point: {center_lat}, {center_lon}")

        # Convert lat/lon to tile coordinates (assuming Web Mercator projection)
        def lat_lon_to_tile(lat, lon, zoom):
            lat_rad = math.radians(lat)
            n = 2.0 ** zoom
            x = int((lon + 180.0) / 360.0 * n)
            y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return x, y

        # Choose a zoom level (you may need to adjust this)
        zoom = 5

        x, y = lat_lon_to_tile(center_lat, center_lon, zoom)

        logger.info(f"Tile coordinates: x={x}, y={y}, z={zoom}")

        # Generate the map image
        response = location_client.get_map_tile(
            MapName=AWS_LOCATION_SERVICE_MAP_NAME,
            X=str(x),
            Y=str(y),
            Z=str(zoom)
        )

        logger.info(f"AWS Location Service response metadata: {response['ResponseMetadata']}")
        logger.info(f"Response content type: {response.get('ContentType')}")
        
        # Read the entire response body
        image_data = response['Blob'].read()
        
        logger.info(f"Image data length: {len(image_data)} bytes")

        return response.get('ContentType'), image_data
        
        # Return the raw response
        #return response

    except Exception as e:
        logger.error(f"Error creating AWS Location Service map: {str(e)}", exc_info=True)
        return None

def create_map(locations):
    if IS_PRODUCTION:
        logger.info(f"Imagewill be embedded")
        #return create_aws_location_map(locations)
        #return create_aws_location_map_embed(locations)
    else:
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
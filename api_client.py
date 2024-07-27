import boto3
import json
import os
from hugchat import hugchat
from hugchat.login import Login
import streamlit as st
import logging
from config import API_MODE, CLAUDE_MODEL_ID, VOYAGE_PROMPT
import anthropic  # New import for native Claude API

logger = logging.getLogger(__name__)

@st.cache_resource
def initialize_api_client():
    if API_MODE == 'bedrock':
        try:
            bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv('AWS_REGION'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            return bedrock_client
        except Exception as e:
            logger.error(f"Bedrock client initialization failed: {str(e)}")
            st.error(f"Bedrock client initialization failed. Please check your AWS credentials.")
            return None
    elif API_MODE == 'huggingface':
        try:
            #print("creds",os.getenv('HF_EMAIL'), os.getenv('HF_PASS'))
            sign = Login(os.getenv('HF_EMAIL'), os.getenv('HF_PASS'))
            cookies = sign.login()
            chatbot = hugchat.ChatBot(cookies=cookies)
            return chatbot
        except Exception as e:
            logger.error(f"HuggingFace client initialization failed: {str(e)}")
            st.error(f"HuggingFace client initialization failed. Please check your credentials.")
            return None
    elif API_MODE == 'native_claude':
        try:
            claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            return claude_client
        except Exception as e:
            logger.error(f"Native Claude client initialization failed: {str(e)}")
            st.error(f"Native Claude client initialization failed. Please check your Anthropic API key.")
            return None
    else:
        logger.error(f"Invalid API_MODE: {API_MODE}")
        st.error(f"Invalid API_MODE. Please check your configuration.")
        return None

def invoke_model(prompt, api_client, user_profile):
    past_trips = user_profile.get("past_trips", [])
    upcoming_trips = user_profile.get("upcoming_trips", [])
    credit_cards = user_profile.get("credit_cards", [])
    preferences = user_profile.get("preferences", {})

    past_trips_info = "Past Trips:\n" + "\n".join([format_trip_details(trip) for trip in past_trips])
    upcoming_trips_info = "Upcoming Trips:\n" + "\n".join([format_trip_details(trip) for trip in upcoming_trips])
    credit_cards_info = "Credit Cards:\n" + "\n".join([format_credit_card_info(card) for card in credit_cards])
    preferences_info = format_preferences(preferences)

    full_prompt = f"""{VOYAGE_PROMPT}

User Profile Information:

{past_trips_info}

{upcoming_trips_info}

{credit_cards_info}

{preferences_info}

User Query: {prompt}

TravelEase:"""
    logger.info(f"Raw response: {full_prompt}")
    if API_MODE == 'bedrock':
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            })
            response = api_client.invoke_model(
                body=body,
                modelId=CLAUDE_MODEL_ID,
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
        except Exception as error:
            logger.error(f"Error invoking Claude model: {error}")
            return "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."
    elif API_MODE == 'huggingface':
        try:
            response = api_client.chat(full_prompt)
            return f"TravelEase: {response}"
        except Exception as e:
            logger.error(f"Error invoking HuggingFace model: {str(e)}")
            return "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."
    elif API_MODE == 'native_claude':
        try:
            response = api_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error invoking native Claude model: {str(e)}")
            return "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."

def classify_topic(prompt, api_client):
    full_prompt = f"""
    Analyze the following user input and categorize it into one of these topics: 
    hotel, flights, restaurants, emergency. 
    Also, identify a relevant subtopic from: availability, bookings, reviews, locations, help.
    
    Provide the response in JSON format with 'topic' and 'subtopic' keys.
    
    User input: "{prompt}"
    
    JSON response:
    """
    
    logger.info(f"Raw response: {full_prompt}")
    if API_MODE == 'bedrock':
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            })
            response = api_client.invoke_model(
                body=body,
                modelId=CLAUDE_MODEL_ID,
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
        except Exception as error:
            logger.error(f"Error invoking Claude model: {error}")
            return "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."
    elif API_MODE == 'huggingface':
        try:
            response = api_client.chat(full_prompt)
            return f"TravelEase: {response}"
        except Exception as e:
            logger.error(f"Error invoking HuggingFace model: {str(e)}")
            return "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."
    elif API_MODE == 'native_claude':
        try:
            response = api_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error invoking native Claude model: {str(e)}")
            return "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."

def format_trip_details_old(trip):
    trip_details = f"Destination: {trip['destination']}, Date: {trip['date']}\n"
    trip_details += f"  Flight: {trip['flight']['class']} class, Departure: {trip['flight']['departure']}, Return: {trip['flight']['return']}\n"
    if trip['flight']['stopover']:
        trip_details += f"    Stopover: {trip['flight']['stopover']['city']}, Duration: {trip['flight']['stopover']['duration']}\n"
    trip_details += f"    Preferences: {', '.join(trip['flight']['preferences'])}\n"
    trip_details += f"  Hotel: {trip['hotel']['name']}, {trip['hotel']['class']}, Location: {trip['hotel']['location']}\n"
    trip_details += f"    Preferences: {', '.join(trip['hotel']['preferences'])}\n"
    return trip_details

def format_trip_details(trip):
    trip_details = f"Destination: {trip['destination']}, Date: {trip['date']}\n"
    trip_details += f"Flight Details:\n"
    trip_details += f"  - Class: {trip['flight']['class']}\n"
    trip_details += f"  - Departure: {trip['flight']['departure']}\n"
    trip_details += f"  - Return: {trip['flight']['return']}\n"
    if trip['flight'].get('stopover'):
        trip_details += f"  - Stopover: {trip['flight']['stopover']['city']} (Duration: {trip['flight']['stopover']['duration']})\n"
    trip_details += f"  - Preferences: {', '.join(trip['flight']['preferences'])}\n"
    trip_details += f"Hotel Details:\n"
    trip_details += f"  - Name: {trip['hotel']['name']}\n"
    trip_details += f"  - Class: {trip['hotel']['class']}\n"
    trip_details += f"  - Location: {trip['hotel']['location']}\n"
    trip_details += f"  - Number of nights: {trip['hotel']['nights']}\n"
    trip_details += f"  - Preferences: {', '.join(trip['hotel']['preferences'])}\n"
    return trip_details

def format_credit_card_info(card):
    card_info = f"Card: {card['name']}\n"
    card_info += f"Rewards Points: {card['rewards_points']}\n"
    card_info += "Offers:\n"
    for offer in card['offers']:
        card_info += f"  - {offer['description']} (Expires: {offer['expiry']})\n"
    card_info += "Partnerships:\n"
    for partnership in card['partnerships']:
        card_info += f"  - {partnership['brand']}: {partnership['benefit']}\n"
    return card_info

def format_preferences(preferences):
    pref_info = "User Preferences:\n"
    pref_info += "Dining:\n"
    pref_info += f"  - Favorite cuisines: {', '.join(preferences['dining']['favorite_cuisines'])}\n"
    pref_info += f"  - Frequently visited restaurants: {', '.join(preferences['dining']['frequently_visited_restaurants'])}\n"
    pref_info += f"  - Dietary restrictions: {', '.join(preferences['dining']['dietary_restrictions'])}\n"
    pref_info += "Shopping:\n"
    pref_info += f"  - Preferred stores: {', '.join(preferences['shopping']['preferred_stores'])}\n"
    pref_info += f"  - Online retailers: {', '.join(preferences['shopping']['online_retailers'])}\n"
    pref_info += "Entertainment:\n"
    pref_info += f"  - Streaming services: {', '.join(preferences['entertainment']['streaming_services'])}\n"
    pref_info += f"  - Hobbies: {', '.join(preferences['entertainment']['hobbies'])}\n"
    pref_info += "Travel:\n"
    pref_info += f"  - Preferred airlines: {', '.join(preferences['travel']['preferred_airlines'])}\n"
    pref_info += f"  - Preferred hotel chains: {', '.join(preferences['travel']['hotel_chains'])}\n"
    pref_info += f"  - Travel style: {', '.join(preferences['travel']['travel_style'])}\n"
    return pref_info

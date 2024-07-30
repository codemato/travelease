import streamlit as st
from amadeus_api import AmadeusAPI, format_flight_results
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, USE_MOCK_DATA
from api_client import invoke_model
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flight recommendation prompt
FLIGHT_RECOMMENDATION_PROMPT = """
You are an AI travel assistant specializing in flight recommendations. You have been provided with flight search results and the user's profile information. Your task is to analyze this data and provide personalized flight recommendations.

User Profile:
{user_profile_json}

Recent Conversation Context:
{conversation_context}

Flight Search Results:
{flight_results_json}

Based on the above information, please provide:
1. A personalized recommendation for the best flight option(s) considering the user's preferences, past trips, and any relevant information from the recent conversation. If no clear preferences are found, provide a general recommendation based on factors like price, duration, and convenience.
2. A formatted version of the flight details with airport and airline codes expanded to their full names.

Your response MUST be a valid JSON object with two main elements:
1. "recommendation": A text string containing your personalized flight recommendation and explanation.
2. "formatted_results": An array of formatted flight options, each containing expanded details (full airport and airline names) and all relevant information from the original search results.

Use the following format for your response:

{{
  "recommendation": "Your personalized recommendation text here...",
  "formatted_results": [
    {{
      "price": "Price in original currency",
      "itineraries": [
        {{
          "segments": [
            {{
              "departure": {{
                "airport": "Full name of departure airport",
                "iataCode": "Original IATA code",
                "date": "Departure date and time"
              }},
              "arrival": {{
                "airport": "Full name of arrival airport",
                "iataCode": "Original IATA code",
                "date": "Arrival date and time"
              }},
              "airline": "Full name of airline",
              "airlineCode": "Original airline code"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Ensure that your recommendation is clear, concise, and tailored to the user's needs as much as possible. If there are multiple good options, you may mention them in your recommendation. Remember, your entire response must be a valid JSON object.
"""

# Load mock data function
def load_mock_data():
    with open('mock_flight_data.json', 'r') as f:
        return json.load(f)
    
def get_flight_recommendations(flight_results, api_client, user_profile, conversation_context):
    # Prepare the prompt with actual data
    prompt = FLIGHT_RECOMMENDATION_PROMPT.format(
        user_profile_json=json.dumps(user_profile),
        conversation_context=json.dumps(conversation_context),
        flight_results_json=json.dumps(flight_results)
    )
    
    # Get recommendations from the language model
    response = invoke_model(prompt, api_client, user_profile)
    
    try:
        # Attempt to parse the entire response as JSON
        recommendations = json.loads(response)
        return recommendations
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse entire LLM response as JSON: {e}")
        # If parsing the entire response fails, try to extract JSON from the response
        try:
            # Find the start and end of the JSON object
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                recommendations = json.loads(json_str)
                return recommendations
            else:
                raise ValueError("No valid JSON object found in the response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to extract valid JSON from LLM response: {e}")
            st.error("An error occurred while processing flight recommendations.")
            return None

def display_flight_recommendations(recommendations):
    if not recommendations:
        st.warning("Unable to generate flight recommendations at this time.")
        return

    st.subheader("Flight Recommendations")
    st.write(recommendations["recommendation"])

    st.subheader("Flight Options")
    for i, flight in enumerate(recommendations["formatted_results"], 1):
        with st.expander(f"Option {i} - {flight['price']}", expanded=i==1):
            for j, itinerary in enumerate(flight['itineraries'], 1):
                st.markdown(f"**Itinerary {j}**")
                
                for segment in itinerary['segments']:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"**From: {segment['departure']['airport']}**")
                        st.write(f"({segment['departure']['iataCode']}) {segment['departure']['date']}")
                    
                    with col2:
                        st.markdown(f"**To: {segment['arrival']['airport']}**")
                        st.write(f"({segment['arrival']['iataCode']}) {segment['arrival']['date']}")
                    
                    with col3:
                        st.write(f"Airline: {segment['airline']} ({segment['airlineCode']})")
                    
                    st.markdown("---")

def flight_search_page():
    st.title("Flight Search")

    # Check if we should use mock data
    #USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'False').lower() == 'true'

    if not USE_MOCK_DATA:
        # Initialize AmadeusAPI
        try:
            amadeus_api = AmadeusAPI(AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET)
        except Exception as e:
            st.error(f"Failed to initialize Amadeus API: {str(e)}")
            logger.error(f"Amadeus API initialization error: {str(e)}")
            return

    # Use st.form to batch all form processing
    with st.form(key='flight_search_form'):
        st.write("Please provide the following details for your flight search:")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("Departure City (e.g., NYC)", key="origin_input")
            departure_date = st.date_input("Departure Date", key="departure_date_input")
        with col2:
            destination = st.text_input("Destination City (e.g., LON)", key="destination_input")
            return_date = st.date_input("Return Date (optional)", key="return_date_input")

        search_button = st.form_submit_button("Search Flights")

    if search_button:
        if origin and destination and departure_date:
            with st.spinner("Searching for flights and generating recommendations..."):
                try:
                    if USE_MOCK_DATA:
                        # Use mock data
                        flights = load_mock_data()
                        results = format_flight_results(flights['data'])
                    else:
                        # Search for flights using Amadeus API
                        flights = amadeus_api.search_flights(
                            origin,
                            destination,
                            departure_date.strftime("%Y-%m-%d"),
                            return_date.strftime("%Y-%m-%d") if return_date else None
                        )
                        results = format_flight_results(flights)
                    
                    # Get recommendations
                    recommendations = get_flight_recommendations(
                        results, 
                        st.session_state.api_client, 
                        st.session_state.user_profile,
                        st.session_state.get('chat_history', [])[-5:]  # Get last 5 messages as context
                    )
                    
                    # Display recommendations
                    display_flight_recommendations(recommendations)
                except Exception as e:
                    st.error(f"An error occurred while searching for flights: {str(e)}")
                    logger.error(f"Flight search error: {str(e)}")
        else:
            st.warning("Please fill in all required fields.")

if __name__ == "__main__":
    flight_search_page()
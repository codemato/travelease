import streamlit as st
from amadeus_api import AmadeusAPI, format_flight_results
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def flight_search_page():
    st.title("Flight Search")

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
            with st.spinner("Searching for flights..."):
                try:
                    flights = amadeus_api.search_flights(
                        origin,
                        destination,
                        departure_date.strftime("%Y-%m-%d"),
                        return_date.strftime("%Y-%m-%d") if return_date else None
                    )
                    results = format_flight_results(flights)
                    display_flight_results(results)
                except Exception as e:
                    st.error(f"An error occurred while searching for flights: {str(e)}")
                    logger.error(f"Flight search error: {str(e)}")
        else:
            st.warning("Please fill in all required fields.")

def display_flight_results(results):
    st.subheader("Flight Results")
    if not results:
        st.write("No flights found matching your criteria.")
        return
    
    for i, flight in enumerate(results, 1):
        with st.expander(f"Option {i} - {flight['price']}", expanded=True):
            for j, itinerary in enumerate(flight['itineraries'], 1):
                st.markdown(f"**Itinerary {j}**")
                
                for segment in itinerary:
                    col1, col2, col3 = st.columns(3)
                    
                    # Parse and format the datetime
                    dep_time = datetime.fromisoformat(segment['departure']['at'].replace('Z', '+00:00'))
                    arr_time = datetime.fromisoformat(segment['arrival']['at'].replace('Z', '+00:00'))
                    
                    with col1:
                        st.markdown(f"**{segment['departure']['iataCode']}**")
                        st.write(dep_time.strftime('%Y-%m-%d %H:%M'))
                    
                    with col2:
                        st.markdown(f"**{segment['arrival']['iataCode']}**")
                        st.write(arr_time.strftime('%Y-%m-%d %H:%M'))
                    
                    with col3:
                        st.write(f"Airline: {segment['carrierCode']}")
                    
                    st.markdown("---")

if __name__ == "__main__":
    flight_search_page()
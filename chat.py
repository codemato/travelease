import streamlit as st
from config import API_MODE, USE_GOOGLE_MAPS, LOGO_PATH
from api_client import invoke_model, initialize_api_client
from map_utils import extract_locations_llm, create_map
from streamlit_folium import folium_static
import folium
import streamlit.components.v1 as components
from google_reviews import get_hotel_reviews_summary
import json
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def show_map_callback():
    st.session_state.show_map = True

def hide_map_callback():
    st.session_state.show_map = False

def select_location(index):
    st.session_state.selected_location = index
# Helper function to convert image to base64
def image_to_base64(img):
    import io
    import base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "show_map" not in st.session_state:
        st.session_state.show_map = False
    if "locations" not in st.session_state:
        st.session_state.locations = []
    if "selected_location" not in st.session_state:
        st.session_state.selected_location = None

def display_welcome_message():
    welcome_message = f"Welcome back, {st.session_state.username}! How can I assist you with your travel plans today?"
    st.info(welcome_message)

def display_messages():
    # Load the custom icon
    icon = Image.open("images/icon.png")

    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar=icon):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def start_chat():
    if st.session_state.api_client is None:
        st.session_state.api_client = initialize_api_client()

    initialize_session_state()

    if st.session_state.api_client:
        # Holder forTitle and one-liner
        # chat icon
        icon = Image.open("images/icon.png")  
        #Welcome message
        display_welcome_message()
        
        chat_container = st.container()
        location_map_container = st.container()
        follow_up_container = st.container()
        
        with chat_container:
            display_messages()

        prompt = st.chat_input("What can TravelEase assist you with today?")
        
        if prompt:
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.show_map = False
            st.session_state.locations = []
            
            with st.spinner("Thinking..."):
                try:
                    full_response = invoke_model(prompt, st.session_state.api_client, st.session_state.user_profile)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    with chat_container:
                        with st.chat_message("assistant",avatar=icon):
                            st.markdown(full_response)
                    
                    locations = extract_locations_llm(full_response, st.session_state.api_client)
                    
                    if locations:
                        st.session_state.locations = locations
                        with location_map_container:
                            st.markdown("### Location Information")
                            st.write("I've found some locations that might be relevant to your query.")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.button("Show locations on map", on_click=show_map_callback)
                            with col2:
                                st.button("Continue without map", on_click=hide_map_callback)
                
                except Exception as e:
                    logger.error(f"Error during chat: {str(e)}")
                    error_message = "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                    with chat_container:
                        with st.chat_message("assistant",avatar=icon):
                            st.markdown(error_message)

        if st.session_state.show_map and st.session_state.locations:
            with location_map_container:
                st.header("Location Overview")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Suggested Locations")
                    for i, loc in enumerate(st.session_state.locations):
                        st.button(loc, key=f"location_{i}", on_click=select_location, args=(i,))
                
                with col2:
                    st.subheader("Interactive Map")
                    m = create_map(st.session_state.locations)
                    
                    if m:
                        try:
                            # If a location is selected, focus the map on that location
                            if st.session_state.selected_location is not None:
                                selected_loc = st.session_state.locations[st.session_state.selected_location]
                                for marker in m._children.values():
                                    if isinstance(marker, folium.Marker):
                                        if marker.options.get('index') == st.session_state.selected_location:
                                            marker.add_child(folium.Popup(selected_loc, max_width=300))
                                            coordinates = marker.location
                                            st.write(f"Debug - Selected coordinates: {coordinates}")
                                            if coordinates and len(coordinates) == 2:
                                                m.location = coordinates
                                                m.zoom_start = 10  # Adjust zoom level as needed
                                            else:
                                                st.warning(f"Invalid coordinates for {selected_loc}: {coordinates}")
                                            break
                                else:
                                    st.warning(f"No marker found for selected location: {selected_loc}")

                            # Use streamlit_folium to display the map
                            folium_static(m)
                            
                            st.info("💡 Tip: Click on a location name to highlight it on the map.")
                            
                        except Exception as e:
                            st.error(f"Error displaying map: {str(e)}")
                            st.error("An error occurred while displaying the map. Please try again.")
                    else:
                        st.warning("Unable to create map for the specified locations. Please verify the location names.")
                
                # Reviews section
                st.header("Location Reviews and Insights")
                selected_hotel = st.selectbox("Select a hotel to view detailed reviews", st.session_state.locations)
                if selected_hotel:
                    reviews = get_hotel_reviews_summary(selected_hotel, st.session_state.api_client)
                    if reviews:
                        col1, col2, col3 = st.columns([2,1,1])
                        with col1:
                            st.subheader(reviews['name'])
                        with col2:
                            st.metric("Overall Rating", f"{reviews['rating']}/5")
                        with col3:
                            st.metric("AI Score", f"{reviews['summary']['score']}/5")
                        
                        st.subheader("Review Summary")
                        st.write(reviews['summary']['summary'])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("💪 Strengths")
                            for point in reviews['summary']['positive_points']:
                                st.markdown(f"- {point}")
                        
                        with col2:
                            st.subheader("🔧 Areas for Improvement")
                            for point in reviews['summary']['negative_points']:
                                st.markdown(f"- {point}")
                        
                        st.info("💡 Tip: Consider these insights when making your decision.")
                    else:
                        st.warning("No reviews found for this Location. It might be a new or less popular accommodation.")

            with follow_up_container:
                context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-5:]])
                follow_up_prompt = f"""You are a Travel Assistant Chatbot. Based on the following conversation context, generate a relevant follow-up question that continues the discussion about the mentioned locations or the user's travel plans. The question should be specific to the conversation and encourage further engagement:

                {context}

                Follow-up question:"""
                
                follow_up_response = invoke_model(follow_up_prompt, st.session_state.api_client, st.session_state.user_profile)
                
                follow_up_question = follow_up_response.split("TravelEase:")[-1].strip()
                
                st.session_state.messages.append({"role": "assistant", "content": follow_up_question})
                with st.chat_message("assistant",avatar=icon):
                    st.markdown(follow_up_question)

    else:
        st.warning(f"TravelEase initialization failed. Please check your {API_MODE.capitalize()} credentials and try again.")

if __name__ == "__main__":
    start_chat()
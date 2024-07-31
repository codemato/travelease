import streamlit as st
from config import API_MODE, USE_GOOGLE_MAPS, LOGO_PATH
from api_client import invoke_model, initialize_api_client, transcribe_audio, synthesize_speech
from map_utils import extract_locations_llm, create_map, extract_place_info_llm
from ui_components import set_custom_carousel_css
from streamlit_folium import folium_static
import folium
import streamlit.components.v1 as components
from google_reviews import get_hotel_reviews_summary, get_place_photo
import json
import logging
from PIL import Image
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import base64

logger = logging.getLogger(__name__)

def show_map_callback():
    st.session_state.show_map = True

def hide_map_callback():
    st.session_state.show_map = False

def select_location(index):
    st.session_state.selected_location = index

def image_to_base64(img):
    import io
    import base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "show_map" not in st.session_state:
        st.session_state.show_map = False
    if "locations" not in st.session_state:
        st.session_state.locations = []
    if "selected_location" not in st.session_state:
        st.session_state.selected_location = None
    if "selected_button" not in st.session_state:
        st.session_state.selected_button = None
    if "travel_days" not in st.session_state:
        st.session_state.travel_days = 2
    if "place_info" not in st.session_state:
        st.session_state.place_info = []
    if "button_clicked" not in st.session_state:
        st.session_state.button_clicked = False
    if "welcome_displayed" not in st.session_state:
        st.session_state.welcome_displayed = False
    if "helper_buttons_displayed" not in st.session_state:
        st.session_state.helper_buttons_displayed = False
    if "button_results" not in st.session_state:
        st.session_state.button_results = {}

def button_click(button_type):
    st.session_state.selected_button = button_type
    st.session_state.button_clicked = True

def start_voice_chat():
    if "api_client" not in st.session_state or st.session_state.api_client is None:
        st.session_state.api_client = initialize_api_client()

    initialize_session_state()

    if st.session_state.api_client:
        st.markdown('<div class="custom-container voice-chat-container">', unsafe_allow_html=True)
        st.title("Voice-Assisted Travel Planner")
        
        if st.button("Start Recording", key="start_recording"):
            with st.spinner("Recording... Speak now"):
                audio_data = record_audio(duration=5)  # Record for 5 seconds
            
            with st.spinner("Processing your request..."):
                text = transcribe_audio(audio_data)
                st.text(f"You said: {text}")
                
                response = invoke_model(text, st.session_state.api_client, st.session_state.user_profile)
                st.text("AI Response:")
                st.write(response)
                
                audio_response = synthesize_speech(response)
                
                # Convert audio to base64
                audio_base64 = base64.b64encode(audio_response).decode()
                
                # Create an HTML audio element with autoplay
                audio_html = f"""
                    <audio autoplay="true">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                        Your browser does not support the audio element.
                    </audio>
                """
                
                # Display the audio element
                st.components.v1.html(audio_html, height=50)
                
                locations = extract_locations_llm(response, st.session_state.api_client)
                if locations:
                    st.session_state.locations = locations
                    display_map_and_reviews()
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(f"TravelEase initialization failed. Please check your {API_MODE.capitalize()} credentials and try again.")

def record_audio(duration, samplerate=16000):
    audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()
    return audio_data

def should_display_helper_buttons(place_info, full_response):
    if place_info:
        return any(place['current_interest'] or place['future_visit'] or place['checking_details'] for place in place_info)
    else:
        # If no place_info, check if the response indicates travel planning
        planning_keywords = ['plan', 'visit', 'travel', 'trip', 'vacation', 'holiday', 'tour']
        return any(keyword in full_response.lower() for keyword in planning_keywords)

def handle_button_click(button_type, location):
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history[-5:]])
    
    prompts = {
        "restaurants": f"Based on the following conversation context and the location {location}, provide information about popular restaurants nearby:\n\n{context}",
        "activities": f"Based on the following conversation context and the location {location}, provide information about popular activities nearby:\n\n{context}",
        "culture": f"Based on the following conversation context and the location {location}, provide information about popular cultural centers nearby:\n\n{context}",
        "weather": f"Based on the following conversation context and the location {location}, provide generic weather information. If the user specified a time of year for travel, include that specific weather information:\n\n{context}",
    }
    
    prompt = prompts.get(button_type, "")
    if prompt:
        response = invoke_model(prompt, st.session_state.api_client, st.session_state.user_profile)
        
        # Add the response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        return response
    return ""

def button_click(button_type):
    st.session_state.selected_button = button_type
    st.session_state.button_clicked = True

def display_helper_buttons(location):
    st.info("💡 Tip: Click on a below buttons to get more information about the location.")
    cols = st.columns(4)
    buttons = ["Restaurants", "Activities", "Culture", "Weather"]

    for i, button in enumerate(buttons):
        with cols[i]:
            unique_key = f"info_button_{location}_{button.lower()}"
            if st.button(button, key=unique_key):
                button_click(button.lower())

def get_chat_context():
    context = []
    for msg in st.session_state.chat_history[-10:]:  # Get last 10 messages
        if msg['role'] == 'user':
            context.append(f"User: {msg['content']}")
        elif msg['role'] == 'assistant':
            context.append(f"TravelEase: {msg['content']}")
    return "\n".join(context)

def display_debug_info(context):
    st.sidebar.subheader("Debug Information")
    st.sidebar.text("Current Context:")
    st.sidebar.code(context)

def display_button_results(location):
    if st.session_state.button_clicked:
        result = handle_button_click(st.session_state.selected_button, location)
        st.session_state.button_results[st.session_state.selected_button] = result
        st.session_state.button_clicked = False
        
        # Add button click result to chat history
        button_result_message = f"Here's information about {st.session_state.selected_button} in {location}:\n\n{result}"
        st.session_state.chat_history.append({"role": "assistant", "content": button_result_message})
        
        # Display the result in the chat UI
        with st.chat_message("assistant", avatar=Image.open("images/icon.png")):
            st.markdown(f"### {st.session_state.selected_button.capitalize()} Information")
            st.markdown(result)

def display_image_carousel(photos, hotel_name):
    if not photos:
        st.write("No photos available for this location.")
        return

    # Apply custom CSS
    set_custom_carousel_css()

    # Initialize session state for this hotel if not exists
    if f"image_index_{hotel_name}" not in st.session_state:
        st.session_state[f"image_index_{hotel_name}"] = 0

    image_index = st.session_state[f"image_index_{hotel_name}"]
    
    # Create a container for the image and buttons
    with st.container():
        # Display current image
        with st.spinner("Loading image..."):
            photo_reference = photos[image_index]
            image_data = get_place_photo(photo_reference)
            if image_data:
                st.markdown(f"""
                <div class="image-container">
                    <img src="data:image/jpeg;base64,{image_data}">
                </div>
                <p style="text-align: center;">Image {image_index + 1} of {len(photos)}</p>
                """, unsafe_allow_html=True)
            else:
                st.write("Failed to load image.")

        # Use a form for the buttons
        with st.form(key=f"nav_form_{hotel_name}"):
            col1, col2 = st.columns([1, 1])
            with col1:
                prev_button = st.form_submit_button("Previous")
            with col2:
                next_button = st.form_submit_button("Next")
            
            # Handle button clicks
            if prev_button:
                st.session_state[f"image_index_{hotel_name}"] = (image_index - 1) % len(photos)
                st.experimental_rerun()
            elif next_button:
                st.session_state[f"image_index_{hotel_name}"] = (image_index + 1) % len(photos)
                st.experimental_rerun()

def display_map_and_reviews():
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
                                    m.zoom_start = 10
                                else:
                                    st.warning(f"Invalid coordinates for {selected_loc}: {coordinates}")
                                break
                    else:
                        st.warning(f"No marker found for selected location: {selected_loc}")

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
                # Display image carousel
            display_image_carousel(reviews.get('photos', []), reviews['name'])

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

def display_follow_up_question():
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history[-5:]])
    follow_up_prompt = f"""You are a Travel Assistant Chatbot. You dont need to introduce yourself. Based on the following conversation context, generate a relevant follow-up question that continues the discussion about the mentioned locations or the user's travel plans. The question should be specific to the conversation and encourage further engagement:

    {context}

    Follow-up question:"""
    
    follow_up_response = invoke_model(follow_up_prompt, st.session_state.api_client, st.session_state.user_profile)
    
    follow_up_question = follow_up_response.split("TravelEase:")[-1].strip()
    
    st.session_state.chat_history.append({"role": "assistant", "content": follow_up_question})
    with st.chat_message("assistant", avatar=Image.open("images/icon.png")):
        st.markdown(follow_up_question)

def start_chat():
    if "api_client" not in st.session_state or st.session_state.api_client is None:
        st.session_state.api_client = initialize_api_client()

    initialize_session_state()

    if st.session_state.api_client:
        icon = Image.open("images/icon.png")
        
        # Developer mode toggle
        developer_mode = st.sidebar.checkbox("Developer Mode")
        
        # Display welcome message every time
        welcome_message = f"Welcome back, {st.session_state.username}! How can I assist you with your travel plans today?"
        st.info(welcome_message)
        
        # Create a fixed container for buttons
        button_container = st.container()
        
        # Create a container for button responses
        results_container = st.container()
        
        # Display buttons in the fixed container
        with button_container:
            st.markdown('<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Plan a new Trip"):
                    with results_container:
                        with st.spinner("Planning your new trip.."):
                            trip_info = invoke_model("Plan a new trip based on his user profile, preferences", st.session_state.api_client, st.session_state.user_profile)
                            st.markdown("### Plan a new Trip")
                            st.write(trip_info)
            with col2:
                if st.button("My Offers"):
                    with results_container:
                        with st.spinner("Fetching your credit card offers..."):
                            offer_info = invoke_model("Summarize the offers on my credit cards", st.session_state.api_client, st.session_state.user_profile)
                            st.markdown("### My Offers")
                            st.write(offer_info)
            with col3:
                if st.button("My Trips"):
                    with results_container:
                        with st.spinner("Fetching your card details..."):
                            card_info = invoke_model("Summarize my past and future trips", st.session_state.api_client, st.session_state.user_profile)
                            st.markdown("### My Trips")
                            st.write(card_info)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Add some space between the results and the chat history
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display existing chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"], avatar=icon if message["role"] == "assistant" else None):
                st.markdown(message["content"])
        
        # Check if we need to prompt for trip planning
        if st.session_state.get('prompt_trip_planning', False):
            location = st.session_state.get('last_identified_location', 'the location you found')
            prompt = f"Great! I'd be happy to help you plan a trip to {location}. What would you like to know about planning a trip there? For example, I can help with information about accommodations, transportation, attractions, or the best time to visit."
            
            with st.chat_message("assistant", avatar=icon):
                st.markdown(prompt)
            
            st.session_state.chat_history.append({"role": "assistant", "content": prompt})
            st.session_state.prompt_trip_planning = False
        
        # Chat input
        user_input = st.chat_input("What can TravelEase assist you with today?")
        
        if user_input:
            # Display user message
            st.chat_message("user").markdown(user_input)
            
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.spinner("Thinking..."):
                try:
                    # Prepare context from recent chat history
                    context = get_chat_context()
                    
                    # Display debug information if in developer mode
                    if developer_mode:
                        display_debug_info(context)

                    full_response = invoke_model(user_input, st.session_state.api_client, st.session_state.user_profile, context=context)
                    
                    # Display assistant response
                    with st.chat_message("assistant", avatar=icon):
                        st.markdown(full_response)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    
                    locations = extract_locations_llm(full_response, st.session_state.api_client)
                    place_info = extract_place_info_llm(full_response, st.session_state.api_client)
                    
                    st.session_state.locations = locations
                    st.session_state.place_info = place_info
                    
                except Exception as e:
                    logger.error(f"Error during chat: {str(e)}")
                    error_message = "TravelEase: I apologize, but I encountered an error while processing your request. Please try again."
                    
                    # Display error message
                    with st.chat_message("assistant", avatar=icon):
                        st.markdown(error_message)
                    
                    # Add error message to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": error_message})

        # Map and location information
        if st.session_state.locations:
            st.markdown("### Location Information")
            st.write("I've found some locations that might be relevant to your query.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Show locations on map"):
                    st.session_state.show_map = True
            with col2:
                if st.button("Continue without map"):
                    st.session_state.show_map = False

            if st.session_state.show_map:
                display_map_and_reviews()

        # Display helper buttons and results
        if should_display_helper_buttons(st.session_state.place_info, st.session_state.chat_history[-1]["content"] if st.session_state.chat_history else ""):
            location = st.session_state.locations[0] if st.session_state.locations else "general"
            display_helper_buttons(location)
            display_button_results(location)
        
        # Display debug information if in developer mode
        if developer_mode:
            display_debug_info(get_chat_context())

    else:
        st.warning(f"TravelEase initialization failed. Please check your {API_MODE.capitalize()} credentials and try again.")

if __name__ == "__main__":
    start_chat()
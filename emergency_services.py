import streamlit as st
import json
from api_client import invoke_model
from config import EMERGENCY_SERVICES, GOOGLE_MAPS_API_KEY
import logging
import requests
from streamlit_searchbox import st_searchbox

logger = logging.getLogger(__name__)

def get_place_suggestions(query):
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": query,
        "key": GOOGLE_MAPS_API_KEY,
       # "types": "(cities)"  # This restricts suggestions to cities
    }
    response = requests.get(url, params=params)
    suggestions = response.json().get("predictions", [])
    return [suggestion["description"] for suggestion in suggestions]

def get_emergency_contacts(api_client, user_profile, location):
    user_country = user_profile.get('country', 'Unknown')
    prompt = f"""
    Provide emergency contact details for {', '.join(EMERGENCY_SERVICES)} in {location}.
    The user's home country is {user_country}.
    
    Return the information in the following JSON format:
    {{
        "Police": {{
            "Name": "Local Police Department",
            "Phone number": "+1234567890",
            "Email address": "police@example.com",
            "Physical address": "123 Main St, City, Country",
            "Directions": "Head north on Current St, turn right on Main St",
            "Approximate distance": "2 km"
        }},
        "Hospital": {{
            "Name": "City General Hospital",
            "Phone number": "+1987654321",
            "Email address": "hospital@example.com",
            "Physical address": "456 Health Ave, City, Country",
            "Directions": "Head east on Current St, turn left on Health Ave",
            "Approximate distance": "3 km"
        }},
        "Fire Department": {{
            "Name": "City Fire Station",
            "Phone number": "+1122334455",
            "Email address": "fire@example.com",
            "Physical address": "789 Emergency Rd, City, Country",
            "Directions": "Head west on Current St, turn right on Emergency Rd",
            "Approximate distance": "1.5 km"
        }},
        "Embassy": {{
            "Name": "Embassy of {user_country}",
            "Phone number": "+1555666777",
            "Email address": "embassy@example.com",
            "Physical address": "101 Diplomatic Blvd, City, Country",
            "Directions": "Head south on Current St, turn left on Diplomatic Blvd",
            "Approximate distance": "5 km"
        }}
    }}

    Ensure all fields are filled with appropriate information for {location}. If any information is unavailable, use "N/A" as the value.
    """
    response = invoke_model(prompt, api_client, user_profile)
    
    logger.debug(f"Raw response from language model: {response}")
    
    if not response or response.isspace():
        logger.error("Received empty response from language model")
        st.error("Received an empty response from the AI model. Please try again.")
        return None, prompt

    try:
        # Extract JSON from the response
        json_str = response[response.find('{'):response.rfind('}')+1]
        contacts = json.loads(json_str)
        
        # Validate and fill missing fields
        for service in EMERGENCY_SERVICES:
            if service not in contacts:
                contacts[service] = {}
            
            service_info = contacts[service]
            required_fields = ['Name', 'Phone number', 'Email address', 'Physical address', 'Directions', 'Approximate distance']
            for field in required_fields:
                if field not in service_info or not service_info[field]:
                    service_info[field] = "N/A"
                    logger.warning(f"Missing or empty {field} for {service}. Set to N/A.")
        
        return contacts, prompt
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        st.error(f"Error parsing emergency contact information. The response was not valid JSON. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        st.error(f"An unexpected error occurred while processing emergency contact information. Please try again.")
    
    return None, prompt

def display_emergency_contacts(contacts):
    st.header("Emergency Contacts")
    for service, details in contacts.items():
        with st.expander(f"{service} Information"):
            st.subheader(details['Name'])
            st.write(f"📞 Phone: {details['Phone number']}")
            st.write(f"✉️ Email: {details['Email address']}")
            st.write(f"🏢 Address: {details['Physical address']}")
            st.write(f"🧭 Directions: {details['Directions']}")
            st.write(f"📏 Distance: {details['Approximate distance']}")

def emergency_contacts_page():
    st.title("Emergency Contacts")
    
    # Location input with autocomplete using streamlit-searchbox
    selected_location = st_searchbox(
        get_place_suggestions,
        key="location_searchbox",
        label="Enter your current location:",
        placeholder="Start typing a city name...",
        default=""
    )
    
    if st.button("Get Emergency Contacts"):
        if selected_location:
            with st.spinner("Fetching emergency contact information..."):
                contacts, prompt = get_emergency_contacts(st.session_state.api_client, st.session_state.user_profile, selected_location)
                if contacts:
                    display_emergency_contacts(contacts)
                else:
                    st.warning("Unable to retrieve complete emergency contact information. Please try again or contact support.")
        else:
            st.warning("Please enter your current location.")

    # if st.checkbox("Show Debug Information", value=False):
    #     st.subheader("Debug Information")
    #     st.json(st.session_state.user_profile)
    #     st.write("API Client:", type(st.session_state.api_client))
    #     st.write("API Mode:", st.session_state.mode)
        
    #     st.subheader("Prompt Details")
    #     if 'prompt' in locals():
    #         st.code(prompt, language="text")
    #     else:
    #         st.write("Prompt will be displayed after generating emergency contacts.")
        
    #     if st.button("Test API Response"):
    #         test_prompt = f"Provide a sample JSON response for emergency contacts in {selected_location or 'New York City'}."
    #         test_response = invoke_model(test_prompt, st.session_state.api_client, st.session_state.user_profile)
    #         st.text("Test Prompt:")
    #         st.code(test_prompt, language="text")
    #         st.text("Raw API Response:")
    #         st.code(test_response, language="json")
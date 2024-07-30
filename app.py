import streamlit as st
from config import LOGO_PATH, DEFAULT_MODE, BYPASS_LOGIN, BYPASS_USERNAME, ICON_PATH
from auth import init_session_state, login, logout
from chat import start_chat, start_voice_chat
from ui_components import render_sidebar, set_custom_css
from user_profile import load_user_profile
from emergency_services import emergency_contacts_page
from flight_search import flight_search_page  # Import the new flight_search_page function


def main():
    st.set_page_config(page_title="TravelEase", page_icon=LOGO_PATH, layout="wide")
    init_session_state()
    if "mode" not in st.session_state:
        st.session_state.mode = DEFAULT_MODE    
    # Bypass login
    if BYPASS_LOGIN and not st.session_state.logged_in:
        st.session_state.logged_in = True
        st.session_state.username = BYPASS_USERNAME
        st.session_state.user_profile = load_user_profile(BYPASS_USERNAME)

    if st.session_state.logged_in:
        render_sidebar()
        set_custom_css()
        
        try:
            if st.session_state.page == "emergency_contacts":
                emergency_contacts_page()
            elif st.session_state.page == "flight_search":
                flight_search_page()
            elif st.session_state.page == "chat" or st.session_state.page == "":
                if st.session_state.mode == "standard":
                    start_chat()
                else:  # special mode
                    start_voice_chat()
            else:
                st.error("Unknown page selected")
        except ImportError as e:
            st.error(f"Error: Unable to import required modules. Please check your installation. Details: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
    else:
        login()

if __name__ == "__main__":
    main()
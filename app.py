import streamlit as st
from config import LOGO_PATH 
from auth import init_session_state, login, logout
from chat import start_chat
from ui_components import render_sidebar, set_custom_css
#Bypass Login
from user_profile import load_user_profile


def main():
    st.set_page_config(page_title="Voyage", page_icon=LOGO_PATH, layout="wide")
    init_session_state()
    #Bypass login
    st.session_state.logged_in = True
    st.session_state.username = "renjith"
    st.session_state.user_profile = load_user_profile("renjith")

    if st.session_state.logged_in:
        render_sidebar()
        set_custom_css()
        start_chat()
    else:
        login()

if __name__ == "__main__":
    main()

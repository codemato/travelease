import streamlit as st
import json
import bcrypt
import logging
from config import USERS_FILE, LOGO_PATH
from user_profile import load_user_profile

logger = logging.getLogger(__name__)

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_client" not in st.session_state:
        st.session_state.api_client = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None
    if "map_consent" not in st.session_state:
        st.session_state.map_consent = None

def authenticate(username, password):
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)["users"]
        for user in users:
            if user["username"] == username and bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                return True
        return False
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        st.error("An error occurred during authentication. Please try again.")
        return False

def login():
    st.image(LOGO_PATH, width=200)
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_profile = load_user_profile(username)
            st.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def logout():
    st.session_state.logged_in = False
    st.session_state.api_client = None
    st.session_state.messages = []
    st.session_state.username = ""
    st.session_state.user_profile = None
    st.session_state.map_consent = None
    st.success("Logged out successfully.")
    st.rerun()

def require_login(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.logged_in:
            st.warning("Please log in to access this feature.")
            return
        return func(*args, **kwargs)
    return wrapper

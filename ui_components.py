import streamlit as st
from config import LOGO_PATH, API_MODE
from user_profile import add_trip

def set_custom_css():
    st.markdown("""
    <style>
    @import url(https://db.onlinewebfonts.com/c/4b687894b171c0b0472be66a537851f0?family=Chase);
    @font-face {
        font-family: "Chase";
        src: url("https://db.onlinewebfonts.com/t/4b687894b171c0b0472be66a537851f0.eot");
        src: url("https://db.onlinewebfonts.com/t/4b687894b171c0b0472be66a537851f0.eot?#iefix")format("embedded-opentype"),
        url("https://db.onlinewebfonts.com/t/4b687894b171c0b0472be66a537851f0.woff2")format("woff2"),
        url("https://db.onlinewebfonts.com/t/4b687894b171c0b0472be66a537851f0.woff")format("woff"),
        url("https://db.onlinewebfonts.com/t/4b687894b171c0b0472be66a537851f0.ttf")format("truetype"),
        url("https://db.onlinewebfonts.com/t/4b687894b171c0b0472be66a537851f0.svg#Chase")format("svg");
    }
    .logo_title{
        font-family: "Chase";
        font-weight: bold;
        height: 300px
    }
    .horizontal-layout {
        display: flex;
        align-items: center;
        justify-content: flex-start;
    }
    .container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
    }
    .logo {
        width: 200px;
    }
    .bot_title {
        font-size: 26px;
        font-weight: bold;
        color: #005eb8;
        margin-bottom: 0px;
        margin-top: 7px;
        margin-left: -21px;       
    }

    .message-container {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 10px;
    }
    .location-map-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .location-tile {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .location-tile:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .stMapContainer {
        height: 300px !important;
        border-radius: 10px;
        overflow: hidden;
    }
    iframe[data-testid="stIFrame"] {
        width: 100% !important;
    }
    .css-1544g2n.e1fqkh3o4 {
        padding-top: 2rem;
    }
    .stAlert {
        background-color: #e9ecef;
        color: #495057;
        border: none;
        border-radius: 5px;
    }
    .st-eb {
        border-radius: 5px;
    } 
    .bot_title {
        font-size: 36px;
        font-weight: bold;
        color: #005eb8; /* Chase blue color */
        margin-bottom: 10px;
    }
    .oneliner {
        font-size: 20px;
        color: #444444;
        margin-bottom: 20px;
    }
    body {
        font-family: 'Arial', sans-serif;
        color: #333;
        line-height: 1.6;
    }

    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f9f9f9;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Message bubbles */
    .message {
        margin-bottom: 15px;
        padding: 10px 15px;
        border-radius: 18px;
        max-width: 70%;
    }

    .user-message {
        background-color: #DCF8C6;
        align-self: flex-end;
    }

    .assistant-message {
        background-color: #E5E5EA;
        align-self: flex-start;
    }

    /* Location Information section */
    .location-info {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin-top: 30px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .location-info h3 {
        color: #005eb8;
        font-size: 24px;
        margin-bottom: 15px;
        border-bottom: 2px solid #005eb8;
        padding-bottom: 10px;
    }

    /* Buttons */
    .stButton > button {
        background-color: #005eb8;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #004185;
    }

    /* Custom texts */
    .custom-text {
        font-size: 18px;
        color: #333;
        margin-bottom: 15px;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Chase', 'Arial', sans-serif;
        color: #005eb8;
        margin-top: 30px;
        margin-bottom: 15px;
    }

    h1 { font-size: 32px; }
    h2 { font-size: 28px; }
    h3 { font-size: 24px; }
    h4 { font-size: 20px; }
    h5 { font-size: 18px; }
    h6 { font-size: 16px; }

    /* Map container */
    .map-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
        margin-top: 20px;
    }

    /* Hotel reviews section */
    .hotel-reviews {
        background-color: #f5f5f5;
        border-radius: 8px;
        padding: 20px;
        margin-top: 30px;
    }

    .hotel-reviews h4 {
        color: #005eb8;
        border-bottom: 2px solid #005eb8;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    /* Metrics */
    .metric-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #005eb8;
    }

    .metric-label {
        font-size: 14px;
        color: #666;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .chat-container {
            padding: 10px;
        }

        .message {
            max-width: 85%;
        }

        h1 { font-size: 28px; }
        h2 { font-size: 24px; }
        h3 { font-size: 20px; }
    }
    .st-emotion-cache-1ghhuty {
        background-color: rgb(59 196 217);
    }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.image(LOGO_PATH, width=300)
        #st.markdown('<div class="oneliner">Your personalized AI travel companion, simplifying your journeys with tailored recommendations and seamless support</div>', unsafe_allow_html=True)

        st.header("Quick Links")
        
        # if st.button("View Itinerary"):
        #     st.write("Your itinerary will be displayed here.")
        
        if st.button("Travel Tips"):
            st.write("Travel tips for your destination will be shown here.")
        
        st.sidebar.button("Emergency Contacts", on_click=set_page, args=("emergency_contacts",))

        # Mode selection in sidebar
        st.title("Mode Selection")
        mode_options = ["Standard", "Special (Voice Assisted)"]
        selected_mode = st.radio("Choose Mode", mode_options, index=0 if st.session_state.mode == "standard" else 1)
        
        if selected_mode == "Standard":
            st.session_state.mode = "standard"
        else:
            st.session_state.mode = "special"

        # Display current mode
        st.write(f"Current Mode: {st.session_state.mode.capitalize()}")
                
        # if st.button("Manage Past Trips"):
        #     add_trip_ui("past_trips")
        
        # if st.button("Manage Upcoming Trips"):
        #     add_trip_ui("upcoming_trips")
        
        if st.button("Logout"):
            from auth import logout
            logout()
        
        st.write(f"Logged in as {st.session_state.username}")
        st.write(f"API Mode: {API_MODE.capitalize()}")
        
def set_page(page):
    st.session_state.page = page

def render_special_mode_ui():
    with st.container():
        st.markdown('<div class="custom-container">', unsafe_allow_html=True)
        st.title("Voice-Assisted Travel Planner")
        st.markdown("Press the button and speak your travel query.")
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.button("🎤 Press to Speak", key="voice_record_button", help="Click and hold to record your voice", use_container_width=True)

        st.markdown("---")
        st.subheader("Instructions:")
        st.markdown("""
        1. Click the microphone button to start recording.
        2. Speak your travel query clearly.
        3. Release the button to stop recording.
        4. Wait for the AI to process your query and listen to the response.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
def add_trip_ui(trip_type):
    st.subheader(f"Add New {'Past' if trip_type == 'past_trips' else 'Upcoming'} Trip")
    destination = st.text_input("Destination")
    date = st.text_input("Date (e.g., 'Summer 2023')")
    departure = st.date_input("Departure Date")
    return_date = st.date_input("Return Date")
    flight_class = st.selectbox("Flight Class", ["Economy", "Premium Economy", "Business", "First Class"])
    stopover_city = st.text_input("Stopover City", value="")
    stopover_duration = st.text_input("Stopover Duration", value="")
    flight_preferences = st.multiselect("Flight Preferences", ["window seat", "aisle seat", "extra legroom", "vegetarian meal", "kosher meal", "lactose-free meal", "seafood meal"])
    hotel_name = st.text_input("Hotel Name")
    hotel_class = st.selectbox("Hotel Class", ["3-star", "4-star", "5-star"])
    hotel_nights = st.number_input("Number of Nights", min_value=1)
    hotel_location = st.text_input("Hotel Location")
    hotel_preferences = st.multiselect("Hotel Preferences", ["non-smoking", "high floor", "city view", "ocean view", "private pool villa", "yoga classes", "gym access", "business center", "on-site spa", "shuttle service"])

    if st.button("Add Trip"):
        new_trip = {
            "destination": destination,
            "date": date,
            "flight": {
                "departure": str(departure),
                "return": str(return_date),
                "class": flight_class,
                "stopover": {"city": stopover_city, "duration": stopover_duration} if stopover_city else None,
                "preferences": flight_preferences
            },
            "hotel": {
                "name": hotel_name,
                "class": hotel_class,
                "nights": hotel_nights,
                "location": hotel_location,
                "preferences": hotel_preferences
            }
        }
        
        add_trip(trip_type, st.session_state.username, new_trip)
        st.success(f"New {'past' if trip_type == 'past_trips' else 'upcoming'} trip added successfully!")

def set_custom_carousel_css():
    st.markdown("""
    <style>
    .stForm {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
    }
    .stForm > div {
        flex: 1 !important;
        margin: 0 5px !important;
    }
    button.ef3psqc7 {
        width: 100% !important;
        background-color: #f0f2f6 !important;
        color: #333333 !important;
        border: none !important;
        padding: 10px !important;
        border-radius: 5px !important;
        cursor: pointer !important;
        transition: background-color 0.3s !important;
    }
    button.ef3psqc7:hover {
        background-color: #e0e2e6 !important;
    }
    .image-container {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        height: 300px !important;
        overflow: hidden !important;
        margin-bottom: 10px !important;
    }
    .image-container img {
        max-width: 100% !important;
        max-height: 100% !important;
        object-fit: contain !important;
    }
    </style>
    """, unsafe_allow_html=True)
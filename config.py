import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
USERS_FILE = 'users.json'
USER_PROFILES_FILE = 'user_profiles.json'
LOGO_PATH = "images/ease.png"
ICON_PATH = "images/icon.png"
CLAUDE_MODEL_ID = "claude-3-5-sonnet-20240620"
AWS_CLAUDE_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
API_MODE = os.getenv('API_MODE', 'huggingface')  # 'huggingface' or 'bedrock or native_claude'
USE_GOOGLE_MAPS = os.getenv('USE_GOOGLE_MAPS', 'False').lower() == 'true'
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
AMADEUS_CLIENT_ID = os.getenv('AMADEUS_CLIENT_ID')
AMADEUS_CLIENT_SECRET = os.getenv('AMADEUS_CLIENT_SECRET')
# Voyage prompt
VOYAGE_PROMPT = """You are TravelEase, a virtual travel assistant.You don't need to answer non-travel related queries or queries that don't have any context related to travel. Your purpose is to help users with 
travel-related queries and tasks. Provide concise, helpful responses while maintaining a friendly and professional tone. Use the user's past trip 
information, upcoming trip information, users credit card offers/partnerships, users preferences  to provide personalized recommendations and 
references when appropriate. In case the search intent is related to flight search, give the results you have and recommend user to use FlighSearch button from the sidebar"""

# Map categories
MAP_CATEGORIES = ['hotel', 'restaurant', 'attraction', 'landmark']
# Default mode
DEFAULT_MODE = os.getenv('DEFAULT_MODE', 'standard')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
S3_BUCKET = os.getenv('S3_BUCKET')
BYPASS_LOGIN = os.getenv('BYPASS_LOGIN', 'False').lower() == 'true'
BYPASS_USERNAME = os.getenv('BYPASS_USERNAME', 'renjith')
EMERGENCY_SERVICES = ['Police', 'Hospital', 'Fire Department', 'Embassy']

import streamlit as st
from PIL import Image
import io
import base64
# from api_client import analyze_image
import json
import logging
from io import BytesIO
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_REGION, AWS_SECRET_ACCESS_KEY,AWS_SESSION_TOKEN
from jsonschema import validate

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def set_page(page):
    st.session_state.page = page

def format_analysis_response(response):
    st.title(f"Destination Spotlight: {response['identified_location']}")
    
    # Overview
    st.header("📍 Overview")
    st.write(response['main_elements']['overall_scene'])
   # st.write(f"**Confidence Level:** {response['confidence_level']}")

    # Distinctive Features
    st.header("🏛️ Distinctive Features")
    for feature in response['distinctive_features']:
        st.write(f"- {feature}")

    # Historical and Cultural Information
    st.header("📜 Historical & Cultural Significance")
    st.write(response['historical_info'])
    st.write("**Cultural Significance:**", response['cultural_significance'])

    # Architecture and Natural Elements
    st.header("🏰 Architecture & Natural Beauty")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Architecture")
        st.write(response['main_elements']['architecture'])
    with col2:
        st.subheader("Natural Elements")
        st.write(response['main_elements']['natural_elements'])

    # Tourist Activities
    st.header("🎭 Top Tourist Activities")
    activities = response['tourist_activities']
    for idx, activity in enumerate(activities, 1):
        st.write(f"{idx}. {activity}")

    # Accommodation and Dining
    st.header("🏨 Where to Stay & What to Eat")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Recommended Hotels")
        for hotel in response['nearby_hotels']:
            st.write(f"- {hotel}")
    with col2:
        st.subheader("Local Cuisine")
        for dish in response['local_cuisine']:
            st.write(f"- {dish}")

    # Additional Thoughts
    st.header("💡 Interesting Note")
    st.info(response['initial_thoughts'])

    # Call to Action
    st.success("Ready to plan your trip? Check out our travel planning resources!")
    # if st.button("Start Planning"):
    #     st.button("Chat", on_click=set_page, args=("chat",))

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def compress_image(image, max_size=(1024, 1024), quality=95):
    """Compress and resize an image to reduce its size while maintaining quality."""
    img = image.copy()
    img.thumbnail(max_size)
    
    # Convert to RGB if the image has an alpha channel
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
        img = background
    
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=quality)
    return buffered.getvalue()

def image_to_base64(image_bytes):
    """Convert image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')

def get_image_download_link(img, filename, text):
    """Generate a download link for the given image."""
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=95)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/jpg;base64,{img_str}" download="{filename}">{text}</a>'
    return href

schema = {
    "type": "object",
    "properties": {
        "identified_location": {"type": "string"},
        "main_elements": {
            "type": "object",
            "properties": {
                "overall_scene": {"type": "string"},
                "architecture": {"type": "string"},
                "natural_elements": {"type": "string"}
            },
            "required": ["overall_scene", "architecture", "natural_elements"]
        },
        "distinctive_features": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence_level": {"type": "string"},
        "historical_info": {"type": "string"},
        "cultural_significance": {"type": "string"},
        "nearby_hotels": {
            "type": "array",
            "items": {"type": "string"}
        },
        "local_cuisine": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tourist_activities": {
            "type": "array",
            "items": {"type": "string"}
        },
        "initial_thoughts": {"type": "string"}
    },
    "required": [
        "identified_location", "main_elements", "distinctive_features",
        "confidence_level", "historical_info", "nearby_hotels",
        "local_cuisine", "tourist_activities", "initial_thoughts"
    ]
}

def analyze_image(client, image_base64):
    prompt = """
    Analyze the following image and provide a detailed response in the exact JSON format specified below. Ensure all fields are present in your response, even if you're not certain about some information. Use "N/A" for any fields where you cannot provide information.

    {
        "identified_location": "string",
        "main_elements": {
            "overall_scene": "string",
            "architecture": "string",
            "natural_elements": "string"
        },
        "distinctive_features": ["string", "string", "string"],
        "confidence_level": "string",
        "historical_info": "string",
        "cultural_significance": "string",
        "nearby_hotels": ["string", "string", "string"],
        "local_cuisine": ["string", "string", "string"],
        "tourist_activities": ["string", "string", "string", "string", "string"],
        "initial_thoughts": "string"
    }

    Provide the following information:
    1. identified_location: The name of the location or landmark you've identified.
    2. main_elements: Describe the overall scene, architectural style and features, and any natural elements present.
    3. distinctive_features: List 3 unique features that help identify the location.
    4. confidence_level: Your level of confidence in the identification (e.g., "High", "Medium", "Low").
    5. historical_info: Brief historical information about the location.
    6. cultural_significance: Information about the cultural importance of the place.
    7. nearby_hotels: List 3 nearby hotels for visitors.
    8. local_cuisine: List 3 types of local cuisine or restaurants to try.
    9. tourist_activities: List 5 activities tourists can do in the area.
    10. initial_thoughts: Any interesting notes or initial impressions about the location.

    Ensure your response is a valid JSON object matching the structure provided above.
    """

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    })

    try:
        response = client.invoke_model(
            body=body,
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response.get('body').read())
        analysis_result = json.loads(response_body['content'][0]['text'])

        logger.info("Response received successfully")
        return analysis_result

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response: {str(e)}")
        raise ValueError("Invalid JSON response from the model")

    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        raise

def image_search_page():
    st.title("Search by Image")

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "webp"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption='Uploaded Image.', use_column_width=True)
        
        if st.button("Analyze Image"):
            with st.spinner('Analyzing image...'):
                base64_image = encode_image(uploaded_file)
                session = boto3.Session(
                    # aws_access_key_id=AWS_ACCESS_KEY_ID,
                    # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    # aws_session_token=AWS_SESSION_TOKEN,
                    # region_name=AWS_REGION
                )
                bedrock = session.client('bedrock-runtime')
                response = analyze_image(bedrock, base64_image)
                
                format_analysis_response(response)

                if st.button("Plan a Trip to This Location"):
                    chat_message = f"I've found an interesting location: {response['identified_location']}. Here's some information about it:\n\n"
                    chat_message += f"• Overview: {response['main_elements']['overall_scene']}\n"
                    chat_message += f"• Historical Significance: {response['historical_info']}\n"
                    chat_message += f"• Cultural Significance: {response['cultural_significance']}\n"
                    chat_message += f"• Top Activities: {', '.join(response['tourist_activities'][:3])}\n"
                    
                    if 'chat_history' not in st.session_state:
                        st.session_state.chat_history = []
                    st.session_state.chat_history.append({"role": "assistant", "content": chat_message})
                    
                    st.session_state.prompt_trip_planning = True
                    st.session_state.last_identified_location = response['identified_location']
                    st.session_state.page = "chat"
                    
                    st.success("Great! Let's plan your trip. Click on the 'Chat' button in the sidebar to start planning.")

if __name__ == "__main__":
    image_search_page()
    
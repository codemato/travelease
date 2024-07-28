import googlemaps
from googlemaps import exceptions
import logging
from config import GOOGLE_MAPS_API_KEY, API_MODE, CLAUDE_MODEL_ID
import json

logger = logging.getLogger(__name__)

class GoogleReviews:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        
    def get_place_id(self, place_name, location=None):
        try:
            places_result = self.gmaps.places(query=place_name, location=location)
            if places_result['results']:
                return places_result['results'][0]['place_id']
            else:
                logger.warning(f"No place found for: {place_name}")
                return None
        except exceptions.ApiError as e:
            logger.error(f"Error fetching place ID: {str(e)}")
            return None

    def get_reviews(self, place_name, location=None, max_reviews=5):
        place_id = self.get_place_id(place_name, location)
        if not place_id:
            return None

        try:
            place_details = self.gmaps.place(place_id=place_id, fields=['name', 'rating', 'review'])
            if 'result' in place_details:
                result = place_details['result']
                reviews = result.get('reviews', [])
                return {
                    'name': result.get('name'),
                    'rating': result.get('rating'),
                    'reviews': [
                        {
                            'author_name': review.get('author_name'),
                            'rating': review.get('rating'),
                            'text': review.get('text'),
                            'time': review.get('time')
                        } for review in reviews[:max_reviews]
                    ]
                }
            else:
                logger.warning(f"No details found for place: {place_name}")
                return None
        except exceptions.ApiError as e:
            logger.error(f"Error fetching reviews: {str(e)}")
            return None

    def summarize_reviews(self, reviews, api_client):
        if not reviews:
            logger.info("No reviews found to summarize.")
            return {
                "summary": "No reviews available for this location.",
                "positive_points": [],
                "negative_points": [],
                "score": 0
            }

        review_texts = [review['text'] for review in reviews]
        combined_reviews = "\n".join(review_texts)

        prompt = f"""
        Analyze the following hotel reviews and provide:
        1. A concise summary of the overall sentiment
        2. Key positive points
        3. Key negative points (if any)
        4. An overall review score out of 5 based on the sentiment

        The response should be a JSON object. If no reviews are found, return an object with empty fields and a score of 0.

        Reviews:
        {combined_reviews}

        Response (JSON format):
        {{
            "summary": "Your summary here",
            "positive_points": ["Point 1", "Point 2", ...],
            "negative_points": ["Point 1", "Point 2", ...],
            "score": Your score out of 5
        }}
        """

        try:
            if API_MODE == 'bedrock':
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
                response = api_client.invoke_model(
                    body=body,
                    modelId=CLAUDE_MODEL_ID,
                    accept='application/json',
                    contentType='application/json'
                )
                response_body = json.loads(response.get('body').read())
                summary_json = response_body['content'][0]['text']
            elif API_MODE == 'huggingface':
                response = api_client.chat(prompt)
                summary_json = str(response)
            elif API_MODE == 'native_claude':
                response = api_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                summary_json = response.content[0].text

            summary_json = summary_json.strip()
            if summary_json.startswith("```json"):
                summary_json = summary_json[7:-3]
            json_end = summary_json.rfind('}')
            if json_end != -1:
                summary_json = summary_json[:json_end+1]
                
            try:
                summary = json.loads(summary_json)
                return summary
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                logger.error(f"Raw response: {summary_json}")
                return {
                    "summary": "Error processing reviews.",
                    "positive_points": [],
                    "negative_points": [],
                    "score": 0
                }
        except Exception as e:
            logger.error(f"Error summarizing reviews using LLM: {str(e)}")
            return {
                "summary": "Error processing reviews.",
                "positive_points": [],
                "negative_points": [],
                "score": 0
            }

def get_hotel_reviews(hotel_name, location=None, max_reviews=5):
    reviewer = GoogleReviews()
    return reviewer.get_reviews(hotel_name, location, max_reviews)

def get_hotel_reviews_summary(hotel_name, api_client, location=None, max_reviews=5):
    reviewer = GoogleReviews()
    reviews_data = reviewer.get_reviews(hotel_name, location, max_reviews)
    
    if reviews_data:
        summary = reviewer.summarize_reviews(reviews_data['reviews'], api_client)
        if summary:
            return {
                'name': reviews_data['name'],
                'rating': reviews_data.get('rating', 0),
                'summary': summary
            }
        else:
            logger.warning("Failed to generate summary")
            return {
                'name': reviews_data['name'],
                'rating': reviews_data.get('rating', 0),
                'summary': {
                    "summary": "No review summary available.",
                    "positive_points": [],
                    "negative_points": [],
                    "score": 0
                }
            }
    else:
        logger.warning(f"No reviews found for {hotel_name}")
        return {
            'name': hotel_name,
            'rating': 0,
            'summary': {
                "summary": "No reviews available for this location.",
                "positive_points": [],
                "negative_points": [],
                "score": 0
            }
        }
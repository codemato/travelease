import requests
import base64
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmadeusAPI:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://test.api.amadeus.com"
        self.token = None
        self.token_expiry = 0

    def _authenticate(self):
        auth_url = f"{self.base_url}/v1/security/oauth2/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {"Authorization": f"Basic {encoded_credentials}"}
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        auth_data = response.json()
        self.token = auth_data["access_token"]
        self.token_expiry = time.time() + auth_data["expires_in"] - 60  # Subtract 60 seconds for safety

    def _ensure_token(self):
        if not self.token or time.time() > self.token_expiry:
            self._authenticate()

    def search_flights(self, origin: str, destination: str, departure_date: str, return_date: str):
        self._ensure_token()
        endpoint = f"{self.base_url}/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "returnDate": return_date,
            "adults": 1,
            "max": 5
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
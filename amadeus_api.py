from amadeus import Client, ResponseError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AmadeusAPI:
    def __init__(self, client_id, client_secret):
        try:
            self.amadeus = Client(client_id=client_id, client_secret=client_secret)
            logger.info("Amadeus client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Amadeus client: {str(e)}")
            raise

    def search_flights(self, origin, destination, departure_date, return_date=None):
        try:
            logger.info(f"Searching flights: {origin} to {destination}, departure: {departure_date}, return: {return_date}")
            if return_date:
                response = self.amadeus.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=departure_date,
                    returnDate=return_date,
                    adults=1
                )
            else:
                response = self.amadeus.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=departure_date,
                    adults=1
                )
            logger.info(f"Flight search successful. Found {len(response.data)} results.")
            return response.data
        except ResponseError as error:
            logger.error(f"Amadeus API ResponseError: {error}")
            raise Exception(f"Amadeus API error: {error}")
        except Exception as e:
            logger.error(f"Unexpected error in flight search: {str(e)}")
            raise

    def get_airport_code(self, city_name):
        try:
            logger.info(f"Getting airport code for city: {city_name}")
            response = self.amadeus.reference_data.locations.get(
                keyword=city_name,
                subType=Client.location.airport
            )
            if response.data:
                logger.info(f"Found airport code: {response.data[0]['iataCode']}")
                return response.data[0]['iataCode']
            logger.warning(f"No airport code found for city: {city_name}")
            return None
        except ResponseError as error:
            logger.error(f"Amadeus API ResponseError in get_airport_code: {error}")
            raise Exception(f"Amadeus API error: {error}")
        except Exception as e:
            logger.error(f"Unexpected error in get_airport_code: {str(e)}")
            raise

def format_flight_results(flights):
    formatted_results = []
    for flight in flights:
        result = {
            "price": f"{flight['price']['total']} {flight['price']['currency']}",
            "itineraries": []
        }
        for itinerary in flight['itineraries']:
            segments = []
            for segment in itinerary['segments']:
                segments.append({
                    "departure": {
                        "iataCode": segment['departure']['iataCode'],
                        "at": segment['departure']['at']
                    },
                    "arrival": {
                        "iataCode": segment['arrival']['iataCode'],
                        "at": segment['arrival']['at']
                    },
                    "carrierCode": segment['carrierCode']
                })
            result['itineraries'].append(segments)
        formatted_results.append(result)
    return formatted_results
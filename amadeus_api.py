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

    def search_flights(self, origin, destination, departure_date, return_date=None, max_results=10):
        try:
            logger.info(f"Searching flights: {origin} to {destination}, departure: {departure_date}, return: {return_date}, max results: {max_results}")
            
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": 1,
                "max": max_results
            }
            
            if return_date:
                params["returnDate"] = return_date

            response = self.amadeus.shopping.flight_offers_search.get(**params)
            
            if response is None:
                logger.error("Amadeus API returned None response")
                return []
            
            if not hasattr(response, 'data'):
                logger.error(f"Unexpected response format from Amadeus API: {response}")
                return []
            
            logger.info(f"Flight search successful. Found {len(response.data)} results.")
            return response.data[:max_results]  # Ensure we don't exceed max_results
        
        except ResponseError as error:
            logger.error(f"Amadeus API ResponseError: {error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in flight search: {str(e)}")
            return []

    # ... (rest of the class remains the same)

def format_flight_results(flights):
    if not flights:
        logger.warning("No flights to format")
        return []

    formatted_results = []
    for i, flight in enumerate(flights):
        try:
            logger.debug(f"Formatting flight {i+1}/{len(flights)}")
            
            if 'price' not in flight:
                logger.error(f"Flight {i+1} is missing 'price' key")
                continue
            
            if 'total' not in flight['price'] or 'currency' not in flight['price']:
                logger.error(f"Flight {i+1} has incomplete price information")
                continue

            result = {
                "price": f"{flight['price']['total']} {flight['price']['currency']}",
                "itineraries": []
            }

            if 'itineraries' not in flight:
                logger.error(f"Flight {i+1} is missing 'itineraries' key")
                continue

            for j, itinerary in enumerate(flight['itineraries']):
                segments = []
                if 'segments' not in itinerary:
                    logger.error(f"Itinerary {j+1} in flight {i+1} is missing 'segments' key")
                    continue

                for k, segment in enumerate(itinerary['segments']):
                    try:
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
                    except KeyError as e:
                        logger.error(f"Segment {k+1} in itinerary {j+1} of flight {i+1} is missing key: {e}")
                        continue

                result['itineraries'].append(segments)
            formatted_results.append(result)
        except KeyError as e:
            logger.error(f"KeyError while formatting flight {i+1}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while formatting flight {i+1}: {e}")
    
    logger.info(f"Formatted {len(formatted_results)} flights successfully")
    return formatted_results
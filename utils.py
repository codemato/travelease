import re
from collections import Counter

def extract_location(prompt):
    indicators = ['in', 'at', 'near', 'from', 'to', 'of']
    
    sentences = re.split(r'[.!?]+', prompt)
    
    locations = []
    for sentence in sentences:
        words = sentence.split()
        for i, word in enumerate(words):
            if word.lower() in indicators and i + 1 < len(words):
                if words[i + 1][0].isupper():
                    location = ' '.join(words[i + 1:])
                    location = re.sub(r'[,.:].*$', '', location)
                    location = re.sub(r'\s+(in|at|near|from|to|of).*$', '', location)
                    locations.append(location.strip())

    if not locations:
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', prompt)
        locations = [word for word in capitalized_words if word not in ['Voyage', 'Past', 'Upcoming']]

    location_counts = Counter(locations)
    
    return location_counts.most_common(1)[0][0] if location_counts else None

def format_trip_details(trip):
    trip_details = f"Destination: {trip['destination']}, Date: {trip['date']}\n"
    trip_details += f"  Flight: {trip['flight']['class']} class, Departure: {trip['flight']['departure']}, Return: {trip['flight']['return']}\n"
    if trip['flight']['stopover']:
        trip_details += f"    Stopover: {trip['flight']['stopover']['city']}, Duration: {trip['flight']['stopover']['duration']}\n"
    trip_details += f"    Preferences: {', '.join(trip['flight']['preferences'])}\n"
    trip_details += f"  Hotel: {trip['hotel']['name']}, {trip['hotel']['class']}, Location: {trip['hotel']['location']}\n"
    trip_details += f"    Preferences: {', '.join(trip['hotel']['preferences'])}\n"
    return trip_details

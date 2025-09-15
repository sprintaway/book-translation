import requests
import json
from collections import Counter
import time
from geopy.geocoders import Nominatim

def get_taxi_availability():
    """
    Fetch taxi availability data from Data.gov.sg Taxi Availability API from LTA
    
    Returns:
        dict: Response data containing taxi locations and count
    """
    
    url = "https://api.data.gov.sg/v1/transport/taxi-availability"
    

    try:
        # Make the API request
        response = requests.get(url)
        response.raise_for_status()  
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def get_location_name(lat, lon):
    """
    Get location name from coordinates using geopy reverse geocoding
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
    
    Returns:
        str: Location name or coordinates if geocoding fails
    """
    try:
        # I will be using geopy which is free but rate-limited, can also use google map api but that requires API key and may not be free after certain usage

        # From documentation https://geopy.readthedocs.io/en/stable/,  

        # To find the address corresponding to a set of coordinates:
        # from geopy.geocoders import Nominatim
        # geolocator = Nominatim(user_agent="specify_your_app_name_here")
        # location = geolocator.reverse("52.509669, 13.376294")
        # print(location.address)
        # Potsdamer Platz, Mitte, Berlin, 10117, Deutschland, European Union
        # print((location.latitude, location.longitude))
        # (52.5094982, 13.3765983)
        # print(location.raw)
        # {'place_id': '654513', 'osm_type': 'node', ...}

        geolocator = Nominatim(user_agent="TaxiAvailabilityChecker")
        location = geolocator.reverse(f"{lat}, {lon}")
        return location.address
    
    except Exception as e:
        print(f"Error geocoding {lat}, {lon}: {e}")
        return f"Lat: {lat}, Lon: {lon}"

def display_taxi_data(data):
    """
    Extract and display the total number of available taxis and lists top 10 areas with highest concentration of taxis
    
    Args:
        data (dict): API response data
    """
    if not data:
        print("No data received from API")
        return
    
    try:
        # Extract taxi count from the GeoJSON response

        # In data.gov.sg, the structure you get from curl is

        # {
        # "type": "FeatureCollection",
        # "crs": {
        #     "type": "link",
        #     "properties": {
        #     "href": "http://spatialreference.org/ref/epsg/4326/ogcwkt/",
        #     "type": "ogcwkt"
        #     }
        # },
        # "features": [
        #     {
        #     "type": "Feature",
        #     "geometry": {
        #         "type": "MultiPoint",
        #         "coordinates": [
        #   [
        #     103.61448,
        #     1.26637
        #   ],
        #   [
        #     103.6251772195,
        #     1.3043662603
        #   ],
        #          ............
        #        },
        #       "properties": {
        #         "timestamp": "2025-09-15T13:09:35+08:00",
        #         "taxi_count": 2176,
        #         "api_info": {
        #           "status": "healthy"
        #         }
        #       }
        #     }
        #   ]
        # }

        features = data.get('features', [])
        
        if not features:
            print("No taxi data available")
            return
        
        # Get the first feature 
        feature = features[0]

        # Get taxi count
        properties = feature.get('properties', {})
        taxi_count = properties.get('taxi_count', 0)

        print(f"Total available taxis: {taxi_count:}")

        # Get coordinates
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates', [])

        if not coordinates:
            print("No coordinate data available")
            return
        

        # Need to round coordinates to 2 dp as shown in test output, currently coordinates are in the form [103.61448, 1.26637] for example
        two_dp_coordinates = []
        
        for i in coordinates:
            lat = round(i[1], 2)
            lon = round(i[0], 2)
            two_dp_coordinates.append((lat, lon))

        # Return top 10 taxi counts for each unique pair of [lat, lon]
        counts = Counter(two_dp_coordinates)
        top_10_counts = counts.most_common(10)

        print("Top 10 areas with the most taxis:")

        # top_10_counts looks like [((lat, lon), count), ((lat, lon), count), ....]
        for i in range(len(top_10_counts)):
            (lat, lon) = top_10_counts[i][0]
            count = top_10_counts[i][1]

            location_name = get_location_name(lat, lon)

            # Add a small delay between requests to be respectful to the API
            time.sleep(0.1)

            map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            
            print(f"{i+1}. Lat: {lat}, Lon: {lon} - {count} taxis")
            print(f"   Location: {location_name}")
            print(f"   Google Maps: {map_link}")

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing API response: {e}")
        print("Raw response structure:")
        print(json.dumps(data, indent=2)[:500] + "..." if len(str(data)) > 500 else json.dumps(data, indent=2))

def main():
    """
    Main function to run the taxi availability checker
    """
    
    data = get_taxi_availability()
    display_taxi_data(data)

if __name__ == "__main__":
    main()
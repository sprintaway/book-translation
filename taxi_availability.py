import requests
import json
from datetime import datetime
import sys

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

def display_taxi_count(data):
    """
    Extract and display the total number of available taxis
    
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
        #         "coordinates":
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
        properties = feature.get('properties', {})
        taxi_count = properties.get('taxi_count', 0)
        
        # Display the results
        print(f"Total Available Taxis: {taxi_count:}")
        
        
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing API response: {e}")
        print("Raw response structure:")
        print(json.dumps(data, indent=2)[:500] + "..." if len(str(data)) > 500 else json.dumps(data, indent=2))

def main():
    """
    Main function to run the taxi availability checker
    """
    
    data = get_taxi_availability()
    display_taxi_count(data)

if __name__ == "__main__":
    main()
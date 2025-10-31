import logging
import requests
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Configure logger for this module
logger = logging.getLogger(__name__)


def search_food(query: str, use_fuzzy: bool = True) -> list[dict]:
    # Base URL for FSVO API
    base_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS"
    endpoint = f"{base_url}/webresources/BLV-api/foods"
    
    # Parameters for the API request
    params = {
        "search": query,
        "lang": "en"
    }
    
    try:
        # Make GET request to the API
        response = requests.get(endpoint, params=params, timeout=10)
        
        # Raise an exception for non-200 status codes
        response.raise_for_status()
        
        # Parse JSON response - API returns a flat list of dictionaries
        data = response.json()
        
        # Extract food items using list comprehension
        # API structure: [{"foodName": "...", "id": ...}, ...]
        results = [
            {"name": item["foodName"], "dbid": item["id"]}
            for item in data
            if isinstance(item, dict) and "foodName" in item and "id" in item
        ]
        
        # If we have results and fuzzy search is enabled, rank them by similarity
        if results and use_fuzzy and FUZZY_AVAILABLE:
            # Sort results by fuzzy match score (higher is better)
            results.sort(
                key=lambda x: fuzz.partial_ratio(query.lower(), x["name"].lower()),
                reverse=True
            )
        
        return results
        
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, HTTP errors, etc.
        logger.error(f"Failed to connect to FSVO API: {str(e)}")
        return []
    except ValueError as e:
        # Handle JSON parsing errors
        logger.error(f"Failed to parse API response: {str(e)}")
        return []


def get_food_details(dbid: int) -> dict | None:
    # Base URL for FSVO API
    base_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS"
    endpoint = f"{base_url}/webresources/BLV-api/food/{dbid}"
    
    # Parameters for the API request
    params = {
        "lang": "en"
    }
    
    # Required macro component names in the API response (from values array)
    # The API uses component names like "Energy, kilocalories", "Protein", etc.
    required_components = {
        "Energy, kilocalories": "kcal",
        "Protein": "protein",
        "Fat, total": "fat",
        "Carbohydrates, available": "carbs"
    }
    
    try:
        # Make GET request to the API
        response = requests.get(endpoint, params=params, timeout=10)
        
        # Raise an exception for non-200 status codes
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # The API returns nutritional data in a 'values' array
        # Each value has a 'component' object with 'name' and a 'value' field
        if not isinstance(data, dict) or "values" not in data:
            logger.error(f"Could not find 'values' array in API response for dbid {dbid}")
            return None
        
        values_array = data["values"]
        
        if not isinstance(values_array, list):
            logger.error(f"'values' is not a list in API response for dbid {dbid}")
            return None
        
        # Extract macro values from the values array
        found_components = {}
        for value_item in values_array:
            if not isinstance(value_item, dict) or "component" not in value_item:
                continue
                
            component = value_item["component"]
            if not isinstance(component, dict) or "name" not in component:
                continue
                
            component_name = component["name"]
            
            # Check if this component matches any required macro
            if component_name in required_components:
                result_key = required_components[component_name]
                
                # Extract the value
                if "value" in value_item:
                    try:
                        found_components[result_key] = float(value_item["value"])
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid value for '{component_name}' (dbid {dbid}): {value_item.get('value')}")
                        return None
                else:
                    logger.error(f"Missing 'value' field for component '{component_name}' (dbid {dbid})")
                    return None
        
        # Check if all required macros were found
        missing_macros = [result_key for result_key in required_components.values() 
                         if result_key not in found_components]
        
        if missing_macros:
            logger.error(f"Missing required macros for dbid {dbid}: {missing_macros}. Found: {list(found_components.keys())}")
            return None
        
        # All required macros were found and extracted successfully
        return found_components
            
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, HTTP errors, etc.
        logger.error(f"Failed to connect to FSVO API for dbid {dbid}: {str(e)}")
        return None
    except ValueError as e:
        # Handle JSON parsing errors
        logger.error(f"Failed to parse API response for dbid {dbid}: {str(e)}")
        return None


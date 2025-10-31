"""
API Client Module for FSVO Public API

This module provides functions to interact with the Swiss Federal Food Safety
and Veterinary Office (FSVO) Public API for food search and nutritional data retrieval.
"""

import requests
from typing import List, Dict, Optional
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


def search_food(query: str, use_fuzzy: bool = True) -> List[Dict]:
    """
    Search for foods in the FSVO database by name.
    
    This function makes a GET request to the FSVO API to search for foods matching
    the given query string. It returns a list of dictionaries containing the food
    name and database ID (dbid) for each matching result. Results are optionally
    sorted by fuzzy match score if fuzzywuzzy is available.
    
    Args:
        query (str): The food name or search term to query.
        use_fuzzy (bool): If True and fuzzywuzzy is available, sort results by 
                         similarity score (default: True).
        
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - 'name' (str): The food name
            - 'dbid' (int): The unique database ID for the food
            
        Returns an empty list if the API call fails or returns no results.
    
    Example:
        >>> results = search_food("chicken")
        >>> print(results)
        [{'name': 'Chicken, breast, without skin, raw', 'dbid': 349589}, ...]
    """
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
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            
            # Initialize result list
            results = []
            
            # Handle different possible response structures
            if isinstance(data, list):
                # If response is a list, iterate through items
                for item in data:
                    food_dict = {}
                    
                    if isinstance(item, dict):
                        # Handle actual API structure: {"foodName": "...", "id": ...}
                        if "foodName" in item:
                            food_dict["name"] = item["foodName"]
                        elif "name" in item:
                            food_dict["name"] = item["name"]
                        
                        # Use 'id' field (not 'foodid') for the API endpoint
                        if "id" in item:
                            food_dict["dbid"] = item["id"]
                        elif "dbid" in item:
                            food_dict["dbid"] = item["dbid"]
                        
                        # Handle nested structure: [{"food": {"name": "...", "dbid": ...}}]
                        if "food" in item and isinstance(item["food"], dict):
                            food_item = item["food"]
                            if "foodName" in food_item:
                                food_dict["name"] = food_item["foodName"]
                            elif "name" in food_item:
                                food_dict["name"] = food_item["name"]
                            if "id" in food_item:
                                food_dict["dbid"] = food_item["id"]
                            elif "dbid" in food_item:
                                food_dict["dbid"] = food_item["dbid"]
                    
                    # Only add to results if both name and dbid are present
                    if "name" in food_dict and "dbid" in food_dict:
                        results.append(food_dict)
            
            # Handle case where response is a single dict with a list inside
            elif isinstance(data, dict):
                # Check for common keys that might contain the food list
                food_list = None
                for key in ["foods", "results", "data", "items"]:
                    if key in data and isinstance(data[key], list):
                        food_list = data[key]
                        break
                
                if food_list:
                    for item in food_list:
                        food_dict = {}
                        if isinstance(item, dict):
                            # Handle actual API structure: {"foodName": "...", "id": ...}
                            if "foodName" in item:
                                food_dict["name"] = item["foodName"]
                            elif "name" in item:
                                food_dict["name"] = item["name"]
                            
                            # Use 'id' field (not 'foodid') for the API endpoint
                            if "id" in item:
                                food_dict["dbid"] = item["id"]
                            elif "dbid" in item:
                                food_dict["dbid"] = item["dbid"]
                            
                            if "name" in food_dict and "dbid" in food_dict:
                                results.append(food_dict)
            
            # If we have results and fuzzy search is enabled, rank them by similarity
            if results and use_fuzzy and FUZZY_AVAILABLE:
                # Sort results by fuzzy match score (higher is better)
                results.sort(
                    key=lambda x: fuzz.partial_ratio(query.lower(), x["name"].lower()),
                    reverse=True
                )
            
            return results
            
        else:
            # Non-200 status code
            print(f"Error: API returned status code {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, etc.
        print(f"Error: Failed to connect to FSVO API - {str(e)}")
        return []
    except ValueError as e:
        # Handle JSON parsing errors
        print(f"Error: Failed to parse API response - {str(e)}")
        return []
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Error: Unexpected error occurred - {str(e)}")
        return []


def get_food_details(dbid: int) -> Optional[Dict]:
    """
    Fetch detailed nutritional information for a specific food by its database ID.
    
    This function makes a GET request to the FSVO API to retrieve detailed
    nutritional information for a food item. It extracts the four core macronutrients:
    calories, protein, fat, and carbohydrates.
    
    Args:
        dbid (int): The unique database ID of the food item.
        
    Returns:
        Optional[Dict]: A dictionary containing nutritional values:
            - 'kcal' (float): Energy in kilocalories per 100g
            - 'protein' (float): Protein in grams per 100g
            - 'fat' (float): Total fat in grams per 100g
            - 'carbs' (float): Available carbohydrates in grams per 100g
            
        Returns None if:
            - The API call fails (non-200 status code or network error)
            - Any of the four required macro values are missing from the response
            - The response cannot be parsed as JSON
    
    Example:
        >>> details = get_food_details(123)
        >>> print(details)
        {'kcal': 165.0, 'protein': 31.0, 'fat': 3.6, 'carbs': 0.0}
    """
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
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            
            # Initialize result dictionary
            result = {}
            
            # The API returns nutritional data in a 'values' array
            # Each value has a 'component' object with 'name' and a 'value' field
            if isinstance(data, dict) and "values" in data:
                values_array = data["values"]
                
                if not isinstance(values_array, list):
                    print(f"Error: 'values' is not a list in API response")
                    return None
                
                # Extract macro values from the values array
                found_components = {}
                for value_item in values_array:
                    if isinstance(value_item, dict) and "component" in value_item:
                        component = value_item["component"]
                        if isinstance(component, dict) and "name" in component:
                            component_name = component["name"]
                            
                            # Check if this component matches any required macro
                            for req_component, result_key in required_components.items():
                                if component_name == req_component:
                                    # Extract the value
                                    if "value" in value_item:
                                        try:
                                            found_components[result_key] = float(value_item["value"])
                                        except (ValueError, TypeError):
                                            print(f"Error: Invalid value for '{component_name}': {value_item.get('value')}")
                                            return None
                
                # Check if all required macros were found
                missing_macros = [result_key for result_key in required_components.values() 
                                 if result_key not in found_components]
                
                if missing_macros:
                    print(f"Error: Missing required macros: {missing_macros}")
                    print(f"Found components: {list(found_components.keys())}")
                    return None
                
                # All required macros were found and extracted successfully
                return found_components
            else:
                # Could not find values array in the response
                print(f"Error: Could not find 'values' array in API response")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return None
                
        else:
            # Non-200 status code
            print(f"Error: API returned status code {response.status_code} for dbid {dbid}")
            return None
            
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, etc.
        print(f"Error: Failed to connect to FSVO API for dbid {dbid} - {str(e)}")
        return None
    except ValueError as e:
        # Handle JSON parsing errors
        print(f"Error: Failed to parse API response for dbid {dbid} - {str(e)}")
        return None
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Error: Unexpected error occurred while fetching food details for dbid {dbid} - {str(e)}")
        return None


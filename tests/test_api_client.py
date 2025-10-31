"""
Unit Tests for API Client Module

Tests for FSVO API integration functions including:
- Food search functionality
- Food detail retrieval
- Error handling for API failures
"""

import pytest
import requests_mock
from src.api_client import search_food, get_food_details


def test_search_food_success():
    """
    Test successful food search with mocked API response.
    
    This test simulates a successful API call and verifies that the function
    correctly parses the JSON response and returns the expected format.
    """
    # Sample API response matching the user's example structure
    mock_response = [
        {"food": {"name": "Chicken Breast", "dbid": 123}},
        {"food": {"name": "Chicken Thigh", "dbid": 124}}
    ]
    
    # Expected output format
    expected_result = [
        {"name": "Chicken Breast", "dbid": 123},
        {"name": "Chicken Thigh", "dbid": 124}
    ]
    
    # Mock the API endpoint
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/foods"
    
    with requests_mock.Mocker() as m:
        # Mock successful GET request
        m.get(
            api_url,
            json=mock_response,
            status_code=200
        )
        
        # Call the function
        result = search_food("chicken")
        
        # Assertions
        assert result == expected_result
        assert len(result) == 2
        assert result[0]["name"] == "Chicken Breast"
        assert result[0]["dbid"] == 123
        assert result[1]["name"] == "Chicken Thigh"
        assert result[1]["dbid"] == 124


def test_search_food_failure():
    """
    Test food search failure handling with mocked 500 server error.
    
    This test simulates a server error (500) and verifies that the function
    returns an empty list and handles the error gracefully.
    """
    # Mock the API endpoint
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/foods"
    
    with requests_mock.Mocker() as m:
        # Mock 500 server error
        m.get(
            api_url,
            status_code=500,
            text="Internal Server Error"
        )
        
        # Call the function
        result = search_food("chicken")
        
        # Assertions
        assert result == []
        assert isinstance(result, list)
        assert len(result) == 0


def test_search_food_empty_response():
    """
    Test food search with empty API response.
    
    Edge case: API returns 200 but with an empty list.
    """
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/foods"
    
    with requests_mock.Mocker() as m:
        m.get(
            api_url,
            json=[],
            status_code=200
        )
        
        result = search_food("nonexistent")
        
        assert result == []
        assert isinstance(result, list)


def test_search_food_flat_structure():
    """
    Test food search with flat response structure (not nested).
    
    Edge case: API returns flat structure [{"name": "...", "dbid": ...}]
    instead of nested structure.
    """
    mock_response = [
        {"name": "Apple", "dbid": 456},
        {"name": "Banana", "dbid": 457}
    ]
    
    expected_result = [
        {"name": "Apple", "dbid": 456},
        {"name": "Banana", "dbid": 457}
    ]
    
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/foods"
    
    with requests_mock.Mocker() as m:
        m.get(
            api_url,
            json=mock_response,
            status_code=200
        )
        
        result = search_food("fruit")
        
        assert result == expected_result
        assert len(result) == 2


def test_get_food_details_success():
    """
    Test successful food details retrieval with mocked API response.
    
    This test simulates a successful API call and verifies that the function
    correctly parses the JSON response and extracts the four required macro values.
    """
    # Sample API response with full nutritional profile
    mock_response = {
        "food": {
            "name": "Chicken Breast",
            "dbid": 123,
            "Energy, kilocalories (kcal)": 165.0,
            "Protein (g)": 31.0,
            "Fat, total (g)": 3.6,
            "Carbohydrates, available (g)": 0.0
        }
    }
    
    # Expected output format
    expected_result = {
        "kcal": 165.0,
        "protein": 31.0,
        "fat": 3.6,
        "carbs": 0.0
    }
    
    # Mock the API endpoint
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/food/123"
    
    with requests_mock.Mocker() as m:
        # Mock successful GET request
        m.get(
            api_url,
            json=mock_response,
            status_code=200
        )
        
        # Call the function
        result = get_food_details(123)
        
        # Assertions
        assert result == expected_result
        assert result is not None
        assert "kcal" in result
        assert "protein" in result
        assert "fat" in result
        assert "carbs" in result
        assert result["kcal"] == 165.0
        assert result["protein"] == 31.0
        assert result["fat"] == 3.6
        assert result["carbs"] == 0.0


def test_get_food_details_missing_data():
    """
    Test food details retrieval with missing macro data.
    
    This test simulates a successful API response (200) but with the 'Protein (g)'
    key missing, which should cause the function to return None.
    """
    # Sample API response with missing Protein key
    mock_response = {
        "food": {
            "name": "Chicken Breast",
            "dbid": 123,
            "Energy, kilocalories (kcal)": 165.0,
            # "Protein (g)" is missing
            "Fat, total (g)": 3.6,
            "Carbohydrates, available (g)": 0.0
        }
    }
    
    # Mock the API endpoint
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/food/123"
    
    with requests_mock.Mocker() as m:
        # Mock successful GET request (200) but with missing data
        m.get(
            api_url,
            json=mock_response,
            status_code=200
        )
        
        # Call the function
        result = get_food_details(123)
        
        # Assertions - should return None because Protein is missing
        assert result is None


def test_get_food_details_api_failure():
    """
    Test food details retrieval failure handling with mocked 404 error.
    
    This test simulates a 404 Not Found error and verifies that the function
    returns None and handles the error gracefully.
    """
    # Mock the API endpoint
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/food/999"
    
    with requests_mock.Mocker() as m:
        # Mock 404 Not Found error
        m.get(
            api_url,
            status_code=404,
            text="Food not found"
        )
        
        # Call the function
        result = get_food_details(999)
        
        # Assertions
        assert result is None


def test_get_food_details_flat_structure():
    """
    Test food details retrieval with flat response structure (macros at top level).
    
    Edge case: API returns macros directly in the response dict, not nested.
    """
    # Sample API response with macros at top level
    mock_response = {
        "name": "Apple",
        "dbid": 456,
        "Energy, kilocalories (kcal)": 52.0,
        "Protein (g)": 0.3,
        "Fat, total (g)": 0.2,
        "Carbohydrates, available (g)": 14.0
    }
    
    # Expected output format
    expected_result = {
        "kcal": 52.0,
        "protein": 0.3,
        "fat": 0.2,
        "carbs": 14.0
    }
    
    # Mock the API endpoint
    api_url = "https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS/webresources/BLV-api/food/456"
    
    with requests_mock.Mocker() as m:
        # Mock successful GET request
        m.get(
            api_url,
            json=mock_response,
            status_code=200
        )
        
        # Call the function
        result = get_food_details(456)
        
        # Assertions
        assert result == expected_result
        assert result is not None
        assert result["kcal"] == 52.0
        assert result["protein"] == 0.3
        assert result["fat"] == 0.2
        assert result["carbs"] == 14.0


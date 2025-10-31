import pytest
import requests_mock
from src.api_client import search_food, get_food_details


def test_search_food_success():
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


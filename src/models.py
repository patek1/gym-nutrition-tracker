"""
Data Models Module

This module defines data structures and schemas used throughout the application.
"""

from typing import TypedDict, List, Optional


class FoodSearchResult(TypedDict):
    """Structure for food search results from API"""
    name: str
    dbid: int


class FoodDetails(TypedDict):
    """Structure for detailed food nutritional information"""
    dbid: int
    name: str
    kcal_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float
    matrixunitcode: Optional[str]


class UserGoals(TypedDict):
    """Structure for user's daily macro targets"""
    target_kcal: int
    target_protein: int
    target_carbs: int
    target_fat: int


class LoggedMeal(TypedDict):
    """Structure for a logged meal entry"""
    food_id: int
    food_name: str
    portion_size_g: float
    kcal_consumed: float
    protein_consumed: float
    carbs_consumed: float
    fat_consumed: float


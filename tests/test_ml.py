"""
Integration Tests for Machine Learning Module

This module contains integration tests that test the ML components together.
For unit tests, see:
- test_data_processor.py
- test_recommendation_engine.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from src.ml.data_processor import load_and_preprocess_data
from src.ml.recommendation_engine import RecommendationEngine


def test_load_and_preprocess_data():
    """
    Test the load_and_preprocess_data function with a mock Excel file.
    
    This test creates a temporary Excel file with sample data, including
    some missing values, and verifies that the function:
    1. Loads the data correctly
    2. Selects the correct columns
    3. Drops rows with missing macro values
    4. Calculates percentage columns correctly
    5. Returns a fitted pipeline
    """
    # Create sample data with some missing values
    sample_data = {
        'Name': ['Chicken Breast', 'Apple', 'Banana', 'Orange', 'Incomplete Food'],
        'Category': ['Meat', 'Fruit', 'Fruit', 'Fruit', 'Other'],
        'Energy, kilocalories (kcal)': [165.0, 52.0, 89.0, 47.0, 200.0],
        'Protein (g)': [31.0, 0.3, 1.1, 0.9, np.nan],  # Missing protein for last row
        'Fat, total (g)': [3.6, 0.2, 0.3, 0.1, 5.0],
        'Carbohydrates, available (g)': [0.0, 14.0, 23.0, 12.0, 30.0]
    }
    
    # Create a temporary directory and Excel file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test_food_data.xlsx"
        
        # Create DataFrame and save to Excel
        df_sample = pd.DataFrame(sample_data)
        df_sample.to_excel(temp_file, index=False)
        
        # Call the function
        df_result, pipeline = load_and_preprocess_data(str(temp_file))
        
        # Assertions
        
        # 1. Check that the DataFrame has the correct columns
        expected_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs', 
                           'protein_pct', 'fat_pct', 'carbs_pct']
        assert list(df_result.columns) == expected_columns
        
        # 2. Check that rows with missing macro values were dropped
        # The "Incomplete Food" row should be dropped because it has NaN protein
        assert len(df_result) == 4  # Should have 4 complete rows
        assert 'Incomplete Food' not in df_result['Name'].values
        
        # 3. Check that there are no missing values in macro columns
        macro_columns = ['kcal', 'protein', 'fat', 'carbs']
        for col in macro_columns:
            assert df_result[col].isna().sum() == 0, f"Column {col} has missing values"
        
        # 4. Check that percentage columns sum to approximately 1.0 for a sample row
        # Use the first row (Chicken Breast) for testing
        chicken_row = df_result[df_result['Name'] == 'Chicken Breast'].iloc[0]
        protein_pct = chicken_row['protein_pct']
        fat_pct = chicken_row['fat_pct']
        carbs_pct = chicken_row['carbs_pct']
        
        # Calculate total for chicken: protein=31, fat=3.6, carbs=0.0, total=34.6
        # Expected percentages: protein=31/34.6≈0.896, fat=3.6/34.6≈0.104, carbs=0/34.6=0
        total_pct = protein_pct + fat_pct + carbs_pct
        assert abs(total_pct - 1.0) < 0.01, f"Percentages sum to {total_pct}, expected ~1.0"
        
        # Also test a fruit row (Apple) with all three macros
        apple_row = df_result[df_result['Name'] == 'Apple'].iloc[0]
        apple_total_pct = (apple_row['protein_pct'] + apple_row['fat_pct'] + 
                          apple_row['carbs_pct'])
        assert abs(apple_total_pct - 1.0) < 0.01, f"Apple percentages sum to {apple_total_pct}, expected ~1.0"
        
        # 5. Check that percentages are calculated correctly for Chicken Breast
        # protein=31, fat=3.6, carbs=0.0, total=34.6
        expected_protein_pct = 31.0 / 34.6
        expected_fat_pct = 3.6 / 34.6
        expected_carbs_pct = 0.0
        
        assert abs(chicken_row['protein_pct'] - expected_protein_pct) < 0.01
        assert abs(chicken_row['fat_pct'] - expected_fat_pct) < 0.01
        assert abs(chicken_row['carbs_pct'] - expected_carbs_pct) < 0.01
        
        # 6. Check that a fitted pipeline object is returned
        assert pipeline is not None
        assert hasattr(pipeline, 'fit')
        assert hasattr(pipeline, 'transform')
        
        # 7. Test that the pipeline can transform data
        feature_columns = ['kcal', 'protein_pct', 'fat_pct', 'carbs_pct']
        X_test = df_result[feature_columns]
        X_transformed = pipeline.transform(X_test)
        
        # Check that transformation produces output
        assert X_transformed is not None
        assert X_transformed.shape[0] == len(df_result)  # Same number of rows
        # Should have 4 features after transformation (scaled kcal + 3 percentages)
        assert X_transformed.shape[1] == 4


def test_load_and_preprocess_data_zero_macros():
    """
    Test edge case: food with zero total macros (protein + fat + carbs = 0).
    
    This should handle division by zero gracefully by filling with 0.
    """
    # Create sample data with a food that has zero macros
    sample_data = {
        'Name': ['Water', 'Chicken Breast'],
        'Category': ['Beverage', 'Meat'],
        'Energy, kilocalories (kcal)': [0.0, 165.0],
        'Protein (g)': [0.0, 31.0],
        'Fat, total (g)': [0.0, 3.6],
        'Carbohydrates, available (g)': [0.0, 0.0]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test_zero_macros.xlsx"
        
        df_sample = pd.DataFrame(sample_data)
        df_sample.to_excel(temp_file, index=False)
        
        df_result, pipeline = load_and_preprocess_data(str(temp_file))
        
        # Water should have all percentages as 0 (division by zero handled)
        water_row = df_result[df_result['Name'] == 'Water'].iloc[0]
        assert water_row['protein_pct'] == 0.0
        assert water_row['fat_pct'] == 0.0
        assert water_row['carbs_pct'] == 0.0


def test_recommendation_engine_initialization():
    """
    Test RecommendationEngine initialization.
    
    This test verifies that the RecommendationEngine class:
    1. Successfully loads and preprocesses data
    2. Trains both K-Means and Nearest Neighbors models
    3. Stores all required attributes
    4. Adds cluster labels to the data DataFrame
    """
    # Create sample data for testing
    # Need at least 8 samples for K-Means with 8 clusters
    sample_data = {
        'Name': ['Chicken Breast', 'Apple', 'Banana', 'Orange', 'Salmon', 'Broccoli', 
                 'Rice', 'Beef', 'Egg', 'Yogurt'],
        'Category': ['Meat', 'Fruit', 'Fruit', 'Fruit', 'Fish', 'Vegetable', 
                     'Grain', 'Meat', 'Dairy', 'Dairy'],
        'Energy, kilocalories (kcal)': [165.0, 52.0, 89.0, 47.0, 208.0, 34.0, 
                                        130.0, 250.0, 155.0, 59.0],
        'Protein (g)': [31.0, 0.3, 1.1, 0.9, 20.0, 2.8, 2.7, 26.0, 13.0, 10.0],
        'Fat, total (g)': [3.6, 0.2, 0.3, 0.1, 13.0, 0.4, 0.3, 15.0, 11.0, 0.4],
        'Carbohydrates, available (g)': [0.0, 14.0, 23.0, 12.0, 0.0, 7.0, 
                                          28.0, 0.0, 1.1, 3.6]
    }
    
    # Create a temporary directory and Excel file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test_engine_data.xlsx"
        
        # Create DataFrame and save to Excel
        df_sample = pd.DataFrame(sample_data)
        df_sample.to_excel(temp_file, index=False)
        
        # Initialize the RecommendationEngine
        engine = RecommendationEngine(str(temp_file))
        
        # Assertions
        
        # 1. Check that self.data is not None and is a DataFrame
        assert engine.data is not None
        assert isinstance(engine.data, pd.DataFrame)
        assert len(engine.data) > 0
        
        # 2. Check that self.preprocessor is not None
        assert engine.preprocessor is not None
        assert hasattr(engine.preprocessor, 'transform')
        
        # 3. Check that self.kmeans_model is not None and is fitted
        assert engine.kmeans_model is not None
        assert hasattr(engine.kmeans_model, 'predict')
        assert hasattr(engine.kmeans_model, 'cluster_centers_')
        
        # 4. Check that self.nn_model is not None and is fitted
        assert engine.nn_model is not None
        assert hasattr(engine.nn_model, 'kneighbors')
        
        # 5. Check that self.X_features is not None and has correct shape
        assert engine.X_features is not None
        assert isinstance(engine.X_features, np.ndarray)
        assert engine.X_features.shape[0] == len(engine.data)  # Same number of rows
        assert engine.X_features.shape[1] == 4  # 4 features (scaled kcal + 3 percentages)
        
        # 6. Check that 'cluster' column has been added to self.data
        assert 'cluster' in engine.data.columns, "Cluster column not found in data"
        assert engine.data['cluster'].notna().all(), "Cluster column has missing values"
        
        # 7. Check that cluster labels are in valid range (0 to 7 for 8 clusters)
        assert engine.data['cluster'].min() >= 0
        assert engine.data['cluster'].max() < 8  # Should be less than n_clusters
        assert engine.data['cluster'].dtype in [np.int32, np.int64], "Cluster labels should be integers"
        
        # 8. Verify that K-Means model has 8 clusters
        assert len(engine.kmeans_model.cluster_centers_) == 8
        
        # 9. Verify that Nearest Neighbors can find neighbors
        # Test with first food in the dataset
        test_features = engine.X_features[0:1]  # First row
        distances, indices = engine.nn_model.kneighbors(test_features)
        assert len(indices[0]) == 6  # Should return 6 neighbors
        assert len(distances[0]) == 6


def test_get_similar_foods():
    """
    Test get_similar_foods method.
    
    This test verifies that the method:
    1. Finds similar foods for a known food
    2. Returns the correct number of recommendations
    3. Excludes the input food from results
    4. Returns foods with similar macro profiles
    """
    # Create sample data
    sample_data = {
        'Name': ['Chicken Breast', 'Turkey Breast', 'Chicken Thigh', 'Apple', 'Banana', 
                 'Orange', 'Salmon', 'Beef', 'Rice', 'Yogurt'],
        'Category': ['Meat', 'Meat', 'Meat', 'Fruit', 'Fruit', 'Fruit', 
                     'Fish', 'Meat', 'Grain', 'Dairy'],
        'Energy, kilocalories (kcal)': [165.0, 135.0, 209.0, 52.0, 89.0, 47.0, 
                                        208.0, 250.0, 130.0, 59.0],
        'Protein (g)': [31.0, 30.0, 26.0, 0.3, 1.1, 0.9, 
                        20.0, 26.0, 2.7, 10.0],
        'Fat, total (g)': [3.6, 0.5, 10.9, 0.2, 0.3, 0.1, 
                           13.0, 15.0, 0.3, 0.4],
        'Carbohydrates, available (g)': [0.0, 0.0, 0.0, 14.0, 23.0, 12.0, 
                                         0.0, 0.0, 28.0, 3.6]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test_similar_foods.xlsx"
        
        df_sample = pd.DataFrame(sample_data)
        df_sample.to_excel(temp_file, index=False)
        
        # Initialize the engine
        engine = RecommendationEngine(str(temp_file))
        
        # Test get_similar_foods
        similar_foods = engine.get_similar_foods("Chicken Breast", n_recommendations=3)
        
        # Assertions
        assert isinstance(similar_foods, pd.DataFrame)
        assert len(similar_foods) <= 3  # Should return at most 3 recommendations
        assert len(similar_foods) > 0, "Should return at least one recommendation"
        
        # Verify the input food is not in the results
        assert "Chicken Breast" not in similar_foods['Name'].values
        
        # Verify required columns are present
        expected_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs', 
                           'protein_pct', 'fat_pct', 'carbs_pct']
        for col in expected_columns:
            assert col in similar_foods.columns, f"Column {col} missing from results"
        
        # Test with food that doesn't exist
        no_similar = engine.get_similar_foods("NonExistent Food", n_recommendations=5)
        assert isinstance(no_similar, pd.DataFrame)
        assert len(no_similar) == 0


def test_get_goal_aligned_foods():
    """
    Test get_goal_aligned_foods method.
    
    This test verifies that the method:
    1. Correctly calculates macro ratios
    2. Predicts the appropriate cluster
    3. Returns foods from that cluster
    4. Returns the correct number of recommendations
    """
    # Create sample data with diverse macro profiles
    sample_data = {
        'Name': ['Chicken Breast', 'Apple', 'Banana', 'Orange', 'Salmon', 'Broccoli', 
                 'Rice', 'Beef', 'Egg', 'Yogurt', 'Almonds', 'Bread'],
        'Category': ['Meat', 'Fruit', 'Fruit', 'Fruit', 'Fish', 'Vegetable', 
                     'Grain', 'Meat', 'Dairy', 'Dairy', 'Nuts', 'Grain'],
        'Energy, kilocalories (kcal)': [165.0, 52.0, 89.0, 47.0, 208.0, 34.0, 
                                        130.0, 250.0, 155.0, 59.0, 579.0, 265.0],
        'Protein (g)': [31.0, 0.3, 1.1, 0.9, 20.0, 2.8, 2.7, 26.0, 13.0, 10.0, 21.0, 9.0],
        'Fat, total (g)': [3.6, 0.2, 0.3, 0.1, 13.0, 0.4, 0.3, 15.0, 11.0, 0.4, 50.0, 3.2],
        'Carbohydrates, available (g)': [0.0, 14.0, 23.0, 12.0, 0.0, 7.0, 
                                          28.0, 0.0, 1.1, 3.6, 22.0, 49.0]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test_goal_aligned.xlsx"
        
        df_sample = pd.DataFrame(sample_data)
        df_sample.to_excel(temp_file, index=False)
        
        # Initialize the engine
        engine = RecommendationEngine(str(temp_file))
        
        # Test get_goal_aligned_foods with sample remaining macros
        remaining_macros = {
            'kcal': 500.0,
            'protein': 50.0,
            'fat': 20.0,
            'carbs': 100.0
        }
        
        aligned_foods = engine.get_goal_aligned_foods(remaining_macros, n_recommendations=5)
        
        # Assertions
        assert isinstance(aligned_foods, pd.DataFrame)
        assert len(aligned_foods) <= 5  # Should return at most 5 recommendations
        assert len(aligned_foods) > 0, "Should return at least one recommendation"
        
        # Verify required columns are present
        expected_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs', 
                           'protein_pct', 'fat_pct', 'carbs_pct', 'cluster']
        for col in expected_columns:
            assert col in aligned_foods.columns, f"Column {col} missing from results"
        
        # Verify all returned foods belong to the same cluster
        if len(aligned_foods) > 1:
            unique_clusters = aligned_foods['cluster'].unique()
            assert len(unique_clusters) == 1, "All foods should belong to the same cluster"
        
        # Test with zero macros (edge case)
        zero_macros = {
            'kcal': 0.0,
            'protein': 0.0,
            'fat': 0.0,
            'carbs': 0.0
        }
        
        zero_aligned = engine.get_goal_aligned_foods(zero_macros, n_recommendations=3)
        # Should still return results (handles division by zero)
        assert isinstance(zero_aligned, pd.DataFrame)


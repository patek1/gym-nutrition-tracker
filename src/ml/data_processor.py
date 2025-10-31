"""
Data Processor Module

This module handles loading, cleaning, and preprocessing of the Swiss Food
Composition Database for machine learning model training.
"""

import os
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from typing import Tuple


def load_and_preprocess_data(filepath: str) -> Tuple[pd.DataFrame, Pipeline]:
    """
    Load and preprocess the Swiss Food Composition Database for ML model training.
    
    This function performs the following steps:
    1. Loads the Excel file into a pandas DataFrame
    2. Selects required columns (Name, Category, and four macro nutrients)
    3. Renames columns for easier access
    4. Drops rows with missing macro values
    5. Calculates percentage distributions of protein/fat/carbs
    6. Creates and fits a preprocessing pipeline with StandardScaler for kcal
    
    Args:
        filepath (str): Path to the Excel file containing the food database
        
    Returns:
        Tuple[pd.DataFrame, Pipeline]:
            - DataFrame: Cleaned DataFrame with original columns plus percentage columns
            - Pipeline: Fitted sklearn Pipeline for preprocessing features
            
    Example:
        >>> df, pipeline = load_and_preprocess_data("data/swiss_food_comp_db.xlsx")
        >>> print(df.columns)
        Index(['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs', 
               'protein_pct', 'fat_pct', 'carbs_pct'], dtype='object')
    """
    # Step 1: Load the Excel file into a pandas DataFrame
    # The Excel file has:
    # - Row 0: Title row (skip)
    # - Row 1: Blank row (skip)
    # - Row 2: Header row with column names (use as header)
    # - Row 3+: Data rows
    # Resolve file path relative to project root if needed
    if not os.path.isabs(filepath):
        # Try to resolve relative to current working directory
        current_dir = os.getcwd()
        abs_path = os.path.join(current_dir, filepath)
        if os.path.exists(abs_path):
            filepath = abs_path
        elif not os.path.exists(filepath):
            # Try relative to this file's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            alt_path = os.path.join(project_root, filepath)
            if os.path.exists(alt_path):
                filepath = alt_path
    
    print(f"Loading data from {filepath}...")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    # Step 2: Define required columns
    required_columns = [
        'Name',
        'Category',
        'Energy, kilocalories (kcal)',
        'Protein (g)',
        'Fat, total (g)',
        'Carbohydrates, available (g)'
    ]
    
    # Try to read the Excel file with different header rows
    # The file structure may vary, so we try header=2 first (expected), then fallback to others
    df = None
    header_row = None
    
    for header_idx in [2, 1, 0, 3]:
        try:
            test_df = pd.read_excel(filepath, header=header_idx)
            # Check if all required columns are present
            missing = [col for col in required_columns if col not in test_df.columns]
            if not missing:
                df = test_df
                header_row = header_idx
                print(f"Successfully loaded data using header row {header_idx}")
                break
        except Exception as e:
            print(f"Failed to read with header={header_idx}: {e}")
            continue
    
    # If we still don't have a valid dataframe, raise an error with helpful info
    if df is None:
        # Try one more time with header=2 to get column info for error message
        try:
            df_debug = pd.read_excel(filepath, header=2)
            available_cols = list(df_debug.columns)
        except:
            try:
                df_debug = pd.read_excel(filepath, header=0)
                available_cols = list(df_debug.columns)
            except:
                available_cols = ["Could not read Excel file"]
        
        # Provide helpful debug information
        print(f"DEBUG: Available columns in DataFrame ({len(available_cols)} total):")
        print(f"  First 20: {available_cols[:20]}")
        # Try to find similar column names
        similar_cols = {}
        for req_col in required_columns:
            # Case-insensitive search
            matches = [c for c in available_cols if req_col.lower() in c.lower() or c.lower() in req_col.lower()]
            if matches:
                similar_cols[req_col] = matches[:5]  # Show first 5 matches
        
        error_msg = f"Missing required columns: {required_columns}"
        error_msg += f"\nFile path used: {filepath}"
        error_msg += f"\nFile exists: {os.path.exists(filepath)}"
        if similar_cols:
            error_msg += f"\nSimilar column names found: {similar_cols}"
        error_msg += f"\nTried header rows: 2, 1, 0, 3"
        raise ValueError(error_msg)
    
    df = df[required_columns].copy()
    
    # Step 3: Rename columns for easier access
    column_mapping = {
        'Energy, kilocalories (kcal)': 'kcal',
        'Protein (g)': 'protein',
        'Fat, total (g)': 'fat',
        'Carbohydrates, available (g)': 'carbs'
    }
    df = df.rename(columns=column_mapping)
    
    # Step 4: Drop rows where any of the four macro columns have missing values
    macro_columns = ['kcal', 'protein', 'fat', 'carbs']
    initial_rows = len(df)
    df = df.dropna(subset=macro_columns)
    dropped_rows = initial_rows - len(df)
    if dropped_rows > 0:
        print(f"Dropped {dropped_rows} rows with missing macro values")
    
    # Convert macro columns to float to ensure numeric type
    for col in macro_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop any rows that couldn't be converted to numeric
    df = df.dropna(subset=macro_columns)
    
    # Step 5: Feature Engineering - Calculate percentage distributions
    # Calculate total grams of protein + fat + carbs
    df['total_macros_g'] = df['protein'] + df['fat'] + df['carbs']
    
    # Calculate percentages (handle division by zero)
    df['protein_pct'] = (df['protein'] / df['total_macros_g']).fillna(0)
    df['fat_pct'] = (df['fat'] / df['total_macros_g']).fillna(0)
    df['carbs_pct'] = (df['carbs'] / df['total_macros_g']).fillna(0)
    
    # Drop the temporary column
    df = df.drop(columns=['total_macros_g'])
    
    # Step 6: Create preprocessing pipeline
    # Define the transformer for scaling kcal
    preprocessor = ColumnTransformer(
        transformers=[
            ('kcal_scaler', StandardScaler(), ['kcal']),
            # Pass through the percentage columns without transformation
            ('passthrough', 'passthrough', ['protein_pct', 'fat_pct', 'carbs_pct'])
        ],
        remainder='drop'  # Drop any other columns
    )
    
    # Create the pipeline
    pipeline = Pipeline([
        ('preprocessor', preprocessor)
    ])
    
    # Step 7: Fit the pipeline on the data and transform it
    # Prepare the feature matrix for fitting
    feature_columns = ['kcal', 'protein_pct', 'fat_pct', 'carbs_pct']
    X = df[feature_columns]
    
    # Fit and transform the pipeline
    pipeline.fit(X)
    print(f"Pipeline fitted successfully on {len(df)} samples")
    
    # Return the cleaned DataFrame and the fitted pipeline
    return df, pipeline


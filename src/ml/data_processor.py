import logging
import pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from typing import Tuple

# Configure logger for this module
logger = logging.getLogger(__name__)


def load_and_preprocess_data(filepath: str) -> Tuple[pd.DataFrame, Pipeline]:
    # Step 1: Load the Excel file into a pandas DataFrame
    # The Excel file has:
    # - Row 0: Title row (skip)
    # - Row 1: Blank row (skip)
    # - Row 2: Header row with column names (use as header)
    # - Row 3+: Data rows
    
    # Convert filepath to Path object for easier handling
    filepath = Path(filepath)
    
    logger.info(f"Loading data from {filepath}...")
    
    if not filepath.exists():
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
    
    # Load the Excel file with header row 2 (standardized structure)
    df = pd.read_excel(filepath, header=2)
    
    # Check if all required columns are present
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        error_msg = f"Missing required columns: {missing}"
        error_msg += f"\nFile path used: {filepath}"
        error_msg += f"\nFile exists: {filepath.exists()}"
        error_msg += f"\nAvailable columns: {list(df.columns)[:20]}"
        logger.error(error_msg)
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
        logger.warning(f"Dropped {dropped_rows} rows with missing macro values")
    
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
    logger.info(f"Pipeline fitted successfully on {len(df)} samples")
    
    # Return the cleaned DataFrame and the fitted pipeline
    return df, pipeline


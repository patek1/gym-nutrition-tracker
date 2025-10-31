import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from src.ml.data_processor import load_and_preprocess_data


class RecommendationEngine:
    
    def __init__(self, data_filepath: str):
        # Step 1: Load and preprocess the data
        print(f"Initializing RecommendationEngine with data from {data_filepath}...")
        self.data, self.preprocessor = load_and_preprocess_data(data_filepath)
        
        # Step 2: Prepare feature matrix for transformation
        # Select the feature columns that will be used for ML models
        feature_columns = ['kcal', 'protein_pct', 'fat_pct', 'carbs_pct']
        X_raw = self.data[feature_columns]
        
        # Transform features using the fitted preprocessor pipeline
        # This scales kcal and passes through the percentage columns
        self.X_features = self.preprocessor.transform(X_raw)
        
        print(f"Feature matrix shape: {self.X_features.shape}")
        
        # Step 3: Train K-Means clustering model
        print("Training K-Means clustering model (8 clusters)...")
        self.kmeans_model = KMeans(
            n_clusters=8,
            random_state=42,
            n_init='auto'
        )
        
        # Fit the K-Means model on the transformed features
        cluster_labels = self.kmeans_model.fit_predict(self.X_features)
        
        # Store cluster labels as a new column in the data DataFrame
        self.data = self.data.copy()
        self.data['cluster'] = cluster_labels
        
        print(f"K-Means training complete. Cluster distribution:")
        print(self.data['cluster'].value_counts().sort_index())
        
        # Step 4: Train Nearest Neighbors model
        print("Training Nearest Neighbors model (6 neighbors)...")
        self.nn_model = NearestNeighbors(
            n_neighbors=6,  # 6 neighbors (1 will be the food itself + 5 similar)
            metric='euclidean'
        )
        
        # Fit the Nearest Neighbors model on the transformed features
        self.nn_model.fit(self.X_features)
        
        print("Nearest Neighbors training complete.")
        print(f"RecommendationEngine initialized successfully with {len(self.data)} foods.")
    
    def get_similar_foods(self, food_name: str, n_recommendations: int = 5) -> pd.DataFrame:
        # Step 1: Find the index of the food_name in self.data
        food_mask = self.data['Name'] == food_name
        food_indices = self.data.index[food_mask].tolist()
        
        if len(food_indices) == 0:
            print(f"Food '{food_name}' not found in database.")
            return pd.DataFrame()
        
        # Use the first match if multiple exist
        food_idx = food_indices[0]
        
        # Step 2: Get the feature vector for this food from self.X_features
        food_features = self.X_features[food_idx:food_idx+1]  # Keep as 2D array
        
        # Step 3: Use kneighbors to find n_recommendations + 1 nearest neighbors
        # (+1 because the food itself will be included)
        n_neighbors = n_recommendations + 1
        distances, neighbor_indices = self.nn_model.kneighbors(
            food_features, 
            n_neighbors=n_neighbors
        )
        
        # Extract the indices (first dimension is single query, so get [0])
        neighbor_indices = neighbor_indices[0]
        
        # Step 4: Filter out the input food itself (should be the first neighbor)
        # Find indices that are not the input food index
        neighbor_indices = [idx for idx in neighbor_indices if idx != food_idx]
        
        # Limit to n_recommendations (in case we have more than needed)
        neighbor_indices = neighbor_indices[:n_recommendations]
        
        if len(neighbor_indices) == 0:
            print(f"No similar foods found for '{food_name}'.")
            return pd.DataFrame()
        
        # Step 5: Return DataFrame with recommended foods
        recommended_foods = self.data.iloc[neighbor_indices].copy()
        
        # Select relevant columns for the output
        output_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs', 
                         'protein_pct', 'fat_pct', 'carbs_pct']
        recommended_foods = recommended_foods[output_columns]
        
        return recommended_foods
    
    def get_goal_aligned_foods(self, remaining_macros: dict, n_recommendations: int = 5) -> pd.DataFrame:
        # Step 1: Calculate target macro ratios (P%, F%, C%)
        # Handle division by zero case
        total_macros = remaining_macros['protein'] + remaining_macros['fat'] + remaining_macros['carbs']
        
        if total_macros == 0:
            # If all macros are zero, use equal distribution
            target_protein_pct = 0.0
            target_fat_pct = 0.0
            target_carbs_pct = 0.0
        else:
            target_protein_pct = remaining_macros['protein'] / total_macros
            target_fat_pct = remaining_macros['fat'] / total_macros
            target_carbs_pct = remaining_macros['carbs'] / total_macros
        
        # Step 2: Prepare the kcal value for scaling
        target_kcal = remaining_macros['kcal']
        
        # Create a DataFrame with the target macro values for preprocessing
        # We need to match the format expected by the preprocessor
        target_df = pd.DataFrame({
            'kcal': [target_kcal],
            'protein_pct': [target_protein_pct],
            'fat_pct': [target_fat_pct],
            'carbs_pct': [target_carbs_pct]
        })
        
        # Step 3: Scale the kcal using the fitted preprocessor
        # The preprocessor expects columns in order: ['kcal', 'protein_pct', 'fat_pct', 'carbs_pct']
        target_features = self.preprocessor.transform(target_df)
        
        # Step 4: Use K-Means to predict the best-matching cluster
        predicted_cluster = self.kmeans_model.predict(target_features)[0]
        
        # Step 5: Filter self.data for all foods belonging to that cluster
        cluster_foods = self.data[self.data['cluster'] == predicted_cluster].copy()
        
        if len(cluster_foods) == 0:
            print(f"No foods found in cluster {predicted_cluster}.")
            return pd.DataFrame()
        
        # Step 6: Return a sample of n_recommendations from that cluster
        # If there are fewer foods than requested, return all available
        n_sample = min(n_recommendations, len(cluster_foods))
        
        recommended_foods = cluster_foods.sample(
            n=n_sample, 
            random_state=42
        ).reset_index(drop=True)
        
        # Select relevant columns for the output
        output_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs', 
                         'protein_pct', 'fat_pct', 'carbs_pct', 'cluster']
        recommended_foods = recommended_foods[output_columns]
        
        return recommended_foods


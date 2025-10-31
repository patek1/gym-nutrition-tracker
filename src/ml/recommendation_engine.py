import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from src.ml.data_processor import load_and_preprocess_data


class RecommendationEngine:
    
    def __init__(self, data_filepath: str):
        # Step 1: Load and preprocess the data. The processor will create a pipeline
        # that is fitted on ['protein_pct', 'fat_pct', 'carbs_pct'].
        print(f"Initializing RecommendationEngine with data from {data_filepath}...")
        self.data, self.preprocessor = load_and_preprocess_data(data_filepath)
        
        # Reset index to ensure positional alignment with numpy arrays
        # This ensures that self.X_features[i] corresponds to self.data.iloc[i]
        self.data = self.data.reset_index(drop=True)
        
        # Step 2: Prepare feature matrix for transformation.
        # This MUST align with the features the preprocessor was trained on.
        feature_columns = ['protein_pct', 'fat_pct', 'carbs_pct']
        X_raw = self.data[feature_columns]
        
        # Transform the features using the fitted preprocessor pipeline.
        self.X_features = self.preprocessor.transform(X_raw)
        
        print(f"Feature matrix shape: {self.X_features.shape}")
        
        # Step 3: Train K-Means clustering model
        print("Training K-Means clustering model (8 clusters)...")
        self.kmeans_model = KMeans(
            n_clusters=8,
            random_state=42,
            n_init='auto'
        )
        self.kmeans_model.fit(self.X_features)
        self.data['cluster'] = self.kmeans_model.labels_
        
        print(f"K-Means training complete. Cluster distribution:")
        print(self.data['cluster'].value_counts().sort_index())
        
        # Step 4: Train Nearest Neighbors model
        print("Training Nearest Neighbors model (6 neighbors)...")
        self.nn_model = NearestNeighbors(
            n_neighbors=6,
            metric='euclidean'
        )
        self.nn_model.fit(self.X_features)
        
        print("Nearest Neighbors training complete.")
        print(f"RecommendationEngine initialized successfully with {len(self.data)} foods.")
    
    def get_similar_foods(self, food_name: str, n_recommendations: int = 5) -> pd.DataFrame:
        """
        Find foods similar to the given food based on macro composition.
        
        Args:
            food_name: Name of the food to find similar foods for
            n_recommendations: Number of recommendations to return
        """
        # Step 1: Find the positional index of the food_name in self.data
        # Try exact match first (case-insensitive)
        food_mask = self.data['Name'].str.lower() == food_name.lower()
        
        # If no exact match, try partial match (contains)
        if not food_mask.any():
            food_mask = self.data['Name'].str.lower().str.contains(food_name.lower(), na=False, regex=False)
            print(f"DEBUG: No exact match for '{food_name}', trying partial match...")
        
        if not food_mask.any():
            print(f"DEBUG: Food '{food_name}' not found in database.")
            print(f"DEBUG: Searching for similar names...")
            # Try fuzzy matching - show some foods with similar names
            similar_names = self.data[self.data['Name'].str.lower().str.contains(food_name.lower().split()[0] if food_name else '', na=False, regex=False)]['Name'].head(5)
            if len(similar_names) > 0:
                print(f"DEBUG: Similar names found: {list(similar_names)}")
            return pd.DataFrame()

        # Get the first matching positional index (since index was reset in __init__)
        food_pos_idx = food_mask[food_mask].index[0]
        food_category = self.data.iloc[food_pos_idx]['Category']
        food_macros = self.data.iloc[food_pos_idx][['protein', 'fat', 'carbs']]
        matched_name = self.data.iloc[food_pos_idx]['Name']
        
        print(f"DEBUG: Finding similar foods for '{food_name}' -> matched '{matched_name}' (Category: {food_category}, Position: {food_pos_idx})")
        print(f"DEBUG: Food macros - P: {food_macros['protein']}g, F: {food_macros['fat']}g, C: {food_macros['carbs']}g")
        
        # Step 2: Get the feature vector for this food (which is based on ratios only)
        food_features = self.X_features[food_pos_idx:food_pos_idx+1]
        
        # Step 3: Use kneighbors to find neighbors - search more neighbors to get better same-category matches
        # Search for more neighbors than needed to ensure we have enough same-category options
        search_neighbors = min(n_recommendations * 3 + 1, len(self.data))
        distances, neighbor_indices = self.nn_model.kneighbors(food_features, n_neighbors=search_neighbors)
        
        neighbor_indices = neighbor_indices[0]
        neighbor_distances = distances[0]
        
        # Step 4: Create list of neighbors with additional info
        neighbors_with_info = []
        for pos_idx, dist in zip(neighbor_indices, neighbor_distances):
            if pos_idx != food_pos_idx:
                same_category = self.data.iloc[pos_idx]['Category'] == food_category
                neighbor_macros = self.data.iloc[pos_idx][['protein', 'fat', 'carbs']]
                # Calculate macro similarity (absolute difference in macro percentages)
                neighbor_features = self.X_features[pos_idx:pos_idx+1]
                macro_diff = np.linalg.norm(food_features - neighbor_features)
                
                neighbors_with_info.append((pos_idx, dist, same_category, macro_diff))
        
        if not neighbors_with_info:
            print(f"DEBUG: No other similar foods found for '{food_name}'.")
            return pd.DataFrame()
        
        # Step 5: Rank neighbors with strong priority for same category
        # Sort by: (not same_category, macro_diff) - same category foods first, then by macro similarity
        # This ensures oils find other oils, lean meats find other lean meats, etc.
        ranked = sorted(neighbors_with_info, key=lambda x: (not x[2], x[3]))
        
        # Take top recommendations
        top_neighbors = ranked[:n_recommendations]
        final_pos_indices = [pos_idx for pos_idx, _, _, _ in top_neighbors]
        
        # Step 6: Return DataFrame with recommended foods
        recommended_foods = self.data.iloc[final_pos_indices].copy()
        
        output_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs']
        return recommended_foods[output_columns]

    def get_goal_aligned_foods(self, remaining_macros: dict, user_goals: dict = None, n_recommendations: int = 5) -> pd.DataFrame:
        """
        Get foods that help meet remaining macro goals.
        
        Args:
            remaining_macros: Dict with 'protein', 'carbs', 'fat', 'kcal' remaining
            user_goals: Optional dict with total goals to calculate completion percentages
            n_recommendations: Number of recommendations to return
        """
        print(f"DEBUG: Goal-aligned recommendations for remaining macros: {remaining_macros}")
        
        # Step 1: Calculate target macro ratios (P%, F%, C%)
        total_pfc_grams = remaining_macros['protein'] + remaining_macros['fat'] + remaining_macros['carbs']
        
        if total_pfc_grams <= 0:
            print("DEBUG: All macro goals are met. No recommendations needed.")
            return pd.DataFrame()
            
        target_protein_pct = remaining_macros['protein'] / total_pfc_grams
        target_fat_pct = remaining_macros['fat'] / total_pfc_grams
        target_carbs_pct = remaining_macros['carbs'] / total_pfc_grams

        print(f"DEBUG: Target macro ratios - P: {target_protein_pct:.2%}, F: {target_fat_pct:.2%}, C: {target_carbs_pct:.2%}")
        
        # Step 2: Calculate goal completion percentages if goals provided
        # This helps filter out foods high in macros that are already mostly met
        goal_completion = {}
        if user_goals:
            goal_completion = {
                'protein': 1 - (remaining_macros['protein'] / user_goals['protein']) if user_goals['protein'] > 0 else 0,
                'fat': 1 - (remaining_macros['fat'] / user_goals['fat']) if user_goals['fat'] > 0 else 0,
                'carbs': 1 - (remaining_macros['carbs'] / user_goals['carbs']) if user_goals['carbs'] > 0 else 0,
            }
            print(f"DEBUG: Goal completion - P: {goal_completion['protein']:.1%}, F: {goal_completion['fat']:.1%}, C: {goal_completion['carbs']:.1%}")
        
        # Step 3: Create a target vector matching the preprocessor's expected input.
        target_df = pd.DataFrame([{
            'protein_pct': target_protein_pct,
            'fat_pct': target_fat_pct,
            'carbs_pct': target_carbs_pct
        }])
        
        # Transform the target vector into the scaled feature space
        target_features = self.preprocessor.transform(target_df)
        
        # Step 4: Predict the best-matching cluster
        predicted_cluster = self.kmeans_model.predict(target_features)[0]
        print(f"DEBUG: Predicted cluster: {predicted_cluster}")
        
        # Step 5: Get all foods from that cluster
        cluster_mask = self.data['cluster'] == predicted_cluster
        cluster_foods = self.data[cluster_mask].copy()
        
        if cluster_foods.empty:
            print(f"DEBUG: No foods found in cluster {predicted_cluster}.")
            return pd.DataFrame()
        
        print(f"DEBUG: Found {len(cluster_foods)} foods in cluster {predicted_cluster}")
        
        # Step 6: Filter out foods with very low macro density (mostly water/fiber)
        # Calculate total macros per 100g for each food
        cluster_foods['total_macros'] = cluster_foods['protein'] + cluster_foods['fat'] + cluster_foods['carbs']
        MIN_MACRO_DENSITY = 10  # Filter out foods with less than 10g total macros per 100g
        cluster_foods = cluster_foods[cluster_foods['total_macros'] >= MIN_MACRO_DENSITY].copy()
        print(f"DEBUG: After filtering low-density foods (<{MIN_MACRO_DENSITY}g total macros): {len(cluster_foods)} foods remaining")
        
        if cluster_foods.empty:
            print("DEBUG: No foods with sufficient macro density found.")
            return pd.DataFrame()
        
        # Step 7: Smart Filtering - Remove foods high in macros that are already mostly met
        def is_suitable(food):
            # Filter out foods high in macros that are already mostly met (e.g., >50% goal completion)
            if user_goals:
                if goal_completion['fat'] > 0.5 and food['fat_pct'] > 0.60:  # Fat goal >50% met, food is >60% fat
                    return False
                if goal_completion['protein'] > 0.5 and food['protein_pct'] > 0.60:  # Protein goal >50% met
                    return False
                if goal_completion['carbs'] > 0.5 and food['carbs_pct'] > 0.60:  # Carbs goal >50% met
                    return False
            
            # Filter out foods high in macros that are NOT needed (remaining < 10g)
            if remaining_macros['fat'] < 10 and food['fat_pct'] > 0.50:
                return False
            if remaining_macros['protein'] < 10 and food['protein_pct'] > 0.50:
                return False
            if remaining_macros['carbs'] < 10 and food['carbs_pct'] > 0.50:
                return False
            
            return True

        suitable_indices = cluster_foods[cluster_foods.apply(is_suitable, axis=1)].index
        print(f"DEBUG: After filtering unsuitable foods: {len(suitable_indices)} foods remaining")
        
        # Step 8: Score foods based on:
        # - Distance to target macro ratios (lower is better)
        # - Absolute macro contribution (higher is better for needed macros)
        cluster_pos_indices = cluster_foods.index.values
        cluster_features = self.X_features[cluster_pos_indices]
        ratio_distances = np.linalg.norm(cluster_features - target_features, axis=1)
        
        # Calculate contribution score: how much this food helps meet absolute goals
        contribution_scores = []
        for idx in cluster_foods.index:
            food = cluster_foods.loc[idx]
            # Prioritize foods that provide substantial amounts of needed macros
            contribution = 0
            if remaining_macros['protein'] > 0:
                contribution += food['protein'] * (remaining_macros['protein'] / total_pfc_grams)
            if remaining_macros['fat'] > 0:
                contribution += food['fat'] * (remaining_macros['fat'] / total_pfc_grams)
            if remaining_macros['carbs'] > 0:
                contribution += food['carbs'] * (remaining_macros['carbs'] / total_pfc_grams)
            contribution_scores.append(contribution)
        
        # Normalize scores (ratio distance: lower is better, contribution: higher is better)
        # Combine: lower ratio distance + higher contribution = better score
        max_contribution = max(contribution_scores) if contribution_scores else 1
        max_distance = max(ratio_distances) if len(ratio_distances) > 0 else 1
        
        # Normalize and combine (weight contribution more heavily)
        normalized_distances = ratio_distances / max_distance if max_distance > 0 else ratio_distances
        normalized_contributions = [c / max_contribution if max_contribution > 0 else 0 for c in contribution_scores]
        
        # Combined score: lower is better (inverse of contribution)
        combined_scores = 0.4 * normalized_distances + 0.6 * (1 - np.array(normalized_contributions))
        cluster_foods['score'] = combined_scores
        
        # Step 9: Select final recommendations
        if len(suitable_indices) >= n_recommendations:
            # Use only suitable foods
            final_foods = cluster_foods.loc[suitable_indices].sort_values('score').head(n_recommendations)
        else:
            # If not enough suitable foods, use best overall (but still filtered for density)
            final_foods = cluster_foods.sort_values('score').head(n_recommendations)
            
        print(f"DEBUG: Top {len(final_foods)} recommendations after filtering:")
        
        # Drop helper columns
        output_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs']
        return final_foods[output_columns].reset_index(drop=True)
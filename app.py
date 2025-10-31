import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.api_client import search_food, get_food_details
from src.ml.recommendation_engine import RecommendationEngine

# Set page configuration
st.set_page_config(page_title="Gym Nutrition Tracker")

# Cached Model Loading
@st.cache_resource
def load_engine():
    try:
        engine = RecommendationEngine(data_filepath='data/Swiss_food_composition_database.xlsx')
        return engine
    except Exception as e:
        st.error(f"Error loading recommendation engine: {str(e)}")
        return None

# Load the recommendation engine (cached)
engine = load_engine()

# Main title
st.title("Gym Nutrition Tracker")

# Food Logging Section - Moved to top for better UX
st.header("Log a Meal")

# Search Form
# Create a text input for food search query
search_query = st.text_input(
    "Search for a food",
    placeholder="Type a food name (e.g., 'chicken', 'apple')",
    help="Search the Swiss Food Database for foods"
)

# Initialize session state for search results if not exists
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# When query is not empty, call search_food
if search_query:
    try:
        # Call search_food API
        search_results = search_food(search_query)
        
        if search_results:
            # Store results in session state
            st.session_state.search_results = search_results
            
            # Extract food names for selectbox
            food_names = [food['name'] for food in search_results]
            
            # Display selectbox with food names
            selected_food_name = st.selectbox(
                "Select a food",
                options=food_names,
                help="Choose a food from the search results"
            )
            
            # Find the dbid of the selected food
            selected_food = next(
                (food for food in search_results if food['name'] == selected_food_name),
                None
            )
            
            if selected_food:
                # Logging Form
                with st.form(key='log_food_form'):
                    st.write(f"**Selected:** {selected_food_name}")
                    
                    # Number input for portion size
                    portion_size = st.number_input(
                        'Portion Size (g)',
                        min_value=0.0,
                        value=100.0,
                        step=1.0,
                        help="Enter the portion size in grams (e.g., 100 for 100g)"
                    )
                    
                    # Submit button
                    submitted_log = st.form_submit_button("Log Food")
                    
                    # When form is submitted
                    if submitted_log:
                        # Get the dbid of the selected food
                        food_dbid = selected_food['dbid']
                        
                        # Call get_food_details to fetch nutritional information
                        try:
                            food_details = get_food_details(food_dbid)
                            
                            if food_details:
                                # Calculate consumed macros based on portion size
                                # API returns macros per 100g, so: (portion / 100) * macro_per_100g
                                portion_factor = portion_size / 100.0
                                
                                consumed_kcal = portion_factor * food_details['kcal']
                                consumed_protein = portion_factor * food_details['protein']
                                consumed_carbs = portion_factor * food_details['carbs']
                                consumed_fat = portion_factor * food_details['fat']
                                
                                # Create a dictionary for the logged meal
                                logged_meal = {
                                    'name': selected_food_name,
                                    'portion_g': portion_size,
                                    'kcal': consumed_kcal,
                                    'protein': consumed_protein,
                                    'carbs': consumed_carbs,
                                    'fat': consumed_fat
                                }
                                
                                # Append to logged_meals
                                st.session_state.logged_meals.append(logged_meal)
                                
                                # Show success message
                                st.success(f"Successfully logged {portion_size:.1f}g of {selected_food_name}!")
                                
                                # Rerun to refresh the dashboard
                                st.rerun()
                            else:
                                # If get_food_details returns None
                                st.error("Could not fetch nutritional data for this food.")
                        except Exception as e:
                            # Handle any errors during API call
                            st.error(f"Error fetching food details: {str(e)}")
        else:
            # No results found
            st.info("No food found. Try a different search term.")
            # Clear search results
            st.session_state.search_results = []
    except Exception as e:
        # Handle search errors
        st.error(f"Error searching for food: {str(e)}")
        st.session_state.search_results = []
else:
    # Clear search results when query is empty
    st.session_state.search_results = []
    st.info("Enter a food name above to search and log meals.")

st.divider()

# Initialize Session State
# Check if 'user_goals' is not in session state, initialize with default values
if 'user_goals' not in st.session_state:
    st.session_state.user_goals = {
        'kcal': 2000,
        'protein': 150,
        'carbs': 200,
        'fat': 60
    }

# Check if 'logged_meals' is not in session state, initialize as empty list
if 'logged_meals' not in st.session_state:
    st.session_state.logged_meals = []

# Goal Setting UI in Sidebar
with st.sidebar:
    st.header("Set Your Daily Goals")
    
    # Create a form for goal setting
    with st.form(key='goal_form'):
        # Number inputs for each macro goal
        # Get current values from session state
        kcal_goal = st.number_input(
            'Calories (kcal)',
            min_value=0,
            max_value=10000,
            value=st.session_state.user_goals['kcal'],
            step=50,
            help="Set your daily calorie target"
        )
        
        protein_goal = st.number_input(
            'Protein (g)',
            min_value=0,
            max_value=500,
            value=st.session_state.user_goals['protein'],
            step=5,
            help="Set your daily protein target in grams"
        )
        
        carbs_goal = st.number_input(
            'Carbs (g)',
            min_value=0,
            max_value=1000,
            value=st.session_state.user_goals['carbs'],
            step=10,
            help="Set your daily carbohydrate target in grams"
        )
        
        fat_goal = st.number_input(
            'Fat (g)',
            min_value=0,
            max_value=500,
            value=st.session_state.user_goals['fat'],
            step=5,
            help="Set your daily fat target in grams"
        )
        
        # Submit button
        submitted = st.form_submit_button('Set Goals')
        
        # If button is clicked, update session state
        if submitted:
            st.session_state.user_goals = {
                'kcal': int(kcal_goal),
                'protein': int(protein_goal),
                'carbs': int(carbs_goal),
                'fat': int(fat_goal)
            }
            st.success("Goals updated successfully!")

# Dashboard Visualization Section
st.header("Today's Progress")

# Calculate Totals
# Check if logged_meals is not empty
if st.session_state.logged_meals:
    # Create a pandas DataFrame from the list of logged meal dictionaries
    df_logged = pd.DataFrame(st.session_state.logged_meals)
    
    # Calculate the sum of consumed macros
    total_kcal = df_logged['kcal'].sum() if 'kcal' in df_logged.columns else 0
    total_protein = df_logged['protein'].sum() if 'protein' in df_logged.columns else 0
    total_carbs = df_logged['carbs'].sum() if 'carbs' in df_logged.columns else 0
    total_fat = df_logged['fat'].sum() if 'fat' in df_logged.columns else 0
else:
    # If no meals, totals should be 0
    total_kcal = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

# Display Progress Bars
# Helper function to display progress for each macro
def display_progress_bar(macro_name: str, consumed: float, target: float, unit: str = ""):
    st.write(f"**{macro_name}**")
    
    # Calculate progress percentage, cap at 1.0 to prevent overflow
    if target > 0:
        progress = min(consumed / target, 1.0)
    else:
        progress = 0.0
    
    # Display progress bar
    st.progress(progress)
    
    # Calculate remaining
    remaining = max(target - consumed, 0)
    
    # Display remaining text
    st.markdown(f"Remaining: {remaining:.1f} {unit}")
    
    # Display consumed/target info
    st.caption(f"Consumed: {consumed:.1f} / {target:.1f} {unit}")

# Display progress bars in a 2x2 grid layout for better UX
col1, col2 = st.columns(2)

with col1:
    display_progress_bar("Calories", total_kcal, st.session_state.user_goals['kcal'], "kcal")

with col2:
    display_progress_bar("Protein", total_protein, st.session_state.user_goals['protein'], "g")

col3, col4 = st.columns(2)

with col3:
    display_progress_bar("Carbs", total_carbs, st.session_state.user_goals['carbs'], "g")

with col4:
    display_progress_bar("Fat", total_fat, st.session_state.user_goals['fat'], "g")

# Display Pie Chart
st.header("Macro Distribution")

# Check if total grams of P+F+C are greater than zero
total_macros_g = total_protein + total_carbs + total_fat

if total_macros_g > 0:
    # Create a Plotly pie chart showing the distribution of consumed macros
    fig = go.Figure(data=[go.Pie(
        labels=['Protein', 'Carbs', 'Fat'],
        values=[total_protein, total_carbs, total_fat],
        hole=0.3,  # Creates a donut chart
        marker_colors=['#FF6B6B', '#4ECDC4', '#FFE66D']
    )])
    
    # Update layout
    fig.update_layout(
        title="Consumed Macro Distribution",
        annotations=[dict(text=f'{total_macros_g:.1f}g<br>Total', x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
else:
    # If no macros have been logged, display a message
    st.info("Log a meal to see your macro distribution.")

# AI Recommendations Section
st.header("AI Recommendations")

# Check if engine is loaded successfully
if engine is None:
    st.warning("Recommendation engine is not available. Please ensure the data file exists.")
else:
    # Add button to get recommendations
    if st.button("Get Recommendations"):
        # Goal-Aligned Recommendations
        st.subheader("Foods to Help Meet Your Goals")
        
        # Calculate remaining macros (target - total consumed)
        remaining_macros = {
            'kcal': max(st.session_state.user_goals['kcal'] - total_kcal, 0),
            'protein': max(st.session_state.user_goals['protein'] - total_protein, 0),
            'carbs': max(st.session_state.user_goals['carbs'] - total_carbs, 0),
            'fat': max(st.session_state.user_goals['fat'] - total_fat, 0)
        }
        
        # Check if there are remaining macros
        if sum(remaining_macros.values()) > 0:
            try:
                # Call get_goal_aligned_foods
                goal_aligned_foods = engine.get_goal_aligned_foods(remaining_macros, n_recommendations=5)
                
                if not goal_aligned_foods.empty:
                    # Display results in a dataframe
                    # Select relevant columns for display
                    display_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs']
                    st.dataframe(
                        goal_aligned_foods[display_columns],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No recommendations found. Try adjusting your goals.")
            except Exception as e:
                st.error(f"Error getting goal-aligned recommendations: {str(e)}")
        else:
            st.info("🎉 Congratulations! You've met all your macro goals for today!")
        
        # Similar Food Recommendations
        # Check if any meals have been logged
        if st.session_state.logged_meals:
            st.subheader("Substitutes for Your Last Meal")
            
            # Get the name of the last logged food
            last_logged_food_name = st.session_state.logged_meals[-1]['name']
            
            try:
                # Call get_similar_foods
                similar_foods = engine.get_similar_foods(last_logged_food_name, n_recommendations=5)
                
                if not similar_foods.empty:
                    # Display results in a dataframe
                    # Select relevant columns for display
                    display_columns = ['Name', 'Category', 'kcal', 'protein', 'fat', 'carbs']
                    st.dataframe(
                        similar_foods[display_columns],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(f"No similar foods found for '{last_logged_food_name}'.")
            except Exception as e:
                st.error(f"Error getting similar food recommendations: {str(e)}")
        else:
            # Don't show similar foods section if no meals logged
            pass

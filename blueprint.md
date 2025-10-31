Of course. This is an excellent project for a structured, iterative approach. I will now create the detailed blueprint, break it down into iterative chunks, and then generate the series of LLM prompts.

### **Part 1: The Detailed Blueprint & Iterative Plan**

First, I will lay out the development plan, breaking the project into logical, sequential phases. Each phase will then be broken down into smaller, actionable steps. This ensures a clean, testable, and incremental build process.

---

### **Project Blueprint: Gym Nutrition Tracker**

#### **Phase 1: Foundation & Core Services (Backend Logic)**

This phase focuses on creating the non-UI components. We'll build the data access layers and the machine learning engine. These components can be developed and tested in isolation before any user interface is built.

*   **Chunk 1.1: API Client Module**
    *   **Goal:** Create a reliable, testable interface to the FSVO Public API.
    *   **Step 1.1.1: Setup Project Structure.** Create the basic directory layout (`/src`, `/tests`, `requirements.txt`, `README.md`) and install initial dependencies (`requests`, `pytest`, `pandas`).
    *   **Step 1.1.2: Implement Food Search.** Create a function that takes a search query string, calls the `.../foods?search=` endpoint, and returns a list of food names and their `DBID`s.
    *   **Step 1.1.3: Implement Food Detail Fetch.** Create a function that takes a `DBID`, calls the `.../food/{DBID}` endpoint, and extracts the key macronutrient values (Kcal, Protein, Fat, Carbs) and the `matrixunitcode`.
    *   **Step 1.1.4: Unit Testing & Error Handling.** Write `pytest` unit tests for both functions using `requests_mock` to simulate successful API calls, failed calls (e.g., 404, 500), and responses with missing data. Wrap API calls in `try/except` blocks.

*   **Chunk 1.2: Machine Learning Engine**
    *   **Goal:** Build a class that encapsulates all ML-related logic: data loading, preprocessing, model training, and prediction.
    *   **Step 1.2.1: Data Loading & Cleaning.** Create a function to load the local `.xlsx` file into a Pandas DataFrame. Implement the specified cleaning steps: column selection, type conversion, and dropping rows with missing macro values.
    *   **Step 1.2.2: Feature Engineering & Preprocessing.** Create a preprocessing pipeline (using `scikit-learn`'s `Pipeline` is a best practice) that calculates macro ratios (P/F/C %) and scales the Kcal feature.
    *   **Step 1.2.3: Model Training.** Within a main `RecommendationEngine` class, create methods to train and store a `NearestNeighbors` model and a `KMeans` model ($K=8$) on the preprocessed data.
    *   **Step 1.2.4: Recommendation Logic (Similar Foods).** Implement a method in the class that takes a food's macro profile as input and uses the `NearestNeighbors` model to return the top 5 most similar foods from the dataset.
    *   **Step 1.2.5: Recommendation Logic (Goal-Aligned Foods).** Implement a method that takes the user's *remaining* macros, calculates the ideal ratio, finds the closest `KMeans` cluster centroid, and returns a sample of foods from that cluster.
    *   **Step 1.2.6: Unit Testing.** Write unit tests for the data loading, preprocessing, and the output format of the recommendation methods.

#### **Phase 2: Application Core & User Interface (Frontend & Integration)**

This phase focuses on building the Streamlit application, managing its state, and creating the user-facing components. We will integrate the services built in Phase 1.

*   **Chunk 2.1: Basic App Structure & State Management**
    *   **Goal:** Set up the Streamlit app file and initialize the session state management.
    *   **Step 2.1.1: Initialize Streamlit App.** Create the main `app.py` file with a title.
    *   **Step 2.1.2: Setup Session State.** Initialize `st.session_state` to hold the `user_goals` object and the `logged_meals` list. This ensures data persists across reruns within a single user session.

*   **Chunk 2.2: UI Component - Goal Setting**
    *   **Goal:** Allow users to input and save their daily macro targets.
    *   **Step 2.2.1: Create Goal Input Form.** Use `st.form` to create number inputs for target Kcal, Protein, Carbs, and Fat.
    *   **Step 2.2.2: Save Goals to Session State.** On form submission, update the `user_goals` dictionary in `st.session_state`.

*   **Chunk 2.3: UI Component - Dashboard Visualization**
    *   **Goal:** Display the user's progress against their goals.
    *   **Step 2.3.1: Calculate Current Totals.** Create a helper function that iterates through `st.session_state.logged_meals` to sum up the total consumed Kcal, Protein, Fat, and Carbs.
    *   **Step 2.3.2: Render Progress Bars.** Use the calculated totals and the user's goals to display four `st.progress` bars. Show "X remaining" text below each.
    *   **Step 2.3.3: Render Macro Distribution Chart.** Use the consumed totals to display a pie chart (e.g., with Plotly via `st.plotly_chart`) showing the percentage breakdown of consumed P/F/C.

*   **Chunk 2.4: UI Component - Food Logging & API Integration**
    *   **Goal:** Create the main interactive feature for searching and logging food. This is a critical integration step.
    *   **Step 2.4.1: Implement Search Interaction.** Add a `st.text_input` for the food search. As the user types, call the `search_food_by_name` function from our API client.
    *   **Step 2.4.2: Display Search Results.** Use a `st.selectbox` to display the food names returned by the search function.
    *   **Step 2.4.3: Implement Logging Logic.** Once a user selects a food and enters a portion size (`st.number_input`), add a "Log Food" button. When clicked, this button will:
        a. Call the `get_food_details_by_id` function from the API client using the selected food's `DBID`.
        b. Perform the macro calculation based on portion size.
        c. Create a new "logged meal" dictionary.
        d. Append this dictionary to `st.session_state.logged_meals`. The app will automatically rerun, updating the dashboard.

#### **Phase 3: Final Integration & Polish**

This phase connects the ML engine to the UI and adds the final touches required by the specification.

*   **Chunk 3.1: ML Recommendation Integration**
    *   **Goal:** Connect the `RecommendationEngine` to the live application state.
    *   **Step 3.1.1: Add "Get Recommendations" Button.** Place a button in the UI.
    *   **Step 3.1.2: Wire Recommendation Logic.** When the button is clicked:
        a. Instantiate the `RecommendationEngine`. (Use `@st.cache_resource` to prevent reloading and retraining the model on every rerun).
        b. Calculate the remaining macros needed to hit the user's goals.
        c. If a food has been logged, get the last logged food's macro profile.
        d. Call the `get_similar_foods` and `get_goal_aligned_foods` methods from the engine.
        e. Display the returned lists of recommended foods neatly to the user using `st.table` or `st.dataframe`.

*   **Chunk 3.2: Documentation & Final Review**
    *   **Goal:** Complete the project by fulfilling the documentation requirements.
    *   **Step 3.2.1: Add Inline Comments.** Review all functions and add clear, concise comments explaining their purpose, inputs, and outputs.
    *   **Step 3.2.2: Create README.md.** Write the `README.md` file with the specified sections: Problem Statement, Requirements Summary, and Installation/Setup instructions.
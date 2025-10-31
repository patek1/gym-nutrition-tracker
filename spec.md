This is the comprehensive, developer-ready specification for the **Gym Nutrition Tracker**.

It integrates all confirmed details regarding requirements, data sources, architecture, ML logic, and user workflow, following the mandatory project requirements (1-6).

---

# Gym Nutrition Tracker: Developer Specification

## 1. Project Overview and Scope (Requirement 1)

**Application Name:** Gym Nutrition Tracker (Streamlit MVP)
**Goal:** To provide Swiss gym-goers with an efficient, data-driven web application for tracking macronutrient intake, visualizing progress against personal goals, and receiving AI-based food recommendations using locally relevant data.

**Target User:** Individuals focused on fitness goals (muscle gain, fat loss) who track Calories, Protein, Carbs, and Fat daily.
**Technology:** Python (Streamlit, Pandas, Scikit-learn).

## 2. Technical Architecture and Stack

| Component | Technology/Method | Purpose |
| :--- | :--- | :--- |
| **Frontend/App Framework** | Streamlit (Python) | User interface and deployment. |
| **Backend/Data Processing** | Python, Pandas | Data manipulation, logging, calculation. |
| **Real-Time Data Source** | FSVO Public API (HTTP GET requests) | Food search and real-time macro lookup. |
| **ML Data Source** | Local `.xlsx` file (Swiss Food Database) | Static dataset for model training. |
| **Machine Learning** | Scikit-learn (K-Means, Nearest Neighbors) | Food recommendations. |
| **Persistence (MVP)** | Streamlit `st.session_state` | Temporary storage for goals and logged meals (per session). |

## 3. Data Sources and API Integration (Requirement 2)

### A. API Interaction Flow (Real-Time Lookup)

The application uses the FSVO API base URL: `https://api.webapp.prod.blv.foodcase-services.com/BLV_WebApp_WS`

| Step | Endpoint & Method | Purpose | Required Output Data |
| :--- | :--- | :--- | :--- |
| **1. Food Search** | `GET /webresources/BLV-api/foods?search={query}&lang=en` | User types food name; the app suggests matches via dropdown. | `Food Name`, `DBID` (unique food ID). |
| **2. Detail Fetch** | `GET /webresources/BLV-api/food/{DBID}?lang=en` | Once the user selects a food, fetch its full nutritional profile. | **Macro Base Values** (per 100g or matrix unit): Kcal, Protein (g), Fat (g), Carbs (g). Also, the `matrixunitcode`. |

### B. User Data Model (Persistence)

Data for the current session is stored via `st.session_state`.

**1. Daily Goals Object:**
*   `target_kcal` (Integer)
*   `target_protein` (Integer)
*   `target_carbs` (Integer)
*   `target_fat` (Integer)

**2. Logged Meals Array (Indexed by Date):**
*   `food_id` (Integer - DBID)
*   `food_name` (String)
*   `portion_size_g` (Float - User Input)
*   `kcal_consumed` (Float - Calculated)
*   `protein_consumed`, `carbs_consumed`, `fat_consumed` (Float - Calculated)

### C. Calculation Logic

Macro values are assumed to be returned by the API per 100g by default.

$$\text{Macro Consumed} = \frac{\text{Portion Size (g)}}{100 \text{ g}} \times \text{API Macro Value (per } 100\text{g)}$$

## 4. Machine Learning (ML) Specification (Requirement 5)

The ML component is trained on the local `.xlsx` dataset and serves two distinct recommendation functions.

### A. Data Pre-processing Pipeline

1.  **Column Selection:** Retain only `Name`, `Category`, `Energy, kilocalories (kcal)`, `Protein (g)`, `Fat, total (g)`, and `Carbohydrates, available (g)`.
2.  **Type Conversion:** Convert the four macro features to `float`.
3.  **Missing Value Handling:** **Drop** any row missing data in the four core macro columns.
4.  **Feature Engineering (Ratios):** Calculate the percentage distribution of P/F/C (P%, F%, C%) relative to the total P+F+C grams per food item.
5.  **Feature Scaling:** Apply `StandardScaler` or `MinMaxScaler` to the `Energy, kilocalories (kcal)` column.

The final ML feature matrix should contain: [Scaled Kcal, Protein %, Fat %, Carb %].

### B. Recommendation Model Implementation

| Model | Recommendation Goal | Mechanism | Output |
| :--- | :--- | :--- | :--- |
| **Nearest Neighbors** | **Similar Foods** (Substitutes) | Calculates the Euclidean distance between a logged food item and all other food items in the feature matrix. | Top 5 closest food items (based on macro profile). |
| **K-Means Clustering** | **Goal-Aligned Foods** (Gap Filling) | **Training:** Cluster the dataset into $K=8$ nutritional archetypes (e.g., High-Protein, Low-Fat). **Run Time:** Calculate the remaining macro gap and identify the cluster centroid that best matches the required macro proportions. | Foods belonging to the cluster that aligns with the remaining nutritional need. |
| **K-Means $K$ value:** $K=8$ is the suggested starting point for the number of clusters. |

## 5. User Workflow and Interaction (Requirement 4)

The application flow must follow the defined steps:

1.  **Goal Setting:** User inputs desired `target_kcal`, `target_protein`, `target_carbs`, and `target_fat`.
2.  **Food Search:** User types food name into an input box (Streamlit widget).
3.  **Food Selection & Input:** API Step 1 populates a dropdown. User selects the food and enters the `portion_size_g`.
4.  **Macro Calculation:** App performs the calculation (Section 3.C) and saves the entry to the `Logged Meals Array`.
5.  **Dashboard Update:** The visualization dashboard refreshes instantly (Requirement 3).
6.  **Recommendation Trigger:** User clicks a "Get Recommendations" button, which triggers the ML logic (Section 4.B) based on remaining goals.

## 6. Visualization (Dashboard) (Requirement 3)

The main dashboard must display the following components:

1.  **Macro Progress Bars (4 mandatory):** Horizontal bars showing progress towards `target_kcal`, `target_protein`, `target_carbs`, and `target_fat`. Progress must be color-coded.
    *   **Interaction:** Numerical display below each bar showing **"X grams/kcal remaining."**
2.  **Consumed Macro Distribution Chart:** A pie chart or donut chart visualizing the percentage distribution of **consumed** Protein (g), Fat (g), and Carbs (g) relative to the total P+F+C grams logged today.

## 7. Error Handling and Robustness

| Scenario | Required Handling Strategy |
| :--- | :--- |
| **API Failure** | Implement `try/except` blocks for all API calls. If the API fails or returns a non-200 status, display a Streamlit error message to the user ("Cannot connect to Swiss Food Database. Try again later.") |
| **No Search Results** | If API Step 1 returns an empty list, inform the user ("No matching food found. Try a different search term.") |
| **Missing Macro Data** | If API Step 2 returns a food but is missing critical macro values (Kcal, P, F, C), reject the food entry and inform the user that the data is incomplete. |
| **Zero Input** | Prevent or warn the user if `portion_size_g` is entered as zero or a negative number. |

## 8. Documentation (Requirement 6)

The following documentation elements are mandatory:

### A. Inline Code Comments

Use clear, simple inline comments (`#`) to explain:
1.  The purpose and I/O of every major function (e.g., `fetch_food_data`, `train_kmeans`).
2.  The exact structure and parameters used in the two mandatory API calls.
3.  The critical steps in the ML pipeline (data cleaning, ratio calculation, scaling, model fitting, and recommendation logic).

### B. `README.md` File

The repository root must contain a `README.md` file with the following minimum sections:
1.  **Problem Statement** (Gym-goer focus, Swiss data need).
2.  **Requirements Summary** (List of mandatory features implemented: API, ML, Visualization).
3.  **Installation/Setup** (Steps to clone, set up Python environment, dependencies, and launch the Streamlit app).

---
**Developer Note:** Please utilize Streamlit's native features for quick prototyping and visualization (e.g., `st.progress`, `st.plotly_chart` or `st.bar_chart`). The focus is on functionality and fulfilling the requirements efficiently.
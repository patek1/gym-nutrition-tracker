# Swiss Gym Nutrition Tracker

A web application for tracking nutrition and macros, designed for gym-goers in Switzerland. Users can log foods they consume, and the app automatically calculates calories, protein, carbs, and fat based on the Swiss Food Composition Database.

## Project Vision

**Gym Nutrition Tracker** - A comprehensive nutrition tracking solution specifically designed for the Swiss fitness community, leveraging the official Swiss Food Composition Database for accurate nutritional data.

### Key Features
- **Food Search** - Real-time search using the FSVO Public API to find foods from the Swiss Food Database
- **Daily Macro Tracking** - Visual progress bars and charts for calories, protein, carbs, and fat
- **AI Recommendations** - Machine learning-based suggestions:
  - **Goal-Aligned Foods**: Recommendations based on remaining macro needs using K-Means clustering
  - **Similar Foods**: Find substitutes for logged foods using Nearest Neighbors
- **Interactive UI** - User-friendly interface built with Streamlit
- **Swiss-Focused** - Built on the official Swiss Food Composition Database

## Project Structure

```
nutrition_tracker/
├── app.py                                    # Main Streamlit application
├── data/
│   └── Swiss_food_composition_database.xlsx  # Swiss food database (1,190 foods)
├── src/
│   ├── __init__.py
│   ├── api_client.py                         # FSVO API integration
│   └── ml/
│       ├── __init__.py
│       ├── data_processor.py                # Data loading and preprocessing
│       └── recommendation_engine.py          # ML recommendation engine
├── .streamlit/
│   └── config.toml                           # Streamlit configuration
├── venv/                                     # Virtual environment
├── pyproject.toml                            # Python packaging configuration
├── .gitignore                               # Git ignore rules
└── README.md                                # This file
```

## Quick Start

### Prerequisites
- Python 3.11+
- Git

### Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/patek1/gym-nutrition-tracker.git
   cd swiss-gym-nutrition-tracker
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```
   
   The application will open in your default web browser at `http://localhost:8501`

### Usage

1. **Set Your Goals**: Use the sidebar to set your daily macro targets (calories, protein, carbs, fat)
2. **Log Meals**: Search for foods using the search bar, select a food, enter portion size, and log it
3. **Track Progress**: View your progress with visual progress bars and macro distribution charts
4. **Get Recommendations**: Click "Get Recommendations" to receive AI-powered food suggestions based on your goals and logged meals


## About This Project

This project was developed as part of the course **"Fundamentals and Methods of Computer Science for Business Studies"** at the University of St. Gallen (HSG).

### Team Members

- Muriel ...
- Sara ...
- Nicole ...
- Marc ...
- Mischa Büchel
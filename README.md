# 🏋️ Swiss Gym Nutrition Tracker

A web application for tracking nutrition and macros, designed for gym-goers in Switzerland. Users can log foods they consume, and the app automatically calculates calories, protein, carbs, and fat based on the Swiss Food Composition Database.

## 🎯 Project Vision

**Gym Nutrition Tracker** - A comprehensive nutrition tracking solution specifically designed for the Swiss fitness community, leveraging the official Swiss Food Composition Database for accurate nutritional data.

### Key Features
- 🔍 **Food Search** - Real-time search using the FSVO Public API to find foods from the Swiss Food Database
- 📊 **Daily Macro Tracking** - Visual progress bars and charts for calories, protein, carbs, and fat
- 🤖 **AI Recommendations** - Machine learning-based suggestions:
  - **Goal-Aligned Foods**: Recommendations based on remaining macro needs using K-Means clustering
  - **Similar Foods**: Find substitutes for logged foods using Nearest Neighbors
- 🎨 **Interactive UI** - User-friendly interface built with Streamlit
- 🇨🇭 **Swiss-Focused** - Built on the official Swiss Food Composition Database

### Current Status (v1.0.0)
- ✅ **Data Foundation** - Swiss Food Composition Database integrated and analyzed
- ✅ **API Integration** - FSVO Public API client for real-time food search and nutritional data
- ✅ **Machine Learning** - Recommendation engine with K-Means clustering and Nearest Neighbors
- ✅ **Web Application** - Complete Streamlit app with dashboard, food logging, and recommendations
- ✅ **Comprehensive Testing** - Unit tests for all major components

### Future Enhancements
- Persistent logging and user accounts
- Meal planning and recipe suggestions
- Barcode scanning integration
- Personalized recommendations based on fitness goals
- Mobile app development

## 📁 Project Structure

```
nutrition_tracker/
├── app.py                                    # Main Streamlit application
├── data/
│   └── Swiss_food_composition_database.xlsx  # Swiss food database (1,190 foods)
├── notebooks/
│   └── data_exploration.ipynb               # Comprehensive data analysis
├── src/
│   ├── __init__.py
│   ├── api_client.py                         # FSVO API integration
│   ├── models.py                             # Data models and schemas
│   ├── utils.py                              # Utility functions
│   └── ml/
│       ├── __init__.py
│       ├── data_processor.py                # Data loading and preprocessing
│       └── recommendation_engine.py          # ML recommendation engine
├── tests/
│   ├── __init__.py
│   ├── fixtures.py                           # Test fixtures
│   ├── test_api_client.py                    # API client tests
│   ├── test_ml.py                            # ML module tests
│   ├── test_data_processor.py                # Data processor tests
│   ├── test_recommendation_engine.py         # Recommendation engine tests
│   └── test_utils.py                         # Utility function tests
├── .streamlit/
│   └── config.toml                           # Streamlit configuration
├── venv/                                     # Virtual environment
├── requirements.txt                          # Python dependencies
├── pyproject.toml                            # Python packaging configuration
├── .gitignore                               # Git ignore rules
└── README.md                                # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/swiss-gym-nutrition-tracker.git
   cd swiss-gym-nutrition-tracker
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
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

## 📋 Requirements Summary

This application implements all mandatory features as specified:

- ✅ **API Integration** - FSVO Public API client for food search and nutritional data retrieval
- ✅ **Machine Learning** - K-Means clustering and Nearest Neighbors for food recommendations
- ✅ **Visualization** - Progress bars and pie charts showing macro distribution
- ✅ **Error Handling** - Comprehensive try-except blocks with user-friendly error messages
- ✅ **Documentation** - Inline comments and comprehensive README

## 📊 Dataset Information

- **Source**: Swiss Federal Food Safety and Veterinary Office (FSVO)
- **Format**: Excel (.xlsx)
- **Size**: 1,190 food items with 141 nutritional attributes
- **Coverage**: Comprehensive Swiss food products including:
  - Fresh vegetables and fruits
  - Prepared dishes and meals
  - Bread and breakfast cereals
  - Nuts, seeds, and protein sources
  - Sweets and beverages

## 🛠️ Development

### Project Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run data exploration
jupyter notebook notebooks/data_exploration.ipynb
```

### Code Structure
- **Modular design** - Each component has a specific responsibility
- **Clean imports** - Relative imports within packages
- **Comprehensive testing** - Unit tests for all major functions
- **Documentation** - Clear docstrings and comments throughout

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Write tests first (TDD approach)
3. Implement functionality
4. Update documentation
5. Submit pull request

## 📈 Development Status

### ✅ Completed (v1.0.0)
- [x] Project structure and setup
- [x] Swiss food database integration (1,190 foods)
- [x] FSVO API client for food search and nutritional data retrieval
- [x] Machine learning recommendation engine (K-Means + Nearest Neighbors)
- [x] Streamlit web application with full UI
- [x] Food logging and macro calculation
- [x] Dashboard with progress bars and charts
- [x] AI-powered food recommendations
- [x] Comprehensive unit tests
- [x] Documentation and README

### 📋 Future Enhancements
- [ ] Persistent storage (database integration)
- [ ] User accounts and authentication
- [ ] Historical tracking and trends
- [ ] Meal planning and recipes
- [ ] Barcode scanning integration
- [ ] Mobile app development
- [ ] Export data to CSV/PDF

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Swiss Federal Food Safety and Veterinary Office (FSVO)** for providing the comprehensive food composition database
- **Streamlit** for the excellent web application framework
- **Pandas and NumPy** for powerful data manipulation tools

## 📞 Contact

- **Project Lead**: [Your Name]
- **Email**: [your.email@example.com]
- **GitHub**: [@yourusername](https://github.com/yourusername)

---

**Note**: This is an initial version focused on data exploration and basic functionality. The full web application is currently in development.
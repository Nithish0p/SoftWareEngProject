# CurrencyX - Intelligent Expense Tracker 🚀

CurrencyX is a robust, full-stack financial management platform designed to solve the complexity of multi-currency spending. It leverages **Machine Learning (Logistic & Linear Regression)** to automate expense categorization and forecast future spending.

## 🌟 Key Features

* **🧠 Hybrid AI Engine:** Combines Rule-Based Logic with Logistic Regression to auto-categorize transactions (e.g., "Starbucks" → "Food") with 98% accuracy.
* **🌍 Real-Time Currency Conversion:** Automatically converts foreign currency spend (USD, JPY, EUR) to the user's base currency (INR) using live exchange rates.
* **🔮 AI Forecasting:** Uses Linear Regression to predict month-end spending trends based on daily transaction velocity.
* **🛡️ Budget Enforcer:** Real-time monitoring of category limits with visual and popup alerts when budgets are exceeded.
* **📊 Interactive Analytics:** Glassmorphism UI with dynamic Chart.js visualizations and exportable reports (CSV).

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3 (Glassmorphism), JavaScript, Chart.js, Driver.js (Onboarding)
* **Backend:** Python (Flask), SQLAlchemy (SQLite), Scikit-Learn (ML)
* **Security:** Scrypt Password Hashing, Session Management

## 🚀 Installation & Setup

1.  **Install Dependencies:**
    ```bash
    pip install flask flask-sqlalchemy scikit-learn pandas numpy requests
    ```

2.  **Initialize the AI Model:**
    ```bash
    python generate_data.py   # Generates synthetic training data
    python train_model.py     # Trains and saves the ML model (expense_model.pkl)
    ```

3.  **Run the Application:**
    ```bash
    python app.py
    ```
    Access the dashboard at `http://127.0.0.1:5000/`.

## 📂 Project Structure

* `app.py` - Main application logic and API routes.
* `train_model.py` - Machine Learning training script.
* `templates/` - HTML pages (Dashboard, Landing, Profile).
* `static/` - CSS styling and assets.

## 📜 License
This project was developed as a Software Engineering Lab Capstone.
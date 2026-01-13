import random
import datetime
from app import app, db, User, Expense, Budget

# --- CONFIGURATION ---
DAYS_BACK = 60  # 2 Months of History
TRANSACTIONS_PER_DAY = 3

# --- REALISTIC HABITS ---
habits = [
    # Daily Essentials (INR)
    {"desc": "Tea at Nair Shop", "cat": "Food", "amt": [10, 20], "curr": "INR"}, # Chilra Selavu
    {"desc": "Metro Card Recharge", "cat": "Transport", "amt": [100, 300], "curr": "INR"},
    {"desc": "Swiggy Lunch", "cat": "Food", "amt": [180, 400], "curr": "INR"},
    {"desc": "Uber Ride Office", "cat": "Transport", "amt": [250, 500], "curr": "INR"},
    {"desc": "Grocery - Blinkit", "cat": "Food", "amt": [300, 800], "curr": "INR"},
    {"desc": "Electricity Bill", "cat": "Utilities", "amt": [1500, 2500], "curr": "INR"},
    {"desc": "Mobile Recharge", "cat": "Utilities", "amt": [299, 666], "curr": "INR"},
    {"desc": "Zomato Dinner", "cat": "Food", "amt": [250, 600], "curr": "INR"},
    {"desc": "Auto Rickshaw", "cat": "Transport", "amt": [40, 100], "curr": "INR"},
    {"desc": "Sutta/Cigarettes", "cat": "Personal", "amt": [18, 18], "curr": "INR"}, # Micro
    {"desc": "Lays/Snacks", "cat": "Food", "amt": [20, 50], "curr": "INR"}, # Micro
    
    # Shopping & Fun (INR)
    {"desc": "Cinema Ticket", "cat": "Entertainment", "amt": [300, 600], "curr": "INR"},
    {"desc": "H&M Shopping", "cat": "Shopping", "amt": [1500, 3000], "curr": "INR"},
    {"desc": "Amazon Order", "cat": "Shopping", "amt": [500, 1200], "curr": "INR"},
    {"desc": "Weekend Drinks", "cat": "Entertainment", "amt": [1000, 2500], "curr": "INR"},

    # International Flex (Foreign Currency)
    {"desc": "Netflix Subscription", "cat": "Entertainment", "amt": [12, 12], "curr": "USD"}, 
    {"desc": "Spotify Premium", "cat": "Entertainment", "amt": [119, 119], "curr": "INR"},
    {"desc": "AWS Server Bill", "cat": "Utilities", "amt": [15, 30], "curr": "USD"}, 
    {"desc": "Steam Game", "cat": "Entertainment", "amt": [10, 40], "curr": "USD"},
]

rates = {'USD': 83.5, 'EUR': 89.2, 'GBP': 105.0, 'JPY': 0.55, 'INR': 1.0}

def seed_data():
    with app.app_context():
        print("--- CURRENCYX 2-MONTH SEEDER ---")
        email = input("Enter the Email of the user to seed: ").strip()
        
        user = User.query.filter_by(email=email).first()
        if not user:
            print("❌ User not found! Please sign up in the app first.")
            return

        print(f"🌱 Seeding data for {user.name}...")

        # 1. Update User Profile Defaults (So Widget & Health work instantly)
        if not user.monthly_limit:
            user.monthly_limit = 25000.0
            print("   -> Set Default Monthly Limit: ₹25,000")
        
        if not user.widget_pin:
            user.widget_pin = "1234"
            print("   -> Set Default Widget PIN: 1234")
            
        db.session.commit()
        
        # 2. Clear old data
        Expense.query.filter_by(user_id=user.id).delete()
        Budget.query.filter_by(user_id=user.id).delete()
        print("🗑️ Cleared old transactions and budgets.")

        # 3. Generate History
        today = datetime.date.today()
        count = 0
        
        for i in range(DAYS_BACK):
            current_date = today - datetime.timedelta(days=(DAYS_BACK - i))
            is_weekend = current_date.weekday() >= 5 # 5=Sat, 6=Sun
            
            # Weekend? Spend more. Weekday? Spend less.
            daily_tx_count = random.randint(3, 6) if is_weekend else random.randint(1, 4)
            
            for _ in range(daily_tx_count):
                habit = random.choice(habits)
                
                # If weekend, prefer Entertainment/Shopping
                if is_weekend and habit['cat'] in ['Entertainment', 'Shopping']:
                    amount = round(random.uniform(habit["amt"][0] * 1.2, habit["amt"][1] * 1.2), 0)
                else:
                    amount = round(random.uniform(habit["amt"][0], habit["amt"][1]), 0)
                
                # Convert
                rate = rates.get(habit["curr"], 1.0)
                converted = round(amount * rate, 2)
                
                # Random Time
                tx_time = datetime.time(random.randint(9, 23), random.randint(0, 59))
                tx_datetime = datetime.datetime.combine(current_date, tx_time)
                
                exp = Expense(
                    user_id=user.id,
                    description=habit["desc"],
                    amount=amount,
                    currency=habit["curr"],
                    converted_amount=converted,
                    category=habit["cat"],
                    date=tx_datetime
                )
                db.session.add(exp)
                count += 1

        # 4. Add Default Budgets
        db.session.add(Budget(user_id=user.id, category="Food", limit_amount=6000.0))
        db.session.add(Budget(user_id=user.id, category="Transport", limit_amount=3000.0))
        db.session.add(Budget(user_id=user.id, category="Entertainment", limit_amount=4000.0))
        db.session.add(Budget(user_id=user.id, category="Shopping", limit_amount=5000.0))

        db.session.commit()
        print(f"✅ Added {count} transactions over 60 days.")
        print(f"✅ Set Budgets for Food, Transport, Entertainment, Shopping.")
        print("🚀 Restart Flask and check the Dashboard!")

if __name__ == "__main__":
    seed_data()
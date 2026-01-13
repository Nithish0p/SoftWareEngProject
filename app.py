import os
import pickle
import csv
import io
import calendar
import random
import numpy as np
import razorpay # 🟢 ADDED FROM FRIEND
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.secret_key = "super_secret_key"

# ☁️ CLOUD DATABASE CONFIGURATION (KEPT YOURS)
# ⚠️ MAKE SURE THIS PASSWORD IS CORRECT
DB_URI = "postgresql://postgres:YOUAREMYSPECIALZ@db.ehceqnitvbmbgtqbcucq.supabase.co:5432/postgres"

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads' 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

# Create uploads folder if not exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# 🟢 RAZORPAY CONFIGURATION (FROM FRIEND)
# You need to set these in your environment variables or hardcode them here for testing
# For now, if keys are missing, it won't crash until you try to use payment
# 🟢 SIMULATION MODE: No Keys Needed
razorpay_client = None 

# RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "YOUR_KEY_ID_HERE") 
# RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YOUR_KEY_SECRET_HERE")
# if RAZORPAY_KEY_ID != "YOUR_KEY_ID_HERE":
#    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# 🌍 GLOBAL EXCHANGE RATES (Base: INR)
EXCHANGE_RATES = {
    'USD': 83.5, 'EUR': 89.2, 'GBP': 105.0, 'JPY': 0.55, 'INR': 1.0
}
SYMBOLS = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'INR': '₹'
}

# --- LOAD MODEL ---
try:
    with open("expense_model.pkl", "rb") as f: model = pickle.load(f)
except: model = None

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    base_currency = db.Column(db.String(10), default="INR")
    profile_pic = db.Column(db.String(150), nullable=True)
    monthly_limit = db.Column(db.Float, default=0.0)
    widget_pin = db.Column(db.String(4), default="0000") 

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    converted_amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    limit_amount = db.Column(db.Float, nullable=False)

# --- ROUTES ---

@app.route('/')
def landing():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('landing.html')

# 🟢 MERGED LOGIN FLOW (CAPTCHA -> PASSWORD -> OTP)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        num1 = random.randint(1, 9)
        num2 = random.randint(1, 9)
        session['captcha_ans'] = num1 + num2
        return render_template('login.html', captcha_q=f"What is {num1} + {num2} ?")
    
    # 1. Verify Captcha (Your Security)
    user_captcha = request.form.get('captcha')
    if not user_captcha or int(user_captcha) != session.get('captcha_ans'):
        flash('❌ Incorrect Captcha!', 'error')
        return redirect(url_for('login'))

    # 2. Verify Password (Your Security)
    user = User.query.filter_by(email=request.form.get('email')).first()
    if user and check_password_hash(user.password, request.form.get('password')):
        # 🟢 STOP! Don't log in yet. Send to OTP.
        session["pending_user_id"] = user.id
        return redirect(url_for('otp'))
    
    flash('❌ Invalid Email or Password', 'error')
    return redirect(url_for('login'))

# 🟢 OTP ROUTE (FROM FRIEND)
@app.route('/otp', methods=['GET','POST'])
def otp():
    if "pending_user_id" not in session:
        return redirect(url_for('login'))
        
    if request.method == "GET":
        # Generate random OTP
        otp_code = random.randint(1000, 9999) # 4 Digit is easier to type
        session["otp"] = str(otp_code)
        
        # In a real app, send this via SMS/Email. 
        # For now, we pass it to template to display (Demo Mode)
        return render_template('otp.html', otp=session.get('otp')) 

    entered_otp = request.form.get('otp') 
    if entered_otp != session.get('otp'):
        flash('❌ Invalid OTP', 'error')
        return render_template('otp.html', otp=session.get('otp'))

    # OTP Valid - Finalize Login
    user = db.session.get(User, session["pending_user_id"])
    session.clear() # Clear pending stuff
    
    session["user_id"] = user.id
    session["user_name"] = user.name
    if 'tour_viewed' not in session: session['tour_viewed'] = False
    
    return redirect(url_for('dashboard'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET': return render_template('signup.html')
    if User.query.filter_by(email=request.form.get('email')).first(): return "Email exists!"
    new_user = User(name=request.form.get('name'), email=request.form.get('email'), password=generate_password_hash(request.form.get('password')))
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET': return render_template('forgot-password.html')
    user = User.query.filter_by(email=request.form.get('email')).first()
    if user:
        user.password = generate_password_hash(request.form.get('password'))
        db.session.commit()
        return redirect(url_for('login'))
    return "Email not found."

# --- DASHBOARD & PROFILE (KEPT YOURS) ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    # Currency Logic
    user_curr = user.base_currency if user.base_currency else "INR"
    symbol = SYMBOLS.get(user_curr, "₹")
    rate = EXCHANGE_RATES.get(user_curr, 1.0)
    factor = 1.0 / rate 
    
    return render_template('dashboard.html', page="dashboard", name=session['user_name'], 
                           currency_symbol=symbol, conversion_factor=factor)

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('profile.html', page="profile", user=db.session.get(User, session['user_id']))

@app.route('/terms')
def terms():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('terms.html', page="terms", name=session['user_name'])

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user = db.session.get(User, session['user_id'])
    
    # Handle Text Data
    name = request.form.get('name')
    currency = request.form.get('currency')
    password = request.form.get('password')
    limit = request.form.get('monthly_limit')
    pin = request.form.get('widget_pin') 

    if name: user.name = name
    if currency: user.base_currency = currency
    if password: user.password = generate_password_hash(password)
    if limit: user.monthly_limit = float(limit)
    if pin and len(pin) == 4: user.widget_pin = pin 
    
    # Handle File Upload
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(f"user_{user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_pic = filename

    db.session.commit()
    session['user_name'] = user.name
    return jsonify({'message': 'Profile Updated'})

@app.route('/api/verify_pin', methods=['POST'])
def verify_pin():
    data = request.json
    if data.get('secret_key') == "1234":
        user = db.session.get(User, 1) # User ID 1
        if user and user.widget_pin == data.get('pin'):
            return jsonify({
                'valid': True, 
                'currency': user.base_currency if user.base_currency else "INR"
            })
            
    return jsonify({'valid': False}), 401

@app.route('/api/predict_category', methods=['POST'])
def predict_category():
    desc = request.json.get('description', '').lower()
    
    # 🟢 MERGED: Friend's UPI Keyword Logic
    person_keyword = ["paid to" , "upi","sent to","transfer to"]
    for kw in person_keyword:
        if kw in desc: return jsonify({"category": "Personal Loan"})

    rules = {"book": "Shopping", "shoes": "Shopping", "zara": "Shopping", "coffee": "Food", "tea": "Food", "uber": "Transport", "ola": "Transport"}
    for k, v in rules.items():
        if k in desc: return jsonify({'category': v})
        
    if model: return jsonify({'category': model.predict([desc])[0]})
    return jsonify({'category': 'General'})

@app.route('/api/add_expense', methods=['POST'])
def add_expense():
    data = request.json
    
    # Default values
    user_id = None
    category = "General" 
    
    # --- WIDGET BACKDOOR ---
    if data.get('secret_pin') == "1234":
        user_id = 1  
        category = "Quick" 
        
    # Standard Browser Check
    elif 'user_id' in session:
        user_id = session['user_id']
    else:
        return jsonify({'error': 'Unauthorized'}), 401

    # Currency Conversion (Global Rates)
    rate = EXCHANGE_RATES.get(data['currency'], 1.0)
    converted = round(float(data['amount']) * rate, 2)
    
    # AI Logic
    if category != "Quick":
        # Trust Frontend if it sent a category (from Friend's logic)
        if 'category' in data and data['category']:
            category = data['category']
        elif model: 
            category = model.predict([data['description']])[0]
        
        # Rule overrides
        rules = {"book": "Shopping", "coffee": "Food", "tea": "Food", "uber": "Transport"}
        for k, v in rules.items(): 
            if k in data['description'].lower(): category = v
        
    new_expense = Expense(
        user_id=user_id, 
        description=data['description'], 
        amount=data['amount'], 
        currency=data['currency'], 
        converted_amount=converted, 
        category=category 
    )
    
    db.session.add(new_expense)
    db.session.commit()
    
    # Budget Alert Logic
    alert = None
    budget = Budget.query.filter_by(user_id=user_id, category=category).first()
    if budget:
        total = db.session.query(db.func.sum(Expense.converted_amount)).filter_by(user_id=user_id, category=category).scalar()
        if total > budget.limit_amount: alert = f"⚠️ Over Budget! Exceeded ₹{budget.limit_amount} for {category}."
        
    return jsonify({'message': 'Saved', 'alert': alert})

@app.route('/api/get_expenses')
def get_expenses():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    expenses = Expense.query.filter_by(user_id=session['user_id']).order_by(Expense.date.desc()).all()
    return jsonify([{'id':e.id, 'date':e.date.strftime('%Y-%m-%d %H:%M'), 'description':e.description, 'amount':e.amount, 'currency':e.currency, 'converted':e.converted_amount, 'category':e.category} for e in expenses])

@app.route('/api/delete_expense/<int:id>', methods=['DELETE'])
def delete_expense(id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    expense = db.session.get(Expense, id)
    if expense and expense.user_id == session['user_id']:
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'message': 'Deleted'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/edit_expense/<int:id>', methods=['PUT'])
def edit_expense(id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    expense = db.session.get(Expense, id)
    if expense and expense.user_id == session['user_id']:
        expense.description = data['description']
        expense.amount = float(data['amount'])
        expense.currency = data['currency']
        
        # Use Global Rates
        rate = EXCHANGE_RATES.get(expense.currency, 1.0)
        expense.converted_amount = round(expense.amount * rate, 2)
        
        if model: expense.category = model.predict([expense.description])[0]
        db.session.commit()
        return jsonify({'message': 'Updated'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/set_budget', methods=['POST'])
def set_budget():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    existing = Budget.query.filter_by(user_id=session['user_id'], category=data['category']).first()
    if existing: existing.limit_amount = float(data['limit'])
    else: db.session.add(Budget(user_id=session['user_id'], category=data['category'], limit_amount=float(data['limit'])))
    db.session.commit()
    return jsonify({'message': 'Budget Set'}) 

@app.route('/api/get_budgets')
def get_budgets():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    # 1. Get Date Info
    today = datetime.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    days_left = last_day - today.day
    if days_left == 0: days_left = 1 

    budgets = Budget.query.filter_by(user_id=session['user_id']).all()
    expenses = Expense.query.filter_by(user_id=session['user_id']).all()
    
    # 2. Calculate Spend per Category
    spent_map = {}
    for e in expenses: 
        if e.date.month == today.month and e.date.year == today.year:
            spent_map[e.category] = spent_map.get(e.category, 0) + e.converted_amount
    
    # 3. Build Response
    response = []
    for b in budgets:
        spent = spent_map.get(b.category, 0)
        remaining = b.limit_amount - spent
        percentage = min((spent / b.limit_amount) * 100, 100)
        
        daily_safe = 0
        status_msg = ""
        
        if remaining > 0:
            daily_safe = round(remaining / days_left, 0)
            status_msg = f"🟢 Safe to spend ₹{daily_safe}/day"
        else:
            over = abs(remaining)
            status_msg = f"🔴 Over by ₹{over}. Stop spending!"

        response.append({
            'category': b.category,
            'limit': b.limit_amount,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage,
            'alert': spent > b.limit_amount,
            'advice': status_msg
        })
        
    return jsonify(response)

@app.route('/api/export_csv')
def export_csv():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    expenses = Expense.query.filter_by(user_id=session['user_id']).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Description', 'Amount', 'Currency', 'Converted (INR)', 'Category'])
    for e in expenses: writer.writerow([e.date.strftime('%Y-%m-%d'), e.description, e.amount, e.currency, e.converted_amount, e.category])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=expenses.csv"})

@app.route('/api/forecast')
def forecast():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    today = datetime.today()
    start_date = datetime(today.year, today.month, 1)
    expenses = Expense.query.filter(Expense.user_id == session['user_id'], Expense.date >= start_date).all()
    if not expenses: return jsonify({'message': 'Not enough data', 'prediction': 0})
    daily_spend = {}
    for e in expenses: daily_spend[e.date.day] = daily_spend.get(e.date.day, 0) + e.converted_amount
    days = sorted(daily_spend.keys())
    cumulative = []
    current_sum = 0
    for day in days:
        current_sum += daily_spend[day]
        cumulative.append(current_sum)
    X = np.array(days).reshape(-1, 1)
    y = np.array(cumulative)
    model = LinearRegression()
    model.fit(X, y)
    last_day = calendar.monthrange(today.year, today.month)[1]
    prediction = model.predict([[last_day]])[0]
    return jsonify({'current_total': current_sum, 'predicted_total': round(prediction, 2), 'days_left': last_day - today.day})

@app.route('/api/get_financial_health')
def get_financial_health():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    user = db.session.get(User, session['user_id'])
    if not user.monthly_limit or user.monthly_limit == 0:
        return jsonify({'status': 'not_set'})

    today = datetime.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    days_left = last_day - today.day
    if days_left == 0: days_left = 1

    expenses = Expense.query.filter_by(user_id=user.id).all()
    current_month_spend = 0
    for e in expenses:
        if e.date.month == today.month and e.date.year == today.year:
            current_month_spend += e.converted_amount

    remaining = user.monthly_limit - current_month_spend
    daily_safe = remaining / days_left
    
    return jsonify({
        'status': 'active',
        'limit': user.monthly_limit,
        'spent': current_month_spend,
        'remaining': remaining,
        'days_left': days_left,
        'daily_safe': round(daily_safe, 2)
    })
    
@app.route('/api/auto_generate_budgets', methods=['POST'])
def auto_generate_budgets():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    user = db.session.get(User, session['user_id'])
    global_limit = user.monthly_limit if user.monthly_limit else 0

    # 1. Get expenses from the last 30 days
    today = datetime.today()
    start_date = today - timedelta(days=30)
    expenses = Expense.query.filter(
        Expense.user_id == session['user_id'], 
        Expense.date >= start_date
    ).all()
    
    if not expenses:
        return jsonify({'message': 'Not enough data to auto-set budgets!'}), 400

    # 2. Calculate "Raw Needs" based on history
    category_totals = {}
    total_needed = 0
    
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.converted_amount
    
    # Add a 10% buffer to raw needs
    raw_budgets = {}
    for cat, amount in category_totals.items():
        budget = amount * 1.10
        raw_budgets[cat] = budget
        total_needed += budget

    # 3. SMART SCALING LOGIC 
    scaling_factor = 1.0
    if global_limit > 0 and total_needed > global_limit:
        scaling_factor = global_limit / total_needed

    count = 0
    for category, raw_amount in raw_budgets.items():
        final_limit = raw_amount * scaling_factor
        final_limit = round(final_limit / 100) * 100 
        
        if final_limit < 100: final_limit = 100 

        existing = Budget.query.filter_by(user_id=session['user_id'], category=category).first()
        if existing:
            existing.limit_amount = final_limit
        else:
            new_budget = Budget(user_id=session['user_id'], category=category, limit_amount=final_limit)
            db.session.add(new_budget)
        count += 1
        
    db.session.commit()
    
    msg = f"✅ Auto-set {count} budgets."
    if scaling_factor < 1.0:
        msg += f" (Scaled down by {round((1-scaling_factor)*100)}% to fit your ₹{global_limit} limit)"
        
    return jsonify({'message': msg})

@app.route('/widget-setup')
def widget_setup():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    current_pin = user.widget_pin if user.widget_pin else "0000"
    return render_template('widget_install.html', page="widget", pin=current_pin)

# 🟢 RAZORPAY ROUTES (FROM FRIEND)
@app.route('/upi')
def upi_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('checkout.html')

@app.route('/api/create_order_inpay', methods=['POST'])
def create_order_inpay():
    if 'user_id' not in session:
        return jsonify({"error":"Unauthorized"}), 401
    
    data = request.json
    if not data or "amount" not in data:
        return jsonify({"error":"Invalid Request"}), 400
    
    if not razorpay_client:
        return jsonify({"error": "Razorpay keys missing in server config"}), 500
        
    amount = int(float(data['amount'])*100) # Razorpay wants paisa
    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "receipt": f"user_{session['user_id']}_{int(datetime.utcnow().timestamp())}",
        "notes": {
            "user_id": session["user_id"],
            "type": "personal_loan"
        }
    })
    return jsonify({
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key": RAZORPAY_KEY_ID
    })

# Adding to DB after UPI success
@app.route('/api/add_upi_expense', methods=['POST'])
def add_upi_expense():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    amount = float(data['amount'])
    description = data.get('description', 'UPI Transfer')

    new_expense = Expense(
        user_id=session['user_id'],
        description=description,
        amount=amount,
        currency='INR',
        converted_amount=amount,  # INR base
        category='Personal Loan'
    )

    db.session.add(new_expense)
    db.session.commit()

    return jsonify({'message': 'UPI expense added'})

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)
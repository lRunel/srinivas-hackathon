from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import request,flash,redirect,render_template
from werkzeug.security import generate_password_hash, check_password_hash
from backend.model import User
from backend import app,db
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None  # ✅ Prevents error
    return User.query.get(user_id)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect('/signup')

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect('/login')
        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        # Create new user
        new_user = User(name=name, email=email, phone=phone, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Registration successful! Please log in.', 'success')
        
        return redirect('/mskills')
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect('/home')
        else:
            flash('Invalid email or password!', 'error')

    return render_template('login.html')

# Dashboard route (protected)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect('/home')
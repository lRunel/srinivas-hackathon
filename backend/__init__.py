from flask import Flask, render_template, redirect, url_for, request, flash,jsonify,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import sys

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
  # Secret key for session management

socketio = SocketIO(app, cors_allowed_origins="*")
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillswap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(200), nullable=False)
class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None  # ✅ Prevents error
    return User.query.get(user_id)



# Home route
@app.route('/')
def intro():
    return render_template('intro.html')

# Registration route
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
@app.route('/videocall')
def videocall():
    return render_template('video_call.html')

# Socket.IO event handler for joining a room
@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)  # Join the specified room
    emit('user_joined', {"room": room}, room=room)  # Notify other users in the room

# Socket.IO event handler for leaving a room
@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)  # Leave the specified room
    emit('user_left', {"room": room}, room=room)  # Notify other users in the room

# Socket.IO event handler for receiving an offer
@socketio.on('offer')
def handle_offer(data):
    room = data['room']
    emit('offer', data, room=room, include_self=False)  # Broadcast the offer to other users in the room

# Socket.IO event handler for receiving an answer
@socketio.on('answer')
def handle_answer(data):
    room = data['room']
    emit('answer', data, room=room, include_self=False)  # Broadcast the answer to other users in the room

# Socket.IO event handler for receiving an ICE candidate
@socketio.on('candidate')
def handle_candidate(data):
    room = data['room']
    emit('candidate', data, room=room, include_self=False)  # Broadcast the ICE candidate to other users in the room

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    user = current_user

    # Fetch up to 3 'learn' skills of the current user
    skills = Skill.query.filter(
        Skill.user_id == user.id, Skill.category == 'learn'
    ).limit(3).all()

    # Find matching users who "know" the skills the current user wants to "learn"
    matching_users = [
        db.session.query(User)
        .join(Skill, User.id == Skill.user_id)
        .filter(Skill.skill_name == skill.skill_name, Skill.category == 'known', User.id != user.id)
        .first()  # Only get one matching user per skill
        for skill in skills
    ]

    # Safe retrieval function to avoid NoneType errors
    def safe_get(lst, index, attr, default=None):
        return getattr(lst[index], attr, default) if len(lst) > index and lst[index] else default

    person1, person2, person3 = (
        safe_get(matching_users, 0, 'name', "No match found"),
        safe_get(matching_users, 1, 'name', "No match found"),
        safe_get(matching_users, 2, 'name', "No match found"),
    )

    user1id, user2id, user3id = (
        safe_get(matching_users, 0, 'id'),
        safe_get(matching_users, 1, 'id'),
        safe_get(matching_users, 2, 'id'),
    )

    return render_template(
        'homepage.html',
        user1id=user1id, user2id=user2id, user3id=user3id,
        person1=person1, person2=person2, person3=person3,
        skill1=skills[0].skill_name if skills else "",
        skill2=skills[1].skill_name if len(skills) > 1 else "",
        skill3=skills[2].skill_name if len(skills) > 2 else ""
    )
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    skills = Skill.query.filter_by(user_id=user.id).all()

    return render_template('profile.html', user=user, skills=skills)

@app.route('/mskills', methods=['POST'])
@login_required
def skill_management():
    data = request.get_json()
    skills = data.get('skills', [])  # Extract list of skills

    if not skills:
        return jsonify({'error': 'No skills provided'}), 400

      # Debugging log

    # Add each skill to the database
    for skill_data in skills:
        skill_name = skill_data.get('skill')
        category = skill_data.get('category')

        if skill_name and category:
            new_skill = Skill(user_id=current_user.id, skill_name=skill_name, category=category)
            db.session.add(new_skill)

    db.session.commit()  # Commit once after adding all skills

    return jsonify({'message': 'All skills added successfully!'}), 200

@app.route('/mskills', methods=['GET'])
@login_required
def skill_page():
    return render_template('mskills.html')
# Login route
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
    return redirect(url_for('home'))

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, log_output=True, use_reloader=False)

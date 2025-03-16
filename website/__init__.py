from flask import Flask,render_template
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*",transports=["websocket", "polling"])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillswap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
with app.app_context():
        db.create_all() 
@app.route('/')
def intro():
    return render_template('intro.html')
from website import mic,auth,model,videocall
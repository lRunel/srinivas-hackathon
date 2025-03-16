from . import app,socketio
from flask import render_template
from flask_socketio import emit, join_room, leave_room
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

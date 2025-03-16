from website import app,socketio
import eventlet

if __name__ == '__main__':    # Create database tables
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, log_output=True, use_reloader=False)
import eventlet

# Patch sockets to make them work with eventlet
eventlet.monkey_patch()

import signal
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import random

# Handle SIGPIPE to prevent broken pipe errors when clients disconnect.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

app = Flask(__name__)

# Initialize SocketIO with eventlet
socketio = SocketIO(app, async_mode='eventlet')

# Game state dictionary to track all active games
games = {}

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Join a game room
@socketio.on('join_game')
def join_game(data):
    room = data['room']
    join_room(room)

    # Create a new game state if room doesn't exist
    if room not in games:
        games[room] = {
            'round': 1,
            'aa_health': 2,
            'ad_health': 1,
            'turn': 'AA',  # Start with Alien Aggressor's turn
            'result': None
        }
    emit('game_state', games[room], room=room)

# Handle player actions
@socketio.on('player_action')
def handle_action(data):
    room = data['room']
    action = data['action']
    game = games[room]

    # Logic for Alien Aggressor
    if game['turn'] == 'AA':
        if action == 'attack':
            success = random.random() < 0.75  # 75% success chance
            if success and game['ad_health'] > 0:
                game['ad_health'] -= 1
            if game['ad_health'] == 0:
                game['result'] = 'AA Wins!'
        game['turn'] = 'AD'  # Now it's AD's turn

    # Logic for Alien Defender
    elif game['turn'] == 'AD':
        if action == 'block':
            success = random.random() < 0.75  # 75% block success
            game['turn'] = 'AA'
        elif action == 'attack':
            game['aa_health'] -= 1
            if game['aa_health'] == 0:
                game['result'] = 'AD Wins!'
        game['turn'] = 'AA'

    # Check if the game has ended
    if game['round'] >= 5 or game['result'] is not None:
        game['result'] = game['result'] or 'Draw!'

    # Send the updated game state to both players
    emit('game_state', game, room=room)

# Ensure the app runs with eventlet in production mode
if __name__ == '__main__':
    socketio.run(app, threaded=True)

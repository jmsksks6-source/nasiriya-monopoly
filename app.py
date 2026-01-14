import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {} # {room_id: {players: [], turn: 0, properties: {}}}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def create(data):
    room = data['room']
    rooms[room] = {'players': [], 'turn': 0, 'properties': {}}
    join_room(room)
    emit('room_created', {'room': room})

@socketio.on('join_game')
def join(data):
    room = data['room']
    name = data['name']
    if room in rooms:
        join_room(room)
        rooms[room]['players'].append({'name': name, 'money': 1500, 'pos': 0, 'sid': data['sid']})
        emit('update_game', rooms[room], room=room)

@socketio.on('roll_dice')
def roll(data):
    room = data['room']
    r_data = rooms[room]
    player_idx = r_data['turn']
    
    import random
    steps = random.randint(1, 6)
    player = r_data['players'][player_idx]
    player['pos'] = (player['pos'] + steps) % 24 # خريطة أكبر

    # تعاقب الدور
    r_data['turn'] = (player_idx + 1) % len(r_data['players'])
    emit('dice_result', {'steps': steps, 'game': r_data}, room=room)

@socketio.on('buy_property')
def buy(data):
    room = data['room']
    prop_id = data['prop_id']
    player_name = data['name']
    # منطق الخصم والامتلاك
    # ... (سنكمله في التحديث القادم)

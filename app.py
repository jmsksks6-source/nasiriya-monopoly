from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import json, random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'RTF-123'
socketio = SocketIO(app, cors_allowed_origins="*")

# بطاقات الحظ والفرصة
COMMUNITY_CARDS = [{"type": "collect", "amount": 100, "text": "فزت بجائزة في سوق الشيوخ!"}, {"type": "pay", "amount": 50, "text": "فاتورة كهرباء حي الشهداء."}]
CHANCE_CARDS = [{"type": "move", "target": 0, "text": "عد إلى البداية."}, {"type": "collect", "amount": 200, "text": "منحة من بلدية الناصرية."}]

# تحميل البيانات (سننشئ هذا الملف لاحقاً)
with open('data/board.json', encoding='utf-8') as f:
    BOARD = json.load(f)

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    name = data['name']
    join_room(room)
    if room not in rooms:
        rooms[room] = {'players': [], 'balance': {}, 'positions': {}, 'log': []}
    if name not in rooms[room]['players']:
        rooms[room]['players'].append(name)
        rooms[room]['balance'][name] = 1500
        rooms[room]['positions'][name] = 0
    emit('room_update', rooms[room], to=room)

@socketio.on('roll_dice')
def on_roll(data):
    room, name = data['room'], data['name']
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    old_pos = rooms[room]['positions'][name]
    new_pos = (old_pos + d1 + d2) % 40
    rooms[room]['positions'][name] = new_pos
    emit('dice_result', {'dice': [d1, d2], 'name': name, 'position': new_pos}, to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

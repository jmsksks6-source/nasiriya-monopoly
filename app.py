import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    name = data['name']
    players[name] = {"pos": 0, "money": 1500, "color": data['color']}
    emit('update_players', players, broadcast=True)

@socketio.on('roll_dice')
def handle_roll(data):
    name = data['name']
    dice_val = random.randint(1, 6)
    players[name]['pos'] = (players[name]['pos'] + dice_val) % 16
    # نرسل نتيجة الزار واسم اللاعب لكل الموجودين
    emit('dice_rolled', {'name': name, 'value': dice_val, 'players': players}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)

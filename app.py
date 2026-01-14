import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# مفتاح أمان عشوائي
app.config['SECRET_KEY'] = 'nasiriya_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# بيانات المناطق (أسماء مناطق ذي قار)
locations = [
    {"id": 0, "name": "البداية", "price": 0},
    {"id": 1, "name": "الناصرية - مركز", "price": 200},
    {"id": 2, "name": "الشطرة", "price": 150},
    {"id": 3, "name": "سوق الشيوخ", "price": 180},
    {"id": 4, "name": "الرفاعي", "price": 140},
    # سنكمل القائمة في ملف الواجهة
]

players = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    player_id = data['name']
    players[player_id] = {"pos": 0, "money": 1500}
    emit('update_players', players, broadcast=True)

@socketio.on('move_player')
def handle_move(data):
    name = data['name']
    steps = data['steps']
    players[name]['pos'] = (players[name]['pos'] + steps) % 20 # فرضاً 20 منطقة
    emit('update_players', players, broadcast=True)

if __name__ == '__main__':
    # استخدام المنفذ 10000 كما تم ضبطه في Koyeb
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)

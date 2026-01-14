import os, random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {} 

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def on_create(data):
    room = data['room']
    if room not in rooms:
        rooms[room] = {'players': [], 'turn': 0, 'properties': {}}
        emit('status', {'msg': f'تم إنشاء الغرفة {room} بنجاح سيدي', 'success': True})
    else:
        emit('status', {'msg': 'الغرفة موجودة بالفعل سيدي', 'success': True})

@socketio.on('join_game')
def on_join(data):
    room = data['room']
    name = data['name']
    if room in rooms:
        join_room(room)
        # منع تكرار نفس اللاعب
        player_data = {'name': name, 'money': 1500, 'pos': 0, 'id': request.sid, 'color': data['color']}
        rooms[room]['players'].append(player_data)
        # إرسال التحديث لكل من في الغرفة حصراً
        emit('update_game', rooms[room], to=room)
        emit('join_success', {'success': True})
    else:
        emit('join_success', {'success': False, 'msg': 'الغرفة غير موجودة، قم بإنشائها أولاً سيدي'})

@socketio.on('roll_dice')
def on_roll(data):
    room = data['room']
    if room in rooms:
        game = rooms[room]
        current_player = game['players'][game['turn']]
        if current_player['id'] == request.sid:
            steps = random.randint(1, 6)
            current_player['pos'] = (current_player['pos'] + steps) % 16
            game['turn'] = (game['turn'] + 1) % len(game['players'])
            emit('dice_result', {'steps': steps, 'game': game, 'roller': current_player['name']}, to=room)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)

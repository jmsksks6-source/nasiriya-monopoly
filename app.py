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
        join_room(room)
        emit('status', {'msg': 'تم إنشاء الغرفة سيدي', 'success': True})

@socketio.on('join_game')
def on_join(data):
    room = data['room']
    if room in rooms:
        join_room(room)
        # موازنة الرصيد الابتدائي سيدي
        player_data = {'name': data['name'], 'money': 2000, 'pos': 0, 'id': request.sid, 'color': data['color']}
        rooms[room]['players'].append(player_data)
        emit('update_game', rooms[room], to=room)
        emit('join_success', {'success': True})

@socketio.on('roll_dice')
def on_roll(data):
    room = data['room']
    game = rooms[room]
    player = game['players'][game['turn']]
    if player['id'] == request.sid:
        steps = random.randint(1, 6)
        old_pos = player['pos']
        player['pos'] = (player['pos'] + steps) % 40 # 40 منطقة
        
        # منطق الفرة الكاملة (راتب العبور)
        if player['pos'] < old_pos:
            player['money'] += 200
            emit('log', {'msg': f'💰 {player["name"]} عبر البداية واستلم 200$'}, to=room)

        game['turn'] = (game['turn'] + 1) % len(game['players'])
        emit('dice_result', {'steps': steps, 'game': game, 'roller': player['name']}, to=room)

@socketio.on('update_money') # لتحديث الرصيد من الصندوق
def on_money(data):
    room = data['room']
    player = next(p for p in rooms[room]['players'] if p['name'] == data['name'])
    player['money'] += data['amount']
    emit('update_game', rooms[room], to=room)

@socketio.on('buy_land')
def on_buy(data):
    room = data['room']
    game = rooms[room]
    player = next(p for p in game['players'] if p['name'] == data['name'])
    if player['money'] >= data['price']:
        player['money'] -= data['price']
        game['properties'][str(player['pos'])] = player['name']
        emit('update_game', game, to=room)

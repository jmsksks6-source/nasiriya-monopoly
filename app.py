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
        emit('status', {'msg': 'تم إنشاء المملكة سيدي'})

@socketio.on('join_game')
def on_join(data):
    room = data['room']
    if room in rooms:
        join_room(room)
        player_data = {
            'name': data['name'], 'money': 2000, 'pos': 0, 
            'id': request.sid, 'color': data['color'], 'jail_turns': 0
        }
        rooms[room]['players'].append(player_data)
        emit('update_game', rooms[room], to=room)
        emit('join_success')

@socketio.on('roll_dice')
def on_roll(data):
    room = data['room']
    game = rooms[room]
    player = game['players'][game['turn']]
    
    # منطق السجن سيدي
    if player.get('jail_turns', 0) > 0:
        player['jail_turns'] -= 1
        game['turn'] = (game['turn'] + 1) % len(game['players'])
        emit('update_game', game, to=room)
        emit('log', {'msg': f'⛓️ {player["name"]} سجين! باقي {player["jail_turns"]} دور'}, to=room)
        return

    steps = random.randint(1, 6)
    old_pos = player['pos']
    player['pos'] = (player['pos'] + steps) % 40
    
    # راتب اللفة (50$)
    if player['pos'] < old_pos:
        player['money'] += 50
    
    # دخول السجن (مربع 30)
    if player['pos'] == 30:
        player['pos'] = 10
        player['jail_turns'] = 3

    game['turn'] = (game['turn'] + 1) % len(game['players'])
    emit('dice_result', {'steps': steps, 'game': game, 'roller': player['name']}, to=room)

@socketio.on('buy_land')
def on_buy(data):
    room = data['room']
    game = rooms[room]
    player = next(p for p in game['players'] if p['name'] == data['name'])
    if player['money'] >= data['price']:
        player['money'] -= data['price']
        game['properties'][str(player['pos'])] = player['name']
        emit('update_game', game, to=room)

@socketio.on('update_money')
def on_money(data):
    room = data['room']
    player = next(p for p in rooms[room]['players'] if p['name'] == data['name'])
    player['money'] += data['amount']
    emit('update_game', rooms[room], to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

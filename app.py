import os, random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

# المجموعات اللونية لذي قار
COLOR_GROUPS = {
    'brown': [1, 3], 'lightblue': [6, 8, 9], 'pink': [11, 13, 14],
    'orange': [16, 18, 19], 'red': [21, 23, 24], 'yellow': [26, 27, 29],
    'green': [31, 32, 34], 'darkblue': [37, 39]
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def on_create(data):
    room = data['room']
    if room not in rooms:
        rooms[room] = {'players': [], 'turn': 0, 'properties': {}, 'houses': {}, 'offers': {}}
        join_room(room)

@socketio.on('join_game')
def on_join(data):
    room = data['room']
    if room in rooms:
        join_room(room)
        if any(p['name'] == data['name'] for p in rooms[room]['players']): return
        player = {
            'name': data['name'], 'money': 1500, 'pos': 0, 
            'id': request.sid, 'color': data['color'], 
            'jail_turns': 0, 'bankrupt': False, 'owned_props': []
        }
        rooms[room]['players'].append(player)
        emit('update_game', rooms[room], to=room)
        emit('join_success', {'success': True})

@socketio.on('roll_dice')
def on_roll(data):
    room = data['room']
    game = rooms[room]
    p = game['players'][game['turn']]
    
    if p['id'] != request.sid: return # ضمان الدور

    steps = random.randint(1, 6)
    old_pos = p['pos']
    p['pos'] = (p['pos'] + steps) % 40
    
    # راتب المرور
    if p['pos'] < old_pos: p['money'] += 200

    # السجن
    if p['pos'] == 30:
        p['pos'] = 10; p['jail_turns'] = 3

    # دفع الايجار
    pos_s = str(p['pos'])
    if pos_s in game['properties']:
        owner_name = game['properties'][pos_s]
        if owner_name != p['name']:
            rent = (int(pos_s) * 2) + 50 # معادلة إيجار
            p['money'] -= rent
            owner = next((pl for pl in game['players'] if pl['name'] == owner_name), None)
            if owner: owner['money'] += rent

    # نرسل "steps" و "roller" لتشغيل الأنيميشن في المتصفح
    emit('dice_result', {'steps': steps, 'game': game, 'roller': p['name']}, to=room)
    game['turn'] = (game['turn'] + 1) % len(game['players'])
    emit('update_game', game, to=room)

@socketio.on('buy_land')
def on_buy(data):
    room = data['room']
    game = rooms[room]
    p = next(pl for pl in game['players'] if pl['name'] == data['name'])
    if p['money'] >= data['price']:
        p['money'] -= data['price']
        game['properties'][str(data['pos'])] = p['name']
        p['owned_props'].append(int(data['pos']))
        emit('update_game', game, to=room)

@socketio.on('propose_trade')
def on_trade_offer(data):
    emit('trade_received', {'from': data['sender'], 'offer': data['offer'], 'target': data['target']}, to=data['room'])

@socketio.on('respond_trade')
def on_trade_response(data):
    room = data['room']; game = rooms[room]
    if data['accepted']:
        sender = next(p for p in game['players'] if p['name'] == data['from'])
        receiver = next(p for p in game['players'] if p['name'] == data['me'])
        off = data['offer']
        sender['money'] = sender['money'] - int(off['money_give']) + int(off['money_want'])
        receiver['money'] = receiver['money'] + int(off['money_give']) - int(off['money_want'])
        for pid in off['props_give']:
            game['properties'][str(pid)] = receiver['name']
            sender['owned_props'].remove(int(pid)); receiver['owned_props'].append(int(pid))
        for pid in off['props_want']:
            game['properties'][str(pid)] = sender['name']
            receiver['owned_props'].remove(int(pid)); sender['owned_props'].append(int(pid))
        emit('update_game', game, to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)

import os, random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

# تعريف مجموعات الألوان (Index للمناطق)
GROUPS = {
    'brown': [1, 3],
    'lightblue': [6, 8, 9],
    'pink': [11, 13, 14],
    'orange': [16, 18, 19],
    'red': [21, 23, 24],
    'yellow': [26, 27, 29],
    'green': [31, 32, 34],
    'blue': [37, 39]
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def on_create(data):
    room = data['room']
    if room not in rooms:
        rooms[room] = {'players': [], 'turn': 0, 'properties': {}, 'houses': {}, 'logs': []}
        join_room(room)
        emit('status', {'msg': 'تم تأسيس المملكة بنجاح سيدي'})

@socketio.on('join_game')
def on_join(data):
    room = data['room']
    if room in rooms:
        join_room(room)
        # التحقق من عدم تكرار اللاعب
        if any(p['name'] == data['name'] for p in rooms[room]['players']):
            return
            
        player_data = {
            'name': data['name'], 'money': 2000, 'pos': 0, 
            'id': request.sid, 'color': data['color'], 'jail_turns': 0, 'is_bankrupt': False
        }
        rooms[room]['players'].append(player_data)
        emit('update_game', rooms[room], to=room)
        emit('join_success', {'success': True})

@socketio.on('roll_dice')
def on_roll(data):
    room = data['room']
    game = rooms[room]
    player = game['players'][game['turn']]
    
    if player['is_bankrupt']: 
        next_turn(game, room)
        return

    # منطق السجن
    if player.get('jail_turns', 0) > 0:
        player['jail_turns'] -= 1
        emit('log', {'msg': f'⛓️ {player["name"]} مسجون! باقي {player["jail_turns"]}'}, to=room)
        next_turn(game, room)
        return

    steps = random.randint(1, 6)
    old_pos = player['pos']
    player['pos'] = (player['pos'] + steps) % 40
    
    # راتب الدورة
    if player['pos'] < old_pos:
        player['money'] += 200 # زيادة الراتب لـ 200 لتسريع اللعب
        emit('effect', {'type': 'money', 'val': '+200$'}, to=room)
    
    # الذهاب للسجن
    if player['pos'] == 30:
        player['pos'] = 10; player['jail_turns'] = 3
        emit('log', {'msg': f'👮 {player["name"]} إلى السجن!'}, to=room)

    # دفع الإيجار التلقائي
    pos_str = str(player['pos'])
    if pos_str in game['properties']:
        owner_name = game['properties'][pos_str]
        if owner_name != player['name']:
            # حساب الإيجار حسب التطوير
            rent = 50 * (game['houses'].get(pos_str, 0) + 1)
            # المحطات تضاعف الإيجار
            if player['pos'] in [5, 15, 25, 35]: rent = 100
            
            player['money'] -= rent
            # تحويل المال للمالك
            owner = next((p for p in game['players'] if p['name'] == owner_name), None)
            if owner: owner['money'] += rent
            
            emit('log', {'msg': f'💸 دفع {player["name"]} إيجار {rent}$ لـ {owner_name}'}, to=room)
            
            # التحقق من الإفلاس
            if player['money'] < 0:
                player['is_bankrupt'] = True
                emit('log', {'msg': f'💀 {player["name"]} أعلن إفلاسه!'}, to=room)

    next_turn(game, room)
    emit('dice_result', {'steps': steps, 'game': game, 'roller': player['name']}, to=room)

def next_turn(game, room):
    game['turn'] = (game['turn'] + 1) % len(game['players'])
    # تخطي المفلسين
    while game['players'][game['turn']]['is_bankrupt']:
        game['turn'] = (game['turn'] + 1) % len(game['players'])
    emit('update_game', game, to=room)

@socketio.on('buy_land')
def on_buy(data):
    room = data['room']
    game = rooms[room]
    player = next(p for p in game['players'] if p['name'] == data['name'])
    if player['money'] >= data['price']:
        player['money'] -= data['price']
        game['properties'][str(player['pos'])] = player['name']
        game['houses'][str(player['pos'])] = 0
        emit('update_game', game, to=room)

@socketio.on('upgrade_land')
def on_upgrade(data):
    room = data['room']
    game = rooms[room]
    player = next(p for p in game['players'] if p['name'] == data['name'])
    pos = str(data['pos'])
    
    cost = 150 # تكلفة التطوير
    if player['money'] >= cost and game['properties'].get(pos) == player['name']:
        player['money'] -= cost
        game['houses'][pos] = game['houses'].get(pos, 0) + 1
        emit('log', {'msg': f'🏗️ قام {player["name"]} بتطوير المنطقة!'}, to=room)
        emit('update_game', game, to=room)

@socketio.on('trade')
def on_trade(data):
    room = data['room']
    sender = next(p for p in rooms[room]['players'] if p['name'] == data['sender'])
    receiver = next(p for p in rooms[room]['players'] if p['name'] == data['receiver'])
    amount = int(data['amount'])
    
    if sender['money'] >= amount:
        sender['money'] -= amount
        receiver['money'] += amount
        emit('log', {'msg': f'🤝 {sender["name"]} حول {amount}$ لـ {receiver["name"]}'}, to=room)
        emit('update_game', rooms[room], to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

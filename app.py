import os, random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

# تعريف المجموعات اللونية لذي قار (Index من 0 الى 39)
# 1,3 (BROWN) | 6,8,9 (L-BLUE) | 11,13,14 (PINK) | 16,18,19 (ORANGE)
# 21,23,24 (RED) | 26,27,29 (YELLOW) | 31,32,34 (GREEN) | 37,39 (D-BLUE)
COLOR_GROUPS = {
    'brown': [1, 3],
    'lightblue': [6, 8, 9],
    'pink': [11, 13, 14],
    'orange': [16, 18, 19],
    'red': [21, 23, 24],
    'yellow': [26, 27, 29],
    'green': [31, 32, 34],
    'darkblue': [37, 39]
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
        emit('status', {'msg': 'تم إنشاء المملكة سيدي'})

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
    
    if p['bankrupt']: 
        pass_turn(game, room); return

    if p['jail_turns'] > 0:
        p['jail_turns'] -= 1
        emit('log', {'msg': f'⛓️ {p["name"]} في السجن..'}, to=room)
        pass_turn(game, room); return

    steps = random.randint(1, 6)
    old_pos = p['pos']
    p['pos'] = (p['pos'] + steps) % 40
    
    # راتب المرور
    if p['pos'] < old_pos:
        p['money'] += 200
        emit('effect', {'type': 'salary'}, to=room)

    # السجن
    if p['pos'] == 30:
        p['pos'] = 10; p['jail_turns'] = 3
        emit('log', {'msg': f'👮 {p["name"]} تم القبض عليه!'}, to=room)

    # دفع الايجار
    pos_s = str(p['pos'])
    if pos_s in game['properties']:
        owner_name = game['properties'][pos_s]
        if owner_name != p['name']:
            rent = calculate_rent(game, int(pos_s))
            p['money'] -= rent
            owner = next((pl for pl in game['players'] if pl['name'] == owner_name), None)
            if owner: owner['money'] += rent
            emit('log', {'msg': f'💸 دفع {p["name"]} إيجار {rent}$'}, to=room)

    emit('dice_result', {'steps': steps, 'game': game, 'roller': p['name']}, to=room)
    pass_turn(game, room)

def calculate_rent(game, pos):
    # حساب الايجار الاساسي + المنازل
    base_rent = pos * 2 # معادلة بسيطة للايجار
    if pos in [5,15,25,35]: base_rent = 100 # محطات
    if pos in [12, 28]: base_rent = 50 # كهرباء
    
    # التحقق من امتلاك المجموعة كاملة (Double Rent)
    # (يمكن تطوير هذا الجزء ليكون أكثر تعقيداً لاحقاً)
    return base_rent * (game['houses'].get(str(pos), 0) + 1)

def pass_turn(game, room):
    game['turn'] = (game['turn'] + 1) % len(game['players'])
    emit('update_game', game, to=room)

@socketio.on('buy_land')
def on_buy(data):
    room = data['room']
    game = rooms[room]
    p = next(pl for pl in game['players'] if pl['name'] == data['name'])
    if p['money'] >= data['price']:
        p['money'] -= data['price']
        game['properties'][str(p['pos'])] = p['name']
        p['owned_props'].append(int(p['pos']))
        emit('update_game', game, to=room)

# --- نظام المقايضة الجديد ---
@socketio.on('propose_trade')
def on_trade_offer(data):
    room = data['room']
    target_name = data['target']
    offer = data['offer'] # {money_give, props_give, money_want, props_want}
    
    # إرسال العرض للهدف
    emit('trade_received', {
        'from': data['sender'],
        'offer': offer
    }, to=room) # سيتم تصفيته في الكلاينت ليصل للشخص المعني فقط

@socketio.on('respond_trade')
def on_trade_response(data):
    room = data['room']
    game = rooms[room]
    
    if data['accepted']:
        # تنفيذ التبادل
        sender = next(p for p in game['players'] if p['name'] == data['from'])
        receiver = next(p for p in game['players'] if p['name'] == data['me'])
        offer = data['offer']
        
        # تحويل الأموال
        sender['money'] -= int(offer['money_give'])
        sender['money'] += int(offer['money_want'])
        receiver['money'] += int(offer['money_give'])
        receiver['money'] -= int(offer['money_want'])
        
        # تحويل الأملاك ( Sender Give -> Receiver )
        for pid in offer['props_give']:
            game['properties'][str(pid)] = receiver['name']
            sender['owned_props'].remove(int(pid))
            receiver['owned_props'].append(int(pid))
            
        # تحويل الأملاك ( Sender Want <- Receiver )
        for pid in offer['props_want']:
            game['properties'][str(pid)] = sender['name']
            receiver['owned_props'].remove(int(pid))
            sender['owned_props'].append(int(pid))
            
        emit('log', {'msg': f'🤝 تمت صفقة تجارية ضخمة بين {sender["name"]} و {receiver["name"]}!'}, to=room)
        emit('update_game', game, to=room)
    else:
        emit('log', {'msg': f'❌ تم رفض العرض التجاري من قبل {data["me"]}'}, to=room)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)

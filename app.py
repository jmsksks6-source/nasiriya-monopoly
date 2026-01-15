import os, random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

# بيانات اللوحة الكاملة (الأسعار، الإيجار، المجموعة)
# type: prop (ملك)، tax (ضريبة)، luck (حظ)، jail (سجن)، start (بداية)
BOARD_DATA = {
    0: {'type': 'start', 'name': 'البداية'},
    1: {'type': 'prop', 'name': 'سوق الشيوخ', 'price': 60, 'rent': 2, 'group': 'brown', 'cost_house': 50},
    2: {'type': 'luck', 'name': 'صندوق الحظ'},
    3: {'type': 'prop', 'name': 'العكيكة', 'price': 60, 'rent': 4, 'group': 'brown', 'cost_house': 50},
    4: {'type': 'tax', 'name': 'ضريبة الدخل', 'amount': 200},
    5: {'type': 'prop', 'name': 'كراج بغداد', 'price': 200, 'rent': 25, 'group': 'station'},
    6: {'type': 'prop', 'name': 'كرمة بني سعيد', 'price': 100, 'rent': 6, 'group': 'lightblue', 'cost_house': 50},
    7: {'type': 'luck', 'name': 'فرصة'},
    8: {'type': 'prop', 'name': 'الطار', 'price': 100, 'rent': 6, 'group': 'lightblue', 'cost_house': 50},
    9: {'type': 'prop', 'name': 'الفهود', 'price': 120, 'rent': 8, 'group': 'lightblue', 'cost_house': 50},
    10: {'type': 'jail', 'name': 'سجن'},
    11: {'type': 'prop', 'name': 'حي الفداء', 'price': 140, 'rent': 10, 'group': 'pink', 'cost_house': 100},
    12: {'type': 'prop', 'name': 'شركة الكهرباء', 'price': 150, 'rent': 0, 'group': 'utility'}, # Rent depends on dice
    13: {'type': 'prop', 'name': 'حي الشهداء', 'price': 140, 'rent': 10, 'group': 'pink', 'cost_house': 100},
    14: {'type': 'prop', 'name': 'حي الشموخ', 'price': 160, 'rent': 12, 'group': 'pink', 'cost_house': 100},
    15: {'type': 'prop', 'name': 'كراج البصرة', 'price': 200, 'rent': 25, 'group': 'station'},
    16: {'type': 'prop', 'name': 'حي سومر', 'price': 180, 'rent': 14, 'group': 'orange', 'cost_house': 100},
    17: {'type': 'luck', 'name': 'صندوق الحظ'},
    18: {'type': 'prop', 'name': 'شارع بغداد', 'price': 180, 'rent': 14, 'group': 'orange', 'cost_house': 100},
    19: {'type': 'prop', 'name': 'حي اريدو', 'price': 200, 'rent': 16, 'group': 'orange', 'cost_house': 100},
    20: {'type': 'parking', 'name': 'موقف مجاني'},
    21: {'type': 'prop', 'name': 'الحبوبي', 'price': 220, 'rent': 18, 'group': 'red', 'cost_house': 150},
    22: {'type': 'luck', 'name': 'فرصة'},
    23: {'type': 'prop', 'name': 'شارع النيل', 'price': 220, 'rent': 18, 'group': 'red', 'cost_house': 150},
    24: {'type': 'prop', 'name': 'المتنزه', 'price': 240, 'rent': 20, 'group': 'red', 'cost_house': 150},
    25: {'type': 'prop', 'name': 'محطة ناصرية', 'price': 200, 'rent': 25, 'group': 'station'},
    26: {'type': 'prop', 'name': 'مدينة أور', 'price': 260, 'rent': 22, 'group': 'yellow', 'cost_house': 150},
    27: {'type': 'prop', 'name': 'الزقورة', 'price': 260, 'rent': 22, 'group': 'yellow', 'cost_house': 150},
    28: {'type': 'prop', 'name': 'إسالة الماء', 'price': 150, 'rent': 0, 'group': 'utility'},
    29: {'type': 'prop', 'name': 'المتحف', 'price': 280, 'rent': 24, 'group': 'yellow', 'cost_house': 150},
    30: {'type': 'goto_jail', 'name': 'اذهب للسجن'},
    31: {'type': 'prop', 'name': 'الإدارة المحلية', 'price': 300, 'rent': 26, 'group': 'green', 'cost_house': 200},
    32: {'type': 'prop', 'name': 'إبراهيم الخليل', 'price': 300, 'rent': 26, 'group': 'green', 'cost_house': 200},
    33: {'type': 'luck', 'name': 'صندوق الحظ'},
    34: {'type': 'prop', 'name': 'حي المتنزه', 'price': 320, 'rent': 28, 'group': 'green', 'cost_house': 200},
    35: {'type': 'prop', 'name': 'القطار السريع', 'price': 200, 'rent': 25, 'group': 'station'},
    36: {'type': 'luck', 'name': 'فرصة'},
    37: {'type': 'prop', 'name': 'المنصورية', 'price': 350, 'rent': 35, 'group': 'darkblue', 'cost_house': 200},
    38: {'type': 'tax', 'name': 'ضريبة فاخرة', 'amount': 100},
    39: {'type': 'prop', 'name': 'الكورنيش', 'price': 400, 'rent': 50, 'group': 'darkblue', 'cost_house': 200}
}

# المجموعات للتحقق من "الاحتكار"
GROUPS = {
    'brown': [1, 3], 'lightblue': [6, 8, 9], 'pink': [11, 13, 14],
    'orange': [16, 18, 19], 'red': [21, 23, 24], 'yellow': [26, 27, 29],
    'green': [31, 32, 34], 'darkblue': [37, 39]
}

@app.route('/')
def index(): return render_template('index.html')

@socketio.on('create_room')
def on_create(data):
    room = data['room']
    if room not in rooms:
        rooms[room] = {'players': [], 'turn': 0, 'properties': {}, 'houses': {}} # houses: {'1': 2} (zone 1 has 2 houses)
        join_room(room)

@socketio.on('join_game')
def on_join(data):
    room = data['room']
    join_room(room)
    if not any(p['name'] == data['name'] for p in rooms[room]['players']):
        rooms[room]['players'].append({
            'name': data['name'], 'money': 1500, 'pos': 0, 'id': request.sid, 
            'color': data['color'], 'jail': 0
        })
    emit('update_game', rooms[room], to=room)
    emit('join_success', {'success': True})

# --- الصوت والويب آر تي سي (WebRTC Signaling) ---
@socketio.on('voice_signal')
def on_voice_signal(data):
    # تمرير بيانات الصوت (Offer, Answer, ICE Candidates) بين اللاعبين
    emit('voice_signal', data, to=data['room'], include_self=False)

@socketio.on('roll_dice')
def on_roll(data):
    room = data['room']; game = rooms[room]
    p = game['players'][game['turn']]
    if p['id'] != request.sid: return

    steps = random.randint(1, 6)
    p['pos'] = (p['pos'] + steps) % 40
    
    # التعامل مع المربع الحالي
    sq = BOARD_DATA.get(p['pos'], {})
    msg = ""
    
    if sq.get('type') == 'goto_jail':
        p['pos'] = 10; p['jail'] = 3
        msg = "👮 ذهب إلى السجن!"
    elif sq.get('type') == 'tax':
        p['money'] -= sq['amount']
        msg = f"💸 دفع ضريبة {sq['amount']}"
    elif sq.get('type') == 'prop':
        owner = game['properties'].get(str(p['pos']))
        if owner and owner != p['name']:
            rent = calculate_rent(game, p['pos'])
            p['money'] -= rent
            # بحث عن المالك وإعطائه المال
            for pl in game['players']:
                if pl['name'] == owner: pl['money'] += rent
            msg = f"📉 دفع إيجار {rent} لـ {owner}"

    emit('dice_result', {'steps': steps, 'game': game, 'roller': p['name'], 'msg': msg}, to=room)
    
    # تغيير الدور (إلا إذا كان هناك Double - للتسهيل سنغير الدور دائماً حالياً)
    game['turn'] = (game['turn'] + 1) % len(game['players'])
    emit('update_game', game, to=room)

def calculate_rent(game, pos):
    sq = BOARD_DATA[pos]
    houses = game['houses'].get(str(pos), 0)
    base_rent = sq['rent']
    
    # إذا كان يملك كل المجموعة تتضاعف الإيجارات (بدون منازل)
    owner = game['properties'][str(pos)]
    group = sq.get('group')
    if group in GROUPS:
        # هل يملك المالك كل عقارات هذه المجموعة؟
        group_indices = GROUPS[group]
        all_owned = all(game['properties'].get(str(i)) == owner for i in group_indices)
        if all_owned and houses == 0:
            return base_rent * 2
    
    # معادلة الإيجار مع المنازل (مثال مبسط)
    if houses > 0:
        return base_rent * (5 ** houses) # تزايد ضخم للإيجار
    return base_rent

@socketio.on('buy_prop')
def on_buy(data):
    room = data['room']; game = rooms[room]
    p = next(pl for pl in game['players'] if pl['name'] == data['name'])
    sq = BOARD_DATA[data['pos']]
    if p['money'] >= sq['price']:
        p['money'] -= sq['price']
        game['properties'][str(data['pos'])] = p['name']
        emit('update_game', game, to=room)
        emit('play_sound', {'sound': 'buy'}, to=room)

@socketio.on('build_house')
def on_build(data):
    room = data['room']; game = rooms[room]
    pos = data['pos']
    p = next(pl for pl in game['players'] if pl['name'] == data['name'])
    sq = BOARD_DATA[pos]
    
    # التحقق من أن اللاعب يملك كل المجموعة
    group = sq.get('group')
    if group and group in GROUPS:
        group_indices = GROUPS[group]
        if all(game['properties'].get(str(i)) == p['name'] for i in group_indices):
            # خصم السعر وبناء المنزل
            cost = sq.get('cost_house', 100)
            if p['money'] >= cost:
                p['money'] -= cost
                current_h = game['houses'].get(str(pos), 0)
                if current_h < 5: # الحد الأقصى 5 (فندق)
                    game['houses'][str(pos)] = current_h + 1
                    emit('update_game', game, to=room)
                    emit('play_sound', {'sound': 'build'}, to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)

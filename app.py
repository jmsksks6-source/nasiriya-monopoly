# أضف هذا المنطق داخل دالة on_roll في app.py سيدي
@socketio.on('roll_dice')
def on_roll(data):
    room = data['room']
    game = rooms[room]
    player = game['players'][game['turn']]
    
    # تحقق إذا كان اللاعب في السجن سيدي
    if player.get('jail_turns', 0) > 0:
        player['jail_turns'] -= 1
        emit('log', {'msg': f'⛓️ {player["name"]} لا يزال في السجن! باقي {player["jail_turns"]} أدوار'}, to=room)
        game['turn'] = (game['turn'] + 1) % len(game['players'])
        emit('update_game', game, to=room)
        return

    steps = random.randint(1, 6)
    old_pos = player['pos']
    player['pos'] = (player['pos'] + steps) % 40
    
    # منطق اللفة الكاملة (إضافة 50$ مكافأة سيدي)
    if player['pos'] < old_pos:
        player['money'] += 50 
        emit('log', {'msg': f'🎊 {player["name"]} أكمل دورة واستلم 50$'}, to=room)

    # إذا وقف على مربع "اذهب للسجن"
    if player['pos'] == 30:
        player['pos'] = 10 # موقعه في السجن
        player['jail_turns'] = 3
        emit('log', {'msg': f'🚔 {player["name"]} تم اعتقاله لمدة 3 أدوار!'}, to=room)

    game['turn'] = (game['turn'] + 1) % len(game['players'])
    emit('dice_result', {'steps': steps, 'game': game, 'roller': player['name']}, to=room)

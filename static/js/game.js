const socket = io();
let room = "nasiriya_room";
let name = prompt("ما اسمك يا بطل؟") || "لاعب";

socket.emit('join_room', {room: room, name: name});

document.getElementById('rollBtn').onclick = () => {
    socket.emit('roll_dice', {room: room, name: name});
};

socket.on('dice_result', (data) => {
    const log = document.getElementById('logBox');
    log.innerHTML += `<p>${data.name} رمى الزار ووقف على المربع ${data.position}</p>`;
});

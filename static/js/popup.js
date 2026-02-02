function showCard(title, text) {
    document.getElementById('cardTitle').innerText = title;
    document.getElementById('cardText').innerText = text;
    document.getElementById('cardPopup').style.display = 'flex';
}
document.getElementById('cardOk').onclick = () => {
    document.getElementById('cardPopup').style.display = 'none';
};

import os
from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return "<h1>تم تشغيل مونوبولي ذي قار بنجاح سيدي!</h1><p>السيرفر يعمل الآن للأبد.</p>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

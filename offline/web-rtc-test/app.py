from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("join")
def on_join(data):
    join_room(data["room"])

@socketio.on("signal")
def on_signal(data):
    emit("signal", data, room=data["room"], include_self=False)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
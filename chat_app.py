from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, close_room, send
# close_room - might be required if your're using dynamic number of rooms


# Initialize Flask-SocketIO
app = Flask(__name__)
app.config["SECRET_KEY"] = "adfd4-lkdf5-636lk-fglkj"  # Used for signing the session cookies
socketio = SocketIO(app)
ROOMS = ["General", "News", "Games"]


@app.route("/")
def load_web_page():
    return render_template("index.html", rooms=ROOMS)


# Testing function
def client_callback(json):
    print(f"received new info > {str(json)}")


@socketio.on("server_receive")
def connect_new_client(data):
    username = data["username"]
    msg = data["msg"]
    room = data["room"]
    send({"username": username, "msg": msg},  callback=client_callback, room=room)


@socketio.on("connect")
def connect():
    print(f">>>> connection info: {{namespace: {request.namespace}, sid: {request.sid} }}")


@socketio.on("disconnect")
def disconnect():
    print(f">>>> disconnect info: {{namespace: {request.namespace}, sid: {request.sid} }}")


@socketio.on("join")
def join(data):
    username = data["username"]
    room = data["room"]

    join_room(room)
    # Broadcast that new user has joined
    socketio.send({"msg": username + " has joined the " + room + " room."}, room=room)


@socketio.on("leave")
def leave(data):
    username = data["username"]
    room = data["room"]

    leave_room(room)
    # Broadcast that new user has joined
    socketio.send({"msg": username + " has left the " + room + " room."}, room=room)


if __name__ == '__main__':
  socketio.run(app, debug=True)

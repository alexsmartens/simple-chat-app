import os
import json
import redis
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, close_room
# close_room - might be required if your"re using dynamic number of rooms
import eventlet
eventlet.monkey_patch()


# Initialize the app
app = Flask(__name__)
app.config["SECRET_KEY"] = "adfd4-lkdf5-636lk-fglkj"  # Used for signing the session cookies
socketio = SocketIO(app)

REDIS_CHAN = "chat"
REDIS_URL = os.environ.get("REDIS_URL")
redis = redis.from_url(REDIS_URL, decode_responses=True)


CHAT_ROOM_NAMES = ["General", "News", "Games"]


class ChatBackend:
    def __init__(self):
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get("data")
            if message["type"] == "message":
                yield json.loads(data)

    @staticmethod
    def send(data):
        if "msg" in data and "room" in data:
            room = data["room"]
            del data["room"]
            socketio.send(data, room=room)
        else:
            print(f"Incorrect message format was read from redis: {data}. A correct message should have "
                            f"'room' and 'msg' keys")

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            eventlet.spawn(self.send, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        eventlet.spawn(self.run)


chat = ChatBackend()
chat.start()


@app.route("/")
def load_web_page():
    return render_template("index.html", rooms=CHAT_ROOM_NAMES)


@socketio.on("server_receive")
def server_receive(data):
    # Message sanity check
    if "room" in data and \
        "username" in data and \
        "msg" in data:

        redis.publish(REDIS_CHAN, json.dumps({
            "room": data["room"],
            "username": data["username"],
            # "sid": request.sid,
            "msg": data["msg"],
        }))
    else:
        print(f"Incorrect message format was received form the client: {data}. A correct message should have "
                        f"'room', 'username' and 'msg' keys")


@socketio.on("connect")
def connect():
    print(f"connect info: {{namespace: {request.namespace}, sid: {request.sid} }}")


@socketio.on("disconnect")
def disconnect():
    print(f"disconnect info: {{namespace: {request.namespace}, sid: {request.sid} }}")


@socketio.on("join")
def join(data):
    # Message sanity check
    if "room" in data and \
        "username" in data:

        join_room(data["room"])
        # Broadcast that new user has joined
        redis.publish(REDIS_CHAN, json.dumps({
            "room": data["room"],
            # "sid": request.sid,
            "msg": data["username"] + " has joined the " + data["room"] + " room.",
        }))
    else:
        print(f"Incorrect message format was received form the client: {data}. A correct message should have "
                        f"'room' and 'username' keys")


@socketio.on("leave")
def leave(data):
    # Message sanity check
    if "room" in data and \
        "username" in data:

        leave_room(data["room"])
        # Broadcast that new user has joined
        redis.publish(REDIS_CHAN, json.dumps({
            "room": data["room"],
            # "sid": request.sid,
            "msg": data["username"] + " has left the " + data["room"] + " room.",
        }))
    else:
        print(f"Incorrect message format was received form the client: {data}. A correct message should have "
                        f"'room' and 'username' keys")


if __name__ == "__main__":
  socketio.run(app, debug=True)

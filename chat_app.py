# Recommended by Flask-SocketIO: https://flask-socketio.readthedocs.io/en/latest/#using-nginx-as-a-websocket-reverse-proxy
import eventlet
eventlet.monkey_patch()

import os
import json
import redis
import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, close_room
# close_room - might be required if your"re using dynamic number of rooms


# Initialize the app
app = Flask(__name__)
app.config["SECRET_KEY"] = "adfd4-lkdf5-636lk-fglkj"  # Used for signing the session cookies
# Configure logger
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)
# Add Flask-SocketIO to the Flask application
socketio = SocketIO(app)
# Configure redis
REDIS_CHAN = "chat"
REDIS_URL = os.environ.get("REDIS_URL")
redis = redis.from_url(REDIS_URL, decode_responses=True)

CHAT_ROOM_NAMES = ["General", "News", "Games"]


class RegisteredUserSessionTracker(dict):
    def __setitem__(self, session_id, user_info):
        eventlet.spawn(self._publish, "joined", user_info)
        super().__setitem__(session_id, user_info)


    def __delitem__(self, session_id):
        eventlet.spawn(self._publish, "left", self.get(session_id).copy())
        super().__delitem__(session_id)


    @staticmethod
    def _publish(action_str, user_info):
        # Broadcast that the new user has joined/left the group
        redis.publish(REDIS_CHAN, json.dumps({
            "room": user_info["room"],
            "msg": f"{user_info['username']} has {action_str} the {user_info['room']} room.",
        }))


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
            app.logger.warning(f"Incorrect message format was read from redis: {data}. A correct message should have "
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
user_tracker = RegisteredUserSessionTracker()


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
        app.logger.warning(f"Incorrect message format was received form the client: {data}. A correct message should "
                           f"have 'room', 'username' and 'msg' keys")


@socketio.on("connect")
def connect():
    app.logger.info(f"connect info: {{namespace: {request.namespace}, sid: {request.sid} }}")


@socketio.on("disconnect")
def disconnect():
    # User automatically lives the group on disconnection, but we still have to remove his/her registration if we want
    # to track user sessions
    # Remove user registration if the user is registered
    if request.sid in user_tracker:
        del user_tracker[request.sid]
    app.logger.info(f"disconnect info: {{namespace: {request.namespace}, sid: {request.sid} }}")


@socketio.on("join")
def join(data):
    # Message sanity check
    if "room" in data and \
        "username" in data:

        # Add the new user to the specified room
        join_room(data["room"])
        # Register the new user
        user_tracker[request.sid] = {"username":  data["username"], "room": data["room"]}
    else:
        app.logger.warning(f"Incorrect message format was received form the client: {data}. A correct message should "
                           f"have 'room' and 'username' keys")


@socketio.on("leave")
def leave(data):
    # Message sanity check
    if "room" in data and \
        "username" in data:

        # Remove the user from the specified room
        leave_room(data["room"])
        # Remove user registration
        del user_tracker[request.sid]
    else:
        app.logger.warning(f"Incorrect message format was received form the client: {data}. A correct message should "
                           f"have 'room' and 'username' keys")


if __name__ == "__main__":
    socketio.run(app, debug=True)

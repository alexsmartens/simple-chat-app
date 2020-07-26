import os
import socket
from flask import Flask, request
from service.server import ChatRoomServer, QUIT

chat_room_server = None

app = Flask(__name__)


@app.route("/")
def launch_chat_room():
    global chat_room_server
    # Server instance info
    HOST = socket.gethostname()
    # Local host ip
    # IP = socket.gethostbyname(HOST)
    PORT = 8081

    if chat_room_server is None:
        chat_room_server = ChatRoomServer()
        chat_room_server.start()

    return \
        f"<body> \
            <div> Running the chat room instance at {HOST}:{PORT}</div> \
            <div> Press <a href='{request.base_url}terminate'>terminate</a> to terminate the room thread </div> \
        </body>"


@app.route("/terminate")
def terminate_chat_room():
    global chat_room_server
    # Server instance info
    HOST = socket.gethostname()
    PORT = 8081

    if chat_room_server is not None:
        chat_room_server.quit_server()
        chat_room_server = None

    return \
        f"<body> \
            <div> Terminated the chat room at {HOST}:{PORT}</div> \
        </body>"

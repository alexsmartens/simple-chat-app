from flask import Flask, request
from service.server import ChatRoomServer, QUIT

chat_room_server = None

app = Flask(__name__)


@app.route("/")
def launch_chat_room():
    global chat_room_server

    if chat_room_server is None:
        chat_room_server = ChatRoomServer()
        chat_room_server.start()

    # Server info
    host = chat_room_server.host
    ip = chat_room_server.ip
    port = chat_room_server.port

    return \
        f"<body> \
            <div> Running the chat room instance  @ {ip}:{port} ({host}) </div> \
            <div> Press <a href='{request.base_url}terminate'>terminate</a> to terminate the room thread </div> \
        </body>"


@app.route("/terminate")
def terminate_chat_room():
    global chat_room_server

    if chat_room_server is not None:
        # Server info
        host = chat_room_server.host
        ip = chat_room_server.ip
        port = chat_room_server.port
        # Terminate server
        chat_room_server.quit_server()
        chat_room_server = None
        return \
            f"<body> \
                <div> Terminated the chat room @ {ip}:{port} ({host}) </div> \
            </body>"

    else:
        return \
            f"<body> \
                <div> No chat room running, nothing to terminate </div> \
            </body>"

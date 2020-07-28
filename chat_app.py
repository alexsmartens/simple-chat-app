from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "adfd4-lkdf5-636lk-fglkj"
socketio = SocketIO(app)


@app.route("/")
def load_web_page():
    return render_template("./index.html")


def client_callback(json):
    print(f"received new info > {str(json)}")


@socketio.on("server_receive")
def connect_new_client(json):
    print("new_message: " + str(json))
    # Broadcast a message
    socketio.emit("client_receive", json, callback=client_callback)


if __name__ == '__main__':
  socketio.run(app, debug=True)

import socket
import select
import sys
from threading import Thread

# *** Might be useful later
# 11.11. Passing a Socket File Descriptor Between Processes -from python cookbook
# ***

# Config
# Local host name
HOST = socket.gethostname()
# Local host ip
IP = socket.gethostbyname(HOST)
PORT = 8081
# Maximum number of connections open simultaneously by the server
CONNECTION_LIM = 100
# Maximum buffer size for receiving data from the socket, bytes
BUFSIZE = 1024


class MessengerClient(Thread):
    def __init__(self, chat_participants, client_socket, client_ip):
        self.chat_participants = chat_participants
        self.socket = client_socket
        self.ip = client_ip
        super().__init__()

    def run(self):
        while True:
            try:
                # recv blocks execution until it receives a message
                msg = self.socket.recv(BUFSIZE).decode("utf8")
            except OSError:
                # Possibly client has left the chat
                break

    def broadcast(self):
        pass


if __name__ == "__main__":
    # AF_INET - iPv4 (Internet address family)
    # SOCK_STREAM - TCP (socket type)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set up various socket options
    # SOL_SOCKET - socket layer itself, used to manipulate the socket-level options
    # SO_REUSEADDR - whether bind should permit reuse of local socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the server socket to the local IP at the specified port
    server_socket.bind((IP, PORT))

    # Listen to maximum of connection_lim active connections
    server_socket.listen(CONNECTION_LIM)

    chat_participants = {}
    # Launch sever
    while True:
        client_socket, client_ip = server_socket.accept()
        chat_participants[client_socket] = client_ip
        print(f"Client {client_ip} connected to the server")
        messenger_client = MessengerClient(chat_participants, client_socket, client_ip)
        messenger_client.start()

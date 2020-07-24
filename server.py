import socket
import select
import sys
from threading import Thread

# *** Might be useful later
# 11.11. Passing a Socket File Descriptor Between Processes -from python cookbook
# ***

# Config
# Maximum buffer size for receiving data from the socket, bytes
BUFSIZE = 1024
# Local host name
HOST = socket.gethostname()
# Local host ip
IP = socket.gethostbyname(HOST)
PORT = 8081
# Maximum number of connections open simultaneously by the server
CONNECTION_LIM = 100
# Quit chat message
QUIT = "{q}"

class ChatRoomServer(Thread):
    def __init__(self, ip=IP, port=PORT, connection_lim=CONNECTION_LIM, name="SERVER"):
        super().__init__()
        self.ip = ip
        self.port = port
        self.connection_lim = connection_lim
        self.socket = None
        self.name = name
        self._init_socket()
        # Dictionary of MessengerClient treads by their name {name: thread}
        self.participants = {}
        # Dictionary of MessengerClient treads by their socket {socket: thread}. These clients do not participate in the
        # chat yet (until they get a name)
        self.noname_participants = {}


    def _init_socket(self):
        try:
            # AF_INET - iPv4 (Internet address family)
            # SOCK_STREAM - TCP (socket type)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Set up various socket options
            # SOL_SOCKET - socket layer itself, used to manipulate the socket-level options
            # SO_REUSEADDR - whether bind should permit reuse of local socket
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind the server socket to the local IP at the specified port
            self.socket.bind((self.ip, self.port))
            # Listen to maximum of connection_lim active connections
            self.socket.listen(self.connection_lim)
        except Exception:
            # Chat room cannot be created on this
            raise RuntimeError("> Problem with socket initialization")

    def run(self):
        print(f"> Your chat room [{self.name}] is up and running @ {self.ip}:{self.port}...\nType '{QUIT}' if you want to quit.")
        try:
            # Accept new connections to the room
            while True:
                client_socket, client_ip = self.socket.accept()
                print(f"> Client {client_ip} connected to the server")
                messenger_client = MessengerClient(client_socket, client_ip, self)
                self.noname_participants[client_socket] = messenger_client
                messenger_client.start()
        except socket.error:
            print("> Closed server socket")

    def broadcast(self, sender_name, msg):
        for client_name, client_thread in self.participants.items():
            client_thread.socket.send(bytes(f"<{sender_name}> {msg}", "utf8"))

    def assign_client_name(self, messenger_client, name):
        if name is None:
            print(f"> Error: {messenger_client.socket} tried to assign a None name")
            return None
        else:
            messenger_client.name = name
            del self.noname_participants[messenger_client.socket]
            self.participants[messenger_client.name] = messenger_client
            messenger_client.socket.send(bytes(f"*** Happy chatting {messenger_client.name} ***\nType '{QUIT}' if you want to quit.", "utf8"))
            return messenger_client.name

    def quit_client(self, messenger_client):
        messenger_client.socket.close()
        if messenger_client.name is None:
            del self.noname_participants[messenger_client.socket]
        else:
            del self.participants[messenger_client.name]

    def quit_server(self):
        self.broadcast(self.name, "Chat room is about to be terminated...")
        # Cleaning up
        messenger_clients = list(self.participants.values()) + list(self.noname_participants.values())
        for messenger_client in messenger_clients:
            self.quit_client(messenger_client)
        self.socket.close()


class MessengerClient(Thread):
    def __init__(self, client_socket, client_ip, chat_room_server):
        super().__init__()
        self.socket = client_socket
        self.ip = client_ip
        self.name = None
        self.chat_room_server = chat_room_server

    def run(self):
        msg2server = self.set_client()
        while msg2server:
            msg2server = self.receive_msg()
            if msg2server is None:
                self.chat_room_server(self.name, msg2server)

    def receive_msg(self):
        msg2server = None
        try:
            # recv blocks execution until it receives a message
            msg2server = self.socket.recv(BUFSIZE).decode("utf8")
            print(self.name)
            print(self.name is None)
            print(self.name)
            print(f"> > {self.ip if self.name is None else self.name}: {msg2server}")
            if msg2server == QUIT:
                self.chat_room_server(self)
                msg2server = None
        except OSError:
            # Possibly client has left the chat
            self.chat_room_server(self)
        finally:
            return msg2server

    def set_client(self):
        # Pick a name
        self.socket.send(bytes("*** Welcome to my simple chat room ***\nType your name and press enter:", "utf8"))
        name = self.receive_msg()
        while (name is None) or \
              (name in self.chat_room_server.participants) or \
              (name == self.chat_room_server.name):
            self.socket.send(bytes("*This name already exists, type a different name and press enter:", "utf8"))
            name = self.receive_msg()

        # Set up the player
        if name:
            self.chat_room_server.assign_client_name(self, name)
        return name


if __name__ == "__main__":
    chat_room_server = ChatRoomServer()
    chat_room_server.start()

    # Server command terminal
    is_run_terminal = True
    while is_run_terminal:
        server_command = input()
        print(f"[{chat_room_server.name}] terminal command: {server_command}")
        if server_command == QUIT:
            chat_room_server.quit_server()
            del chat_room_server
            is_run_terminal = False

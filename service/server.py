import socket
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
        self.is_running = False
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
            self.is_running = True
        except Exception as err:
            # Chat room cannot be created on this
            raise RuntimeError(f"> Problem with socket initialization: {err.strerror}")

    def run(self):
        print(f"> Your chat room [{self.name}] is up and running @ {self.ip}:{self.port}...\nType '{QUIT}' if you want to quit.")
        try:
            # Accept new connections to the room
            while True:
                client_socket, client_ip = self.socket.accept()
                print(f"> Client {client_socket} connected to the server")
                messenger_client = MessengerClient(client_socket, client_ip, self)
                self.noname_participants[client_socket] = messenger_client
                messenger_client.start()
        except ConnectionAbortedError:
            print("> Closed server socket")

    def broadcast(self, sender_name, msg):
        for client_name, client_thread in self.participants.items():
            client_thread.socket.send(bytes(f"<{sender_name}> {msg}", "utf8"))

    def assign_client_name(self, messenger_client, name):
        if len(name) == 0 or type(name) is not str:
            print(f"> Error: {messenger_client.socket} tried to assign a None name")
            return ""
        else:
            messenger_client.name = name
            self.broadcast(self.name, f"{messenger_client.name} has joined the chat room")
            del self.noname_participants[messenger_client.socket]
            self.participants[messenger_client.name] = messenger_client
            messenger_client.socket.send(bytes(f"*** Happy chatting {messenger_client.name} ***\nType '{QUIT}' if you want to quit.", "utf8"))
            return messenger_client.name

    def quit_client(self, messenger_client):
        client_name = messenger_client.name
        messenger_client.socket.close()
        # Clean up the client's object
        if len(messenger_client.name):
            del self.participants[messenger_client.name]
        else:
            del self.noname_participants[messenger_client.socket]
        # Broadcast to others that the participant has left if the server is running. Otherwise, the server is
        # closing all the connections and no broadcasting needed
        if self.is_running and len(client_name):
            self.broadcast(self.name, f"{messenger_client.name} has left the chat room")
            del client_name

    def quit_server(self):
        self.broadcast(self.name, "Chat room is about to be terminated...")
        self.is_running = False
        self.socket.close()
        # Cleaning up
        messenger_clients = list(self.participants.values()) + list(self.noname_participants.values())
        for messenger_client in messenger_clients:
            # Clients quit themselves on socket closed
            messenger_client.socket.close()


class MessengerClient(Thread):
    def __init__(self, client_socket, client_ip, chat_room_server):
        super().__init__()
        self.socket = client_socket
        self.ip = client_ip
        self.name = ""
        self.chat_room_server = chat_room_server

    def run(self):
        msg2server = self.get_client_name()
        # Set up the player
        if len(msg2server) != 0 and msg2server != QUIT:
            self.chat_room_server.assign_client_name(self, msg2server)

        while len(msg2server) != 0 and msg2server != QUIT:
            msg2server = self.receive_msg()
            if len(msg2server) != 0 and msg2server != QUIT:
                self.chat_room_server.broadcast(self.name, msg2server)
        self.chat_room_server.quit_client(self)

    def receive_msg(self):
        try:
            # recv blocks execution until it receives a message
            msg2server = self.socket.recv(BUFSIZE).decode("utf8")
            print(f"> <{self.name if len(self.name) else self.ip}> {msg2server}")
        except OSError:
            # Possibly client has left the chat
            msg2server = ""
        finally:
            return msg2server

    def get_client_name(self):
        # Pick a name
        self.socket.send(bytes("*** Welcome to my simple chat room ***\nType your name and press enter:", "utf8"))
        name = self.receive_msg()
        while (name in self.chat_room_server.participants) or \
              (name == self.chat_room_server.name):
            self.socket.send(bytes("*This name already exists, type a different name and press enter:", "utf8"))
            name = self.receive_msg()
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

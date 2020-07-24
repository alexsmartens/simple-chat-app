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
# Quit chat message
QUIT = "{quit}"


class MessengerClient(Thread):
    def __init__(self, client_socket, client_ip, noname_participants_ctrl, chat_participants):
        self.socket = client_socket
        self.ip = client_ip
        self.name = None

        self.noname_participants_ctrl = noname_participants_ctrl
        self.noname_participants_ctrl[self.socket] = self
        self.chat_participants = chat_participants
        super().__init__()

    def run(self):
        msg2server = self.set_client()
        while msg2server:
            msg2server = self.receive_msg()
            if msg2server:
                self.broadcast(msg2server)

    def receive_msg(self):
        msg2server = None
        try:
            # recv blocks execution until it receives a message
            msg2server = self.socket.recv(BUFSIZE).decode("utf8")
            print(f"{self.name if self.name else self.ip}: {msg2server}")
            if msg2server == QUIT:
                self.quit()
                msg2server = None
        except OSError:
            # Possibly client has left the chat
            self.quit()
        finally:
            return msg2server

    def set_client(self):
        # Pick a name
        self.socket.send(bytes("*** Welcome to my simple chat room ***\nType your name and press enter:", "utf8"))
        name = self.receive_msg(self)
        while name is not None and name in chat_participants:
            self.socket.send(bytes("*This name already exists, type a different name and press enter:", "utf8"))
            name = self.receive_msg(self)

        # Set up the player
        if name:
            del self.noname_participants_ctrl[self.socket]
            self.name = name
            self.chat_participants[self.name] = self
            self.socket.send(bytes(f"*** Happy chatting {self.name} ***\nType '{QUIT}' if you want to quit.", "utf8"))
        return name

    def broadcast(self, msg2clients):
        for client_name, client_thread in self.chat_participants.items():
            client_thread.socket.send(bytes(f"<{self.name}> {msg2clients}", "utf8"))

    def quit(self):
        self.socket.close()
        del self.chat_participants[self.name]


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

    # Holding chat communication threads with each participant, who has a name {name: thread}
    chat_participants = {}
    # Holding chat communication threads with each perspective participant, who does not have a name yet
    # {socket: thread}. These clients do not participate in the chat yet
    noname_participants_ctrl = {}
    # Launch chat sever
    while True:
        client_socket, client_ip = server_socket.accept()
        print(f"Client {client_ip} connected to the server")
        messenger_client = MessengerClient(client_socket, client_ip, noname_participants_ctrl, chat_participants)
        messenger_client.start()

    # Cleaning up
    # client_names =
    # for client_name, client_thread in self.chat_participants.items():
    #     client_thread.socket.send(bytes(f"<{self.name}> {msg2clients}", "utf8"))

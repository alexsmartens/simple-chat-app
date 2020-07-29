import socket
import sys
import select
from server import BUFSIZE

if len(sys.argv) != 2 or len(sys.argv[1].split(':')) != 2:
    print("Correct usage: script, IP:PORT")
    exit()

try:
    ip, port = sys.argv[1].split(':')
    port = int(port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((ip, port))

    socket_list = [sys.stdin, server_socket]
    is_open_socket = True
    while is_open_socket:
        # select() examines the I/O descriptor sets to see if some of their descriptors are ready for reading, writing, or
        # have an exceptional condition pending, respectively.
        read_sockets, write_socket, error_socket = select.select(socket_list, [], [])
        for read_socket in read_sockets:
            if read_socket == server_socket:
                msg = read_socket.recv(BUFSIZE).decode("utf8")
                if len(msg):
                    print(msg)
                else:
                    is_open_socket = False
                    print("[info]: server closed connection, exiting ...")
            else:
                msg = sys.stdin.readline()[:-1]
                server_socket.send(bytes(msg, "utf8"))
    server_socket.close()
except (ConnectionRefusedError, OSError) as err:
    print(f"[{ip}:{port}] Error: {err.strerror} (possible cause: server is not running or incorrect server info provided)")
except ValueError as err:
    print(f"[{ip}:{port}] Error: {err.args[0]} (possible cause: incorrect server info provided)")

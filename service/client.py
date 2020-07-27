import socket
import sys
import select
from server import BUFSIZE

if len(sys.argv) != 3:
    print("Correct usage: script, IP address, port number")
    exit()

try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ip = str(sys.argv[1])
    port = int(sys.argv[2])

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
    print(f"[{ip}:{port}]: {err.strerror}")

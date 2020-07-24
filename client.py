import socket
import sys
import select


if len(sys.argv) != 3:
    print("Correct usage: script, IP address, port number")
    exit()

# Config
# Maximum buffer size for receiving data from the socket, bytes
BUFSIZE = 1024
try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ip = str(sys.argv[1])
    port = int(sys.argv[2])

    server_socket.connect((ip, port))
    socket_list = [sys.stdin, server_socket]
    is_run_terminal = True
    while True:
        # select() examines the I/O descriptor sets to see if some of their descriptors are ready for reading, writing, or
        # have an exceptional condition pending, respectively.
        read_sockets, write_socket, error_socket = select.select(socket_list, [], [])
        for read_socket in read_sockets:
            if read_socket == server_socket:
                msg = read_socket.recv(BUFSIZE)
                print(msg)
            else:
                msg = sys.stdin.readline()
                server_socket.send(bytes(msg, "utf8"))
    server_socket.close()
except ConnectionRefusedError:
    print(f"[{ip}:{port}]: connection refused (possible reason: server is not running)")

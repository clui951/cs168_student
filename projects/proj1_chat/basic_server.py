import socket
import sys

port_arg = sys.argv[1]

server_socket = socket.socket()
server_socket.bind(("0.0.0.0", int(port_arg)))
server_socket.listen(5)
(new_sock, address) = server_socket.accept()

print(new_sock.recv(1024))

server_socket.close()
new_sock.close()
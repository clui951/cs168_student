import socket
import sys
from utils import *

ip_arg = sys.argv[1]
port_arg = sys.argv[2]

client_socket = socket.socket()
client_socket.connect((ip_arg, int(port_arg)))
data = raw_input('--> ')
client_socket.send(data)

client_socket.close()
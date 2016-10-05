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


class BasicClient(object):

    def __init__(self, address, port):
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()

    def send(self, message):
        self.socket.connect((self.address, self.port))
        self.socket.send(message)

args = sys.argv
if len(args) != 3:
    print "Please supply a server address and port."
    sys.exit()
client = BasicClient(args[1], args[2])
msg = raw_input()
client.send(msg)


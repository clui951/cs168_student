import socket
import sys
import select

import utils

if(len(sys.argv) < 3) :
    print 'Usage : python chat_client.py hostname port'
    sys.exit()

user_name = sys.argv[1]
client_host = sys.argv[2]
client_port = sys.argv[3]

client_socket = socket.socket()
try:
    client_socket.connect((client_host, int(client_port)))
except:
    print utils.CLIENT_CANNOT_CONNECT.format( client_host, client_port)
    sys.exit()

# send username
client_socket.send(user_name.ljust(utils.MESSAGE_LENGTH))

sys.stdout.write('[Me] '); sys.stdout.flush()

msg_buffer = ""

while 1:
    socket_list = [sys.stdin, client_socket]    

    read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])

    # list of readable sockets
    for sock in read_sockets:
        if sock == client_socket:
            # incoming msg from remote server, client_socket
            data = sock.recv(utils.MESSAGE_LENGTH)
            if not data:
                sys.stdout.write(utils.CLIENT_WIPE_ME)
                sys.stdout.write("\r")
                print utils.CLIENT_SERVER_DISCONNECTED.format( client_host, client_port)
                sys.exit()
            else:
                # print data
                msg_buffer += data
                if len(msg_buffer) >= utils.MESSAGE_LENGTH:
                    # full msg received
                    msg = msg_buffer[:utils.MESSAGE_LENGTH].rstrip()
                    msg_buffer = msg_buffer[utils.MESSAGE_LENGTH:]
                    sys.stdout.write(utils.CLIENT_WIPE_ME)
                    sys.stdout.write("\r{0}\n".format(msg))
                    sys.stdout.write( utils.CLIENT_MESSAGE_PREFIX ); sys.stdout.flush()
                
        else:
            # user entered input
            msg = sys.stdin.readline()
            data = msg.ljust(utils.MESSAGE_LENGTH)
            client_socket.send(data)
            sys.stdout.write( utils.CLIENT_MESSAGE_PREFIX ); sys.stdout.flush() 





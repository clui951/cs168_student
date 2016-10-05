# list of channels (including non channel) and username currently in them
# list of ports/connections, hash username to port/connections to iterate through
# each port/connection has a buffer associated

import sys
import socket
import select
import utils


server_port = sys.argv[1]



CHANNEL_TO_SOCKETS = {} 		# { channel_name : [sock1, sock2, ...], ... }
SOCKET_TO_NAME_BUFFER = {}


def chat_server():
	server_socket = socket.socket()
	server_socket.bind(("0.0.0.0", int(server_port)))
	server_socket.listen(5)

	CHANNEL_TO_SOCKETS[":==default"] = [server_socket]

	while 1:
		for channel_name, socket_list in CHANNEL_TO_SOCKETS.items():
			ready_to_read,ready_to_write,in_error = select.select(socket_list,[],[], .01)

			for sock in ready_to_read:
				# check for new connection request
				if sock == server_socket and channel_name == ":==default" :
					sockfd, addr = server_socket.accept()
					CHANNEL_TO_SOCKETS[":==default"] += [sockfd]
					SOCKET_TO_NAME_BUFFER[sockfd] = [":==default", ""]


				# message from client, not a new connection
				else:

					# receive data from socket
					data = sock.recv(200)
					if data:
						# something in socket; add to buffer
						SOCKET_TO_NAME_BUFFER[sock][1] += data
						if len(SOCKET_TO_NAME_BUFFER[sock][1]) >= 200:
							# full msg received
							msg = SOCKET_TO_NAME_BUFFER[sock][1][:200].rstrip()
							SOCKET_TO_NAME_BUFFER[sock][1] = SOCKET_TO_NAME_BUFFER[sock][1][200:]

							if SOCKET_TO_NAME_BUFFER[sock][0] == ":==default":
								# first msg, update the username
								SOCKET_TO_NAME_BUFFER[sock][0] = msg
							else:
								if msg.startswith("/"):
									# command
									if msg == "/list":
										# return channels list
										response = ""
										for channel in CHANNEL_TO_SOCKETS:
											if channel != ":==default":
												response += channel + "\n"
										if response != "":
											# channels exist
											sock.send(response.ljust(utils.MESSAGE_LENGTH)) 

									elif msg.startswith("/create"):
										split_msg = msg.split(" ")
										if len(split_msg) != 2:
											sock.send(utils.SERVER_CREATE_REQUIRES_ARGUMENT.ljust(utils.MESSAGE_LENGTH))
										else:
											# create the room if doesnt exist
											new_channel = split_msg[1]
											if new_channel not in CHANNEL_TO_SOCKETS:
												CHANNEL_TO_SOCKETS[new_channel] = []

												# change to new_channel
												CHANNEL_TO_SOCKETS[new_channel] += [sock]
												CHANNEL_TO_SOCKETS[channel_name].remove(sock)
												# announce leaving of channel_name
												leaving_msg = utils.SERVER_CLIENT_LEFT_CHANNEL.format(SOCKET_TO_NAME_BUFFER[sock][0])
												broadcast_unpadded_msg(channel_name, leaving_msg, sock)

											else:
												sock.send(utils.SERVER_CHANNEL_EXISTS.format(new_channel).ljust(utils.MESSAGE_LENGTH))

									elif msg.startswith("/join"):
										# do join stuff
										split_msg = msg.split(" ")
										if len(split_msg) != 2:
											sock.send(utils.SERVER_JOIN_REQUIRES_ARGUMENT.ljust(utils.MESSAGE_LENGTH))
										else:
											# join room if possible
											join_channel = split_msg[1]
											if join_channel in CHANNEL_TO_SOCKETS:
												# change to join_channel
												CHANNEL_TO_SOCKETS[join_channel] += [sock]
												CHANNEL_TO_SOCKETS[channel_name].remove(sock)
												# announce arrival to join_channel and leaving of channel_name
												leaving_msg = utils.SERVER_CLIENT_LEFT_CHANNEL.format(SOCKET_TO_NAME_BUFFER[sock][0])
												broadcast_unpadded_msg(channel_name, leaving_msg, sock)
												arrival_msg = utils.SERVER_CLIENT_JOINED_CHANNEL.format(SOCKET_TO_NAME_BUFFER[sock][0])
												broadcast_unpadded_msg(join_channel, arrival_msg, sock)

											else:
												sock.send(utils.SERVER_NO_CHANNEL_EXISTS.format(join_channel).ljust(utils.MESSAGE_LENGTH))

									# elif msg == "/debug":
										# print(CHANNEL_TO_SOCKETS)

									else:
										# not a valid command
										sock.send(utils.SERVER_INVALID_CONTROL_MESSAGE.format(msg).ljust(utils.MESSAGE_LENGTH))



								else:
									# regular msg received
									if channel_name != ":==default":
										username = SOCKET_TO_NAME_BUFFER[sock][0]
										data = "[" + username + "] " + msg
										broadcast_unpadded_msg(channel_name, data, sock)
									else:
										# need to join a channel before sending message
										sock.send(utils.SERVER_CLIENT_NOT_IN_CHANNEL.ljust(utils.MESSAGE_LENGTH))


					else:
						# broadcast and remove broken socket
						msg = utils.SERVER_CLIENT_LEFT_CHANNEL.format(SOCKET_TO_NAME_BUFFER[sock][0])
						broadcast_unpadded_msg(channel_name, msg, sock)

						socket_list.remove(sock)
						CHANNEL_TO_SOCKETS[channel_name] = socket_list
						SOCKET_TO_NAME_BUFFER.pop(sock)


def broadcast_unpadded_msg(channel_name, msg, curr_sock):
	if channel_name != ":==default":
		for sock in CHANNEL_TO_SOCKETS[channel_name]:
			if sock != curr_sock:
				sock.send(msg.ljust(utils.MESSAGE_LENGTH))



sys.exit(chat_server())

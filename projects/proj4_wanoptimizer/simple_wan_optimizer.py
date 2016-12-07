import wan_optimizer
from utils import *
from tcp_packet import *

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into fixed-size blocks.

    This WAN optimizer should implement part 1 of project 4.
    """

    # Size of blocks to store, and send only the hash when the block has been
    # sent previously
    BLOCK_SIZE = 8000

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).

        self.srcdest_to_buffer = {}  # (src, dest) -> corresponding buffer
        self.hash_to_raw_data = {}   # get_hash(data) -> data
        return

    def receive(self, packet):
        """ Handles receiving a packet.

        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 1.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of 
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            if not packet.is_raw_data:
                left_to_send = self.hash_to_raw_data[packet.payload]
                while len(left_to_send) > 0:
                    if len(left_to_send) <= MAX_PACKET_SIZE:
                        pack = Packet(packet.src, packet.dest, True, False, left_to_send)
                        self.send(pack, self.address_to_port[packet.dest])
                        left_to_send = ""
                    else:
                        pack = Packet(packet.src, packet.dest, True, False, left_to_send[:MAX_PACKET_SIZE])
                        self.send(pack, self.address_to_port[packet.dest])
                        left_to_send = left_to_send[MAX_PACKET_SIZE:]
                if packet.is_fin:
                    pack = Packet(packet.src, packet.dest, True, True, "")
                    self.send(pack, self.address_to_port[packet.dest])

            else:
                if packet.is_fin and len(packet.payload) == 0:
                    # just forward empty fin packet
                    self.send(packet, self.address_to_port[packet.dest])
                else:
                    if (packet.src, packet.dest) not in self.srcdest_to_buffer.keys():
                        self.srcdest_to_buffer[(packet.src, packet.dest)] = ""
                    pack_buff = self.srcdest_to_buffer[(packet.src, packet.dest)]
                    pack_buff += packet.payload

                    if len(pack_buff) >= self.BLOCK_SIZE:
                        block_to_send = pack_buff[:self.BLOCK_SIZE]
                        pack_buff = pack_buff[self.BLOCK_SIZE:]
                        block_hash = get_hash(block_to_send)
                        self.hash_to_raw_data[block_hash] = block_to_send
                        # send block_to_send in multple packets
                        left_to_send = block_to_send[:]
                        while len(left_to_send) > 0:
                            if len(left_to_send) <= MAX_PACKET_SIZE:
                                pack = Packet(packet.src, packet.dest, True, False, left_to_send)
                                self.send(pack, self.address_to_port[packet.dest])
                                left_to_send = ""
                            else:
                                pack = Packet(packet.src, packet.dest, True, False, left_to_send[:MAX_PACKET_SIZE])
                                self.send(pack, self.address_to_port[packet.dest])
                                left_to_send = left_to_send[MAX_PACKET_SIZE:]

                        if packet.is_fin and len(pack_buff) == 0:
                            # send empty fin packet
                            pack = Packet(packet.src, packet.dest, True, True, "")
                            self.send(pack, self.address_to_port[packet.dest])

                    if packet.is_fin:
                        block_to_send = pack_buff[:]
                        pack_buff = ""
                        block_hash = get_hash(block_to_send)
                        self.hash_to_raw_data[block_hash] = block_to_send
                        left_to_send = block_to_send[:]
                        while len(left_to_send) >= 0:
                            if len(left_to_send) <= MAX_PACKET_SIZE:
                                pack = Packet(packet.src, packet.dest, True, True, left_to_send)
                                self.send(pack, self.address_to_port[packet.dest])
                                left_to_send = ""
                                break
                            else:
                                pack = Packet(packet.src, packet.dest, True, False, left_to_send[:MAX_PACKET_SIZE])
                                self.send(pack, self.address_to_port[packet.dest])
                                left_to_send = left_to_send[MAX_PACKET_SIZE:]


                    self.srcdest_to_buffer[(packet.src, packet.dest)] = pack_buff

        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            if (packet.src, packet.dest) not in self.srcdest_to_buffer.keys():
                self.srcdest_to_buffer[(packet.src, packet.dest)] = ""
            pack_buff = self.srcdest_to_buffer[(packet.src, packet.dest)]

            pack_buff += packet.payload
            if len(pack_buff) >= self.BLOCK_SIZE:
                block_to_send = pack_buff[:self.BLOCK_SIZE]
                pack_buff = pack_buff[self.BLOCK_SIZE:]
                block_hash = get_hash(block_to_send)
                if block_hash in self.hash_to_raw_data.keys():
                    # send hash in new packet
                    pack = Packet(packet.src, packet.dest, False, False, block_hash)
                    self.send(pack, self.wan_port)
                else:
                    self.hash_to_raw_data[block_hash] = block_to_send
                    # send block in multiple new packets
                    left_to_send = block_to_send[:]
                    while len(left_to_send) > 0:
                        if len(left_to_send) <= MAX_PACKET_SIZE:
                            pack = Packet(packet.src, packet.dest, True, False, left_to_send)
                            self.send(pack, self.wan_port)
                            left_to_send = ""
                        else:
                            pack = Packet(packet.src, packet.dest, True, False, left_to_send[:MAX_PACKET_SIZE])
                            self.send(pack, self.wan_port)
                            left_to_send = left_to_send[MAX_PACKET_SIZE:]
                if packet.is_fin and len(pack_buff) == 0:
                    # send empty fin packet
                    pack = Packet(packet.src, packet.dest, True, True, "")
                    self.send(pack, self.wan_port)
                    self.srcdest_to_buffer[(packet.src, packet.dest)] = ""
                    return

            if packet.is_fin:
                block_to_send = pack_buff[:]
                pack_buff = ""
                block_hash = get_hash(block_to_send)
                if block_hash in self.hash_to_raw_data.keys():
                    # send hash in new packet
                    # set is_fin to true
                    pack = Packet(packet.src, packet.dest, False, True, block_hash)
                    self.send(pack, self.wan_port)
                else:
                    if block_to_send != "":
                        self.hash_to_raw_data[block_hash] = block_to_send
                    # send block in multiple new packets
                    # set is_fin to true in the last packet
                    left_to_send = block_to_send[:]
                    while len(left_to_send) >= 0:
                        if len(left_to_send) <= MAX_PACKET_SIZE:
                            pack = Packet(packet.src, packet.dest, True, True, left_to_send)
                            self.send(pack, self.wan_port)
                            left_to_send = ""
                            break
                        else:
                            pack = Packet(packet.src, packet.dest, True, False, left_to_send[:MAX_PACKET_SIZE])
                            self.send(pack, self.wan_port)
                            left_to_send = left_to_send[MAX_PACKET_SIZE:]
            self.srcdest_to_buffer[(packet.src, packet.dest)] = pack_buff



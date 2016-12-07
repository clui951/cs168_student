import wan_optimizer
from utils import *
from tcp_packet import *

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into variable-sized
    blocks based on the contents of the file.

    This WAN optimizer should implement part 2 of project 4.
    """

    # The string of bits to compare the lower order 13 bits of hash to
    GLOBAL_MATCH_BITSTRING = '0111011001010'

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
        functionality described in part 2.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of 
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            # if packet.is_fin:
                # print("2nd wan sees a fin")

            if packet.is_fin and len(packet.payload) == 0:
                # print("empty fin, foward fin")
                pack_buff = self.srcdest_to_buffer[(packet.src, packet.dest)]
                block_hash = get_hash(pack_buff)
                if block_hash not in self.hash_to_raw_data.keys():
                    self.hash_to_raw_data[block_hash] = pack_buff
                self.send_data_in_packets(packet.src, packet.dest, True, False, pack_buff, is_wan_port = False)
                self.srcdest_to_buffer[(packet.src, packet.dest)] = "" # reset buffer
                self.send(packet, self.address_to_port[packet.dest]) # forward empty fin
                return
            
            if (packet.src, packet.dest) not in self.srcdest_to_buffer.keys():
                self.srcdest_to_buffer[(packet.src, packet.dest)] = ""
            
            if packet.is_raw_data:
                pack_buff = self.srcdest_to_buffer[(packet.src, packet.dest)]
                pack_buff += packet.payload

                block_list, remaining_buff = self.break_data_into_blocks(pack_buff)
                for block_to_send in block_list:
                    block_hash = get_hash(block_to_send)
                    # print("sending1")
                    if block_hash in self.hash_to_raw_data.keys():
                        # send extract data from hash in packet
                        block_to_send = self.hash_to_raw_data[block_hash]
                        self.send_data_in_packets(packet.src, packet.dest, True, False, block_to_send, is_wan_port = False)
                    else:
                        self.hash_to_raw_data[block_hash] = block_to_send
                        self.send_data_in_packets(packet.src, packet.dest, True, False, block_to_send, is_wan_port = False)

                if remaining_buff:
                    # print("wan to client remaining_buff: " + remaining_buff)
                    if packet.is_fin:
                        block_hash = get_hash(remaining_buff)
                        block_to_send = remaining_buff
                        # print("sending2")
                        if block_hash in self.hash_to_raw_data.keys():
                        # send hash in packet
                            self.send_data_in_packets(packet.src, packet.dest, True, False, block_to_send, is_wan_port = False)
                        else:
                            self.hash_to_raw_data[block_hash] = block_to_send
                            self.send_data_in_packets(packet.src, packet.dest, True, False, block_to_send, is_wan_port = False)
                        # print("sending fin1")
                        fin_pack = Packet(packet.src, packet.dest, True, True, "")
                        self.send(fin_pack, self.address_to_port[packet.dest])
                        pack_buff = ""
                    else:
                        pack_buff = remaining_buff
                else:
                    pack_buff = ""
                    if packet.is_fin:
                        # print("sending fin2")
                        fin_pack = Packet(packet.src, packet.dest, True, True, "")
                        self.send(fin_pack, self.address_to_port[packet.dest])
                self.srcdest_to_buffer[(packet.src, packet.dest)] = pack_buff
            else:
                block_hash = packet.payload
                block_to_send = self.hash_to_raw_data[block_hash]
                # print("sending3")
                self.send_data_in_packets(packet.src, packet.dest, True, False, block_to_send, is_wan_port = False)
                if packet.is_fin:
                    # print("sending fin3")
                    fin_pack = Packet(packet.src, packet.dest, True, True, "")
                    self.send(fin_pack, self.address_to_port[packet.dest])
                    # self.srcdest_to_buffer[(packet.src, packet.dest)] = "" # TESTING
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            if packet.is_fin and len(packet.payload) == 0:
                pack_buff = self.srcdest_to_buffer[(packet.src, packet.dest)]
                block_hash = get_hash(pack_buff)
                if block_hash in self.hash_to_raw_data.keys():
                    # send hash in packet
                    pack = Packet(packet.src, packet.dest, False, False, block_hash)
                    self.send(pack, self.wan_port)
                else:
                    self.hash_to_raw_data[block_hash] = pack_buff
                    self.send_data_in_packets(packet.src, packet.dest, True, False, pack_buff, is_wan_port = True)
                self.srcdest_to_buffer[(packet.src, packet.dest)] = ""
                self.send(packet, self.wan_port)
                return

            if (packet.src, packet.dest) not in self.srcdest_to_buffer.keys():
                self.srcdest_to_buffer[(packet.src, packet.dest)] = ""
            pack_buff = self.srcdest_to_buffer[(packet.src, packet.dest)]

            pack_buff += packet.payload
            block_list, remaining_buff = self.break_data_into_blocks(pack_buff)

            # send off all completed blocks
            for block_to_send in block_list:
                block_hash = get_hash(block_to_send)
                if block_hash in self.hash_to_raw_data.keys():
                    # send hash in packet
                    pack = Packet(packet.src, packet.dest, False, False, block_hash)
                    self.send(pack, self.wan_port)
                else:
                    self.hash_to_raw_data[block_hash] = block_to_send
                    self.send_data_in_packets(packet.src, packet.dest, True, False, block_to_send, is_wan_port = True)

            if remaining_buff:
                # print("wan to wan remaining_buff: " + remaining_buff)
                if packet.is_fin:
                    # print("finfin")
                    block_to_send = remaining_buff
                    block_hash = get_hash(block_to_send)
                    if block_hash in self.hash_to_raw_data.keys():
                    # send hash in packet
                        pack = Packet(packet.src, packet.dest, False, False, block_hash)
                        self.send(pack, self.wan_port)
                    else:
                        self.hash_to_raw_data[block_hash] = block_to_send
                        self.send_data_in_packets(packet.src, packet.dest, True, False, block_to_send, is_wan_port = True)
                    fin_pack = Packet(packet.src, packet.dest, True, True, "")
                    self.send(fin_pack, self.wan_port)
                    pack_buff = ""
                else:
                    pack_buff = remaining_buff
            else:
                pack_buff = ""
            self.srcdest_to_buffer[(packet.src, packet.dest)] = pack_buff



        








    # return a list of complete blocks and the remaining 
    # if no split, list of complete blocks is empty list
    # if split at end of data, remaining is empty string
    def break_data_into_blocks(self, data):
        complete_blocks = []
        remainder = ""
        changed = True
        while len(data) > 48 and changed:
            changed = False
            for i in range(len(data) - 48 + 1):
                substring = data[i:48 + i]
                substring_hash = get_hash(substring)
                substring_hash_lower = get_last_n_bits(substring_hash, 13)
                if substring_hash_lower == self.GLOBAL_MATCH_BITSTRING:
                    complete_blocks.append(data[:48+i])
                    data = data[48+i:]
                    changed = True
                    break
        remainder = data
        return (complete_blocks, remainder)


    # continuously send packets of MAX_PACKET_SIZE until all data sent
    # FIN PACKET STILL NEEDS TO BE EXPLICITLY SENT
    def send_data_in_packets(self, src, dest, is_raw_data, is_fin, data, is_wan_port):
        assert not is_fin
        left_to_send = data
        while len(left_to_send) >= 0:
            if len(left_to_send) <= MAX_PACKET_SIZE:
                pack = Packet(src, dest, is_raw_data, is_fin, left_to_send)
                if is_wan_port:
                    self.send(pack, self.wan_port)
                else:
                    self.send(pack, self.address_to_port[dest])
                left_to_send = ""
                break
            else:
                pack = Packet(src, dest, is_raw_data, is_fin, left_to_send[:MAX_PACKET_SIZE])
                if is_wan_port:
                    self.send(pack, self.wan_port)
                else:
                    self.send(pack, self.address_to_port[dest])
                left_to_send = left_to_send[MAX_PACKET_SIZE:]






# /Users/calvinlui/Documents/Berkeley/4th_Year/2016_Fall/CS168/cs168_student/projects/proj4_wanoptimizer
# python2 project4_tests.py --middlebox-name lbfs_wan_optimizer --send-less-than-one-block




"""
Your learning switch warm-up exercise for CS-168.
Start it up with a commandline like...
  ./simulator.py --default-switch-type=learning_switch topos.rand --links=0
"""
import sim.api as api
import sim.basics as basics
class LearningSwitch(api.Entity):
    """
    A learning switch.
    Looks at source addresses to learn where endpoints are.  When it doesn't
    know where the destination endpoint is, floods.
    This will surely have problems with topologies that have loops!  If only
    someone would invent a helpful poem for solving that problem...
    """
    def __init__(self):
        """
        Do some initialization.
        You probablty want to do something in this method.
        """
        self.debug = False
        self.dest_to_port = {}
    def handle_link_down(self, port):
        """
        Called when a port goes down (because a link is removed)
        You probably want to remove table entries which are no longer
        valid here.
        """
        dests_to_del = []
        for dest in self.dest_to_port:
            if self.dest_to_port[dest] == port:
                dests_to_del.append(dest)

        for dest in dests_to_del:
            del self.dest_to_port[dest]
            
    def handle_rx(self, packet, in_port):
        """
        Called when a packet is received.
        You most certainly want to process packets here, learning where
        they're from, and either forwarding them toward the destination
        or flooding them.
        """
        # The source of the packet can obviously be reached via the input port, so
        # we should "learn" that the source host is out that port.  If we later see
        # a packet with that host as the *destination*, we know where to send it!
        # But it's up to you to implement that.  For now, we just implement a
        # simple hub.
        if isinstance(packet, basics.HostDiscoveryPacket):
            # Don't forward discovery messages
            return
        if self.debug:
            print("Name: " + self.name)
            print("Origin: " + str(packet.src))
            print("Dest: " + str(packet.dst))
        if packet.src not in self.dest_to_port:
            self.dest_to_port[packet.src] = in_port
        if packet.dst in self.dest_to_port:
            if self.debug:
                print("Found dest in dict!  Dest: " + str(packet.dst))
                print("Dict: " + str(self.dest_to_port))
            self.send(packet, self.dest_to_port[packet.dst], flood=False)
        else:
            #self.dest_to_port[packet.src] = in_port
            if self.debug:
                print("Added new dest!  Dest: " + str(packet.src))
                print("Dict: " + str(self.dest_to_port))
            # Flood out all ports except the input port
            self.send(packet, in_port, flood=True)
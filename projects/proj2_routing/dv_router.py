"""Your awesome Distance Vector router for CS 168."""
import sim.api as api
import sim.basics as basics
# We define infinity as a distance of 16.
INFINITY = 16
class DVRouter(basics.DVRouterBase):
    # NO_LOG = True # Set to True on an instance to disable its logging
    # POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing
    def __init__(self):
        """
        Called when the instance is initialized.
        You probably want to do some additional initialization here.
        """
        self.destDict = {}          # dict: dst -> (out_port, dist, time_added)
        self.port_to_latency = {}   # dict: port -> (latency)
        self.start_timer()  # Starts calling handle_timer() at correct rate
    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.
        The port attached to the link and the link latency are passed
        in.
        """
        # save port/latency information into port_to_latency dict
        self.port_to_latency[port] = latency
        self.handle_timer()
    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.
        The port number used by the link is passed in.
        """
        # remove from port_to_latency dict
        # iterate through dict and update dst with port == out_port
            # if poison, set to infinity
            # else, delete entry completely
        # updates to neighbors will happen at next timer call
        del self.port_to_latency[port]
        dests_to_del = []
        for dst in self.destDict:
            if self.destDict[dst].port == port:
                if self.destDict[dst].directPort != port and self.destDict[dst].directHost:
                        self.destDict[dst].port = self.destDict[dst].directPort
                        self.destDict[dst].dist = self.port_to_latency[self.destDict[dst].directPort]
                else:    
                    if self.POISON_MODE:
                        self.destDict[dst].dist = INFINITY
                    else:
                        dests_to_del.append(dst)
        
        for dst in dests_to_del:
            del self.destDict[dst]

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.
        packet is a Packet (or subclass).
        port is the port number it arrived on.
        You definitely want to fill this in.
        """
        if isinstance(packet, basics.RoutePacket):
            # update own mapping about packet.destination
                # if packet received has dst in self.dstDict going through this port
                    # poison or split or simply update
            # create routepacket to flood neighbors about above update
            UPDATED_FLAG = True
            DELETED_FLAG = False
            if packet.destination not in self.destDict:
                self.destDict[packet.destination] = Dest(port, self.port_to_latency[port] + packet.latency, api.current_time())
            elif self.destDict[packet.destination].port == port:
                if self.POISON_MODE:
                    if packet.latency == INFINITY:                         
                        self.destDict[packet.destination].dist = INFINITY
                        if self.destDict[packet.destination].directHost and self.destDict[packet.destination].directPort in self.port_to_latency:
                            self.destDict[packet.destination].dist = self.port_to_latency[self.destDict[packet.destination].directPort]
                            self.destDict[packet.destination].port = self.destDict[packet.destination].directPort
                        self.destDict[packet.destination].time = api.current_time()
                    elif packet.latency + self.port_to_latency[port] >= INFINITY:
                        self.destDict[packet.destination].dist = INFINITY
                        if self.destDict[packet.destination].directHost and self.destDict[packet.destination].directPort in self.port_to_latency:
                            self.destDict[packet.destination].dist = self.port_to_latency[self.destDict[packet.destination].directPort]
                            self.destDict[packet.destination].port = self.destDict[packet.destination].directPort
                        self.destDict[packet.destination].time = api.current_time()
                    else:
                        self.destDict[packet.destination].dist = packet.latency + self.port_to_latency[port]
                        if self.destDict[packet.destination].directHost and self.destDict[packet.destination].directPort in self.port_to_latency and self.port_to_latency[self.destDict[packet.destination].directPort] < self.destDict[packet.destination].dist:
                            self.destDict[packet.destination].dist = self.port_to_latency[self.destDict[packet.destination].directPort]
                            self.destDict[packet.destination].port = self.destDict[packet.destination].directPort
                        self.destDict[packet.destination].time = api.current_time()
                else:    # split horizon
                    if packet.latency == INFINITY:
                        if self.destDict[packet.destination].directHost and self.destDict[packet.destination].directPort in self.port_to_latency:
                            self.destDict[packet.destination].dist = self.port_to_latency[self.destDict[packet.destination].directPort]
                            self.destDict[packet.destination].port = self.destDict[packet.destination].directPort
                        else:
                            del self.destDict[packet.destination]
                            DELETED_FLAG = True
                    elif packet.latency + self.port_to_latency[port] >= INFINITY:
                        if self.destDict[packet.destination].directHost and self.destDict[packet.destination].directPort in self.port_to_latency:
                            self.destDict[packet.destination].dist = self.port_to_latency[self.destDict[packet.destination].directPort]
                            self.destDict[packet.destination].port = self.destDict[packet.destination].directPort
                        else:
                            del self.destDict[packet.destination]
                            DELETED_FLAG = True
                    else:
                        self.destDict[packet.destination].dist = packet.latency + self.port_to_latency[port]
                        if self.destDict[packet.destination].directHost and self.destDict[packet.destination].directPort in self.port_to_latency and self.port_to_latency[self.destDict[packet.destination].directPort] < self.destDict[packet.destination].dist:
                            self.destDict[packet.destination].dist = self.port_to_latency[self.destDict[packet.destination].directPort]
                            self.destDict[packet.destination].port = self.destDict[packet.destination].directPort
                        self.destDict[packet.destination].time = api.current_time()
            else:
                if self.destDict[packet.destination].dist >= packet.latency + self.port_to_latency[port]:
                    self.destDict[packet.destination].dist = packet.latency + self.port_to_latency[port]
                    self.destDict[packet.destination].port = port
                    self.destDict[packet.destination].time = api.current_time()
                else:
                    UPDATED_FLAG = False
            if UPDATED_FLAG:
                if not DELETED_FLAG:
                    route_pack = basics.RoutePacket(packet.destination, self.destDict[packet.destination].dist)
                    self.send(route_pack, port=port, flood=True)
                if self.POISON_MODE:
                    poison_route_pack = basics.RoutePacket(packet.destination, INFINITY)
                    self.send(poison_route_pack, port=port)
        elif isinstance(packet, basics.HostDiscoveryPacket):
            # new router attached, update own table
            # share route with neighbors immediatly routepacket
            # HostDiscoveryPacket packet should not be forwarded
            lat = self.port_to_latency[port]
            curr_time = api.current_time()
            self.destDict[packet.src] = Dest(port, lat, curr_time, directHost=True, directPort=port)
            route_pack = basics.RoutePacket(packet.src, lat)
            self.send(route_pack, port=port, flood=True)
        else:
            # send packet based upon destination and dict mapping 
            # make sure destination still up
            # forward packet
            if packet.dst in self.destDict:
                if self.destDict[packet.dst].dist < INFINITY:
                    out_port = self.destDict[packet.dst].port
                    if port != out_port:
                        self.send(packet, port=out_port)
    def handle_timer(self):
        """
        Called periodically.
        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.
        """
        # handle timeouts

        # if True or str(self) == "<DVRouter r1>":
        #     print(str(self))
        #     print(DestDictString(self.destDict))
        dests_to_del = []
        for dest in self.destDict:
            if api.current_time() - self.destDict[dest].time >= 15 and not self.destDict[dest].directHost:
                    if self.POISON_MODE:
                        self.destDict[dest].dist = INFINITY
                    else:
                        dests_to_del.append(dest)
        for dest in dests_to_del:
            del self.destDict[dest]
        
        # forward tables
        for dest in self.destDict:
            route_pack = basics.RoutePacket(dest, self.destDict[dest].dist)
            self.send(route_pack, port=self.destDict[dest].port, flood=True)
            if self.POISON_MODE:
                poison_route_pack = basics.RoutePacket(dest, INFINITY)
                self.send(poison_route_pack, port=self.destDict[dest].port)
class Dest():
    def __init__(self, port, dist, time, directHost = False, directPort = None):
        self.port = port
        self.dist = dist
        self.time = time
        self.directHost = directHost
        self.directPort = directPort
    def __str__(self):
        return "(" + str(self.port) + ", " + str(self.dist) + ", " + str(self.time) + ", " + str(self.directHost) + ")"
def DestDictString(destDict):
    output = ""
    for dest in destDict:
        output += "(" + str(dest) + ", " + str(destDict[dest]) + ")  ;  "
    return output
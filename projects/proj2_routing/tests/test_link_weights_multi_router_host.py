"""
Tests that packets take the lowest-cost path.

Creates a topology like the following, where we have a single host connected to multiple routers.

       h1 -- c2
         \\   \\  
          c1   s2
           \\   \\
            s1 - s3 - s4 -- h2
       

After routes have converged, send a packet from h2 to h3.
The path should be s4-s3-s1-c1, because that will be the shortest path.

"""

import sim
import sim.api as api
import sim.basics as basics

from tests.test_simple import GetPacketHost, NoPacketHost


class CountingHub(api.Entity):
    pings = 0

    def handle_rx(self, packet, in_port):
        self.send(packet, in_port, flood=True)
        if isinstance(packet, basics.Ping):
            api.userlog.debug('%s saw a ping' % (self.name, ))
            self.pings += 1


def launch():
    h2 = NoPacketHost.create('h2')
    h1 = GetPacketHost.create('h1')

    s1 = sim.config.default_switch_type.create('s1')
    s2 = sim.config.default_switch_type.create('s2')
    s3 = sim.config.default_switch_type.create('s3')
    s4 = sim.config.default_switch_type.create('s4')

    c1 = CountingHub.create('c1')
    c2 = CountingHub.create('c2')

    h1.linkTo(c1, latency=1)
    h1.linkTo(c2, latency=1)
    c2.linkTo(s2, latency=4)
    c1.linkTo(s1, latency=1)
    s1.linkTo(s3, latency=1)
    s2.linkTo(s3, latency=1)
    s3.linkTo(s4, latency=1)
    s4.linkTo(h2, latency=1)

    def test_tasklet():
        yield 20

        api.userlog.debug('Sending ping from h1 to h2')

        h2.ping(h1)

        yield 5

        good = True
        if c1.pings != 1 or c2.pings != 0:
            api.userlog.debug('The ping took the wrong path')
            good = False
            api.userlog.debug('C1 received %i pings, C2 received %i pings' % (c1.pings, c2.pings))


        import sys
        sys.exit(0 if good else 1)

    api.run_tasklet(test_tasklet)

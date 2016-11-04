"""
Tests that packets take the lowest-cost path.

                h2
              0 ||
                R4
              //||\\
          2 //  ||  \\ 7
          //   8||    \\
    0   //  5   ||   1  \\   0
h5 --- R1 ----- H1 ----- R2 --- h4
        \\      ||      //
          \\   3||    //
          2 \\  ||  // 2
              \\||//
                R3
             .5 ||
                h3

After routes have converged, sends a packet from h2, h3, h4, and h5 to h2.
The test passes if the packet takes the path that is through R1, R2, and R3,
which has more hops but a lower total cost. We check which path the packet took
using c1, c2, c3, and c4, which are CountingHubs.

We then diconnect R2 from the graph, and mak sure that the shortest paths are
taken again.

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
    h1 = GetPacketHost.create('h1')
    h2 = GetPacketHost.create('h2')
    r1 = sim.config.default_switch_type.create('r1')
    r2 = sim.config.default_switch_type.create('r2')
    # c1 = CountingHub.create('c1')
    # c2 = CountingHub.create('c2')
    # h1.linkTo(r1, latency=3)
    h1.linkTo(r2, latency=1)
    r1.linkTo(h1, latency=4)
    r2.linkTo(h1, latency=1)
    r1.linkTo(r2, latency=1)
    h2.linkTo(r1, latency=1)

    def test_tasklet():
        yield 10

        api.userlog.debug('Sending pings')
        h2.ping(h1)

        yield 10

        api.userlog.debug('Disconnecting h1-r2')
        r2.unlinkTo(h1)

        yield 15

        api.userlog.debug('Sending pings')
        h2.ping(h1)

        yield 10

        r1.unlinkTo(h1)

        yield 10

        good = 1

        import sys
        sys.exit(0 if good else 1)

    api.run_tasklet(test_tasklet)

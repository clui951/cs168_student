"""
Super Cool Intense Test Case

Creates the following Topology:


   1     10     1
h1 - R1 ---- R3 - h2
      \\    //
     1  \\//  1
         R2

Sends a ping from h1 to h2, which should take the path:

h1 - R1 - R2 - R3 - h2


Then removes the R2 - R3 link:

   1     10     1
h1 - R1 ---- R3 - h2
      \\
     1  \\
         R2

Sends a ping from h1 to h2, which should take the path:

h1 - R1 - R3 - h2

"""

import sim
import sim.api as api
import sim.basics as basics
import sys

from tests.test_simple import GetPacketHost, NoPacketHost


class SwitchableCountingHub(api.Entity):
    pings = 0
    enabled = True

    def handle_rx(self, packet, in_port):
        if self.enabled:
            self.send(packet, in_port, flood=True)
        if isinstance(packet, basics.Ping):
            api.userlog.debug('%s saw a ping' % (self.name, ))
            self.pings += 1

def launch():

    h1 = GetPacketHost.create('h1')
    h2 = NoPacketHost.create('h2')

    r1 = sim.config.default_switch_type.create('r1')
    r2 = sim.config.default_switch_type.create('r2')
    r3 = sim.config.default_switch_type.create('r3')

    c1 = SwitchableCountingHub.create('c1')
    r1.linkTo(c1, latency=10)
    r3.linkTo(c1, latency=10)
    c2 = SwitchableCountingHub.create('c2')
    r2.linkTo(c2, latency=1)
    r3.linkTo(c2, latency=1)

    h1.linkTo(r1, latency=1)
    r1.linkTo(r2, latency=1)
    h2.linkTo(r3, latency=1)

    hosts = [h1, h2]
    routers = [r1, r2, r3]
    counting_hubs = [c1, c2]

    def test_tasklet():
        yield 20

        api.userlog.debug('Sending ping from h1 to h2 - it should get through')
        h1.ping(h2)

        yield 5

        if c1.pings != 0:
            api.userlog.error("The first ping should not pass through c1")
            sys.exit(1)

        if c2.pings != 1:
            api.userlog.error("The first ping didn't get through")
            sys.exit(1)

        yield 10

        api.userlog.debug('Silently disconnecting r2 and h2')
        c2.unlinkTo(r2)
        c2.unlinkTo(r3)

        yield 25

        api.userlog.debug('Sending ping from h1 to h2 - it should get through')
        h1.ping(h2)

        yield 15

        if c1.pings != 1:
            api.userlog.error("The second ping didn't get through")
            sys.exit(1)

        if c2.pings > 1:
            api.userlog.error("The second ping should not pass through c2")
            sys.exit(1)

        sys.exit(0)

    api.run_tasklet(test_tasklet)

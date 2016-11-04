"""
Super Cool Intense Test Case

Creates the following Topology:


              1
      2 -R1 - - - R2- 4
   0  // ||       || \\  0
h1 - RX  ||16   16||  RY - h2
      \\ ||       ||
      1 -R3 - - - R4
              1


A ping is sent from h1 to h2, and should travel the following path:
h1 - RX - R1 - R2 - RY - h2

Then a link between R4 and ry is created to create the following:

              1
      2 -R1 - - - R2- 4
   0  // ||       || \\  0
h1 - RX  ||16   16||  RY - h2
      \\ ||       || //
      1 -R3 - - - R4-2
              1

And a ping is sent from h1 to h2 which should take the following path:
h1 - RX - R3 - R4 - RY - h2

Then the link between R3 and R4 is removed to create the following:

              1
      2 -R1 - - - R2- 4
   0  // ||       || \\  0
h1 - RX  ||16   16||  RY - h2
      \\ ||       || //
      1 -R3       R4-2

And a ping is sent from h1 to h2 which should take the following path:
h1 - RX - R1 - R2 - RY - h2
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

    rx = sim.config.default_switch_type.create('rx')
    ry = sim.config.default_switch_type.create('ry')
    r1 = sim.config.default_switch_type.create('r1')
    r2 = sim.config.default_switch_type.create('r2')
    r3 = sim.config.default_switch_type.create('r3')
    r4 = sim.config.default_switch_type.create('r4')

    c1 = SwitchableCountingHub.create('c1')
    r1.linkTo(c1, latency=1)
    r2.linkTo(c1, latency=1)
    c2 = SwitchableCountingHub.create('c2')
    r3.linkTo(c2, latency=1)
    r4.linkTo(c2, latency=1)

    h1.linkTo(rx, latency=0)
    h2.linkTo(ry, latency=0)
    rx.linkTo(r1, latency=2)
    rx.linkTo(r3, latency=1)
    ry.linkTo(r2, latency=4)

    c3 = SwitchableCountingHub.create('c3')
    r1.linkTo(c3, latency=16)
    r3.linkTo(c3, latency=16)
    c4 = SwitchableCountingHub.create('c4')
    r2.linkTo(c4, latency=16)
    r4.linkTo(c4, latency=16)

    hosts = [h1, h2]
    routers = [r1, r2, r3, r4]
    counting_hubs = [c1, c2, c3, c4]

    def test_tasklet():
        yield 30

        api.userlog.debug('Sending ping from h1 to h2 - it should get through')
        h1.ping(h2)

        yield 5

        if c1.pings != 1:
            api.userlog.error("The first ping didn't get through")
            sys.exit(1)

        api.userlog.debug('Sending ping from h2 to h1 - it should get through')
        h2.ping(h1)

        yield 10

        if c1.pings != 2:
            api.userlog.error("The second ping didn't get through")
            sys.exit(1)

        yield 10

        api.userlog.debug('Silently connecting r2 and h2')
        ry.linkTo(r4, latency=2)

        yield 20

        api.userlog.debug('Sending ping from h1 to h2 - it should get through')
        h1.ping(h2)

        yield 5

        if c2.pings != 1:
            api.userlog.error("The first ping didn't get through")
            sys.exit(1)

        yield 10

        api.userlog.debug('Sending ping from h2 to h1 - it should get through')
        h2.ping(h1)

        yield 5

        if c2.pings != 2:
            api.userlog.error("The second ping didn't get through")
            sys.exit(1)

        yield 10


        api.userlog.debug('Silently disconnecting r2')
        c2.unlinkTo(r4)
        c2.unlinkTo(r3)

        api.userlog.debug('Waiting for routes to time out')
        yield 20

        api.userlog.debug('Sending ping from h1 to h2 - it should be sent through r1')
        h1.ping(h2)

        yield 5

        if c1.pings != 3:
            api.userlog.error('r1 never received ping')
            sys.exit(1)
        else:
            api.userlog.debug('r1 rerouted the ping as expected')
            sys.exit(0)

    api.run_tasklet(test_tasklet)

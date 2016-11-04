"""
A more complex test of a learning switch.

Creates some hosts connected to different switches. Sends some
pings. Makes sure the expected number of pings and pongs arrive.

"""

import sim
import sim.api as api
import sim.basics as basics
from tests.test_link_weights import CountingHub

class TestHost(basics.BasicHost):
    """A host that counts pings and pongs."""
    pings = 0
    pongs = 0
    ENABLE_DISCOVERY = False  # Too easy with it turned on!

    def handle_rx(self, packet, port):
        if isinstance(packet, basics.Ping):
            self.pings += 1
        elif isinstance(packet, basics.Pong):
            self.pongs += 1
        super(TestHost, self).handle_rx(packet, port)


def launch():
    h1 = TestHost.create("h1")
    h2 = TestHost.create("h2")
    h3 = TestHost.create("h3")
    h4 = TestHost.create("h4")

    c1 = CountingHub.create('c1')
    c2 = CountingHub.create('c2')
    c3 = CountingHub.create('c3')
    c4 = CountingHub.create('c4')

    c1.linkTo(h1)
    c2.linkTo(h2)
    c3.linkTo(h3)
    c4.linkTo(h4)


    s1 = sim.config.default_switch_type.create("s1")
    s2 = sim.config.default_switch_type.create("s2")
    s3 = sim.config.default_switch_type.create("s3")
    s4 = sim.config.default_switch_type.create("s4")
    s5 = sim.config.default_switch_type.create("s5")

    s1.linkTo(c1)
    s2.linkTo(c2)
    s3.linkTo(c3)
    s4.linkTo(c4)

    s1.linkTo(s5)
    s2.linkTo(s5)
    s3.linkTo(s5)
    s4.linkTo(s5)


    def test_tasklet():
        yield 1

        api.userlog.debug("Sending test pings")

        h1.ping(h2)

        yield 10

        h2.ping(h3)

        yield 10

        h3.ping(h4)

        yield 10

        h4.ping(h1)

        api.userlog.debug("Waiting for deliveries")

        yield 10

        h2.ping(h3)

        yield 10  # Wait five seconds for deliveries
        h2.ping(h3)

        yield 10

        h2.ping(h3)
        yield 10
        good = True

        if c1.pings != 4 or c2.pings != 6 or c3.pings != 6 or c4.pings != 4:
            good = False

        # End the simulation and (if not running in interactive mode) exit.
        import sys
        sys.exit(0 if good else 1)

    api.run_tasklet(test_tasklet)

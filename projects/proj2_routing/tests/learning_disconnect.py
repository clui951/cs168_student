"""
A Super Awesome test of a learning switch.

This makes sure that the handle_link_down function works correctly

Creates the following topology, then will have some of the links go down, and
will send pings and make sure the proper amount ar receieved

h1 - s1 - s2 - s3 - h2
     ||   ||   ||
     h3   h4   h5

"""

import sim
import sim.api as api
import sim.basics as basics


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
    h5 = TestHost.create("h5")

    hosts = [h1, h2, h3, h4, h5]

    s1 = sim.config.default_switch_type.create("s1")
    s2 = sim.config.default_switch_type.create("s2")
    s3 = sim.config.default_switch_type.create("s3")

    s1.linkTo(h1)
    s1.linkTo(h3)
    s2.linkTo(s1)
    s2.linkTo(s3)
    s2.linkTo(h4)
    s3.linkTo(h5)
    s3.linkTo(h2)

    def test_tasklet():
        yield 1

        api.userlog.debug("Sending test pings")

        h2.ping(h1)

        yield 3

        h2.ping(h4)

        yield 3

        h1.ping(h2)

        yield 3

        h1.ping(h3)

        yield 3

        h5.ping(h4)

        yield 3

        h3.ping(h5)

        yield 3

        api.userlog.debug("Waiting for deliveries")

        yield 15  # Wait five seconds for deliveries

        api.userlog.debug("Counting Pings and Pongs")
        pings = sum([h.pings for h in hosts])
        pongs = sum([h.pongs for h in hosts])

        good = True
        if pings != 16:
            api.userlog.error("Got %s pings", pings)
            good = False
        if h2.pongs != 2 or h1.pongs != 2 or h5.pongs != 1 or h3.pongs != 1:
            api.userlog.error("A node didn't receive the proper amount of pongs")
            good = False
        if pongs != 6:
            api.userlog.error("Got %s pongs", pongs)
            good = False

        if good:
            api.userlog.debug("Test passed successfully!")

        yield 1

        s3.unlinkTo(h5)
        s2.unlinkTo(h4)

        api.userlog.debug("Sending test pings")

        h2.ping(h1)

        yield 3

        h1.ping(h2)

        yield 3

        h1.ping(h3)

        yield 3

        h5.ping(h4)

        yield 3

        api.userlog.debug("Waiting for deliveries")

        yield 15  # Wait five seconds for deliveries

        api.userlog.debug("Counting Pings and Pongs")
        pings = sum([h.pings for h in hosts]) - pings
        pongs = sum([h.pongs for h in hosts]) - pongs

        if pings != 3:
            api.userlog.error("Got %s pings", pings)
            good = False
        if h2.pongs != 3 or h1.pongs != 4:
            api.userlog.error("A node didn't receive the proper amount of pongs")
            good = False
        if pongs != 3:
            api.userlog.error("Got %s pongs", pongs)
            good = False

        if good:
            api.userlog.debug("Test passed successfully!")

        # End the simulation and (if not running in interactive mode) exit.
        import sys
        sys.exit(0 if good else 1)

    api.run_tasklet(test_tasklet)

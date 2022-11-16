
Test Case: test_selector_002
----------------------------

    Description:

        This use case illustrates a Forwarding Information Base (FIB) with Virtual Routing and
        Forwarding (VRF) and Equal-Cost Multi-Path (ECMP) support. A FIB essentially is the data plane
        copy of the routing table. The VRF support allows for multiple logical routing tables to
        co-exist as part of the same "physical" routing table; the VRF ID typically identifies the
        logical table to provide the matching route for the IP destination address of the input packet.
        The ECMP provides a load balancing mechanism for the packet forwarding by allowing for multiple
        next hops (of equal or different weights, in case of Weighted-Cost Multi-Path (WCMP) to be
        provided for each route.

            In this use case, the VRF ID is read from the IP source address of the input packet as
        opposed to a more complex classification scheme being used. The routing table produces the ID
        of the group of next hops associated with the current route, out of which a single next hop
        is selected based on a hashing scheme that preserves the packet order within each flow (with
        the flow defined here by a typical 3-tuple) by always selecting the same next hop for packets
        that are part of the same flow. The next hop provides the Ethernet header and the output port
        for the outgoing packet.

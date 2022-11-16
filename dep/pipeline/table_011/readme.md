Test Case: test_table_011
-------------------------

    Sdenario being tested:
        To encap action that sets the entire IPv6 header passed as action argument.

    Description:
        Encap the entire IPv6 header passed as an action argument and transmit the packet
        on the same port, for matched action.
        Copy the source MAC address of the received packet into the destination MAC address
        and transmit the packet back on the same port for the unmatched action.

    Verification:
        Packet verification should happen according to the description.
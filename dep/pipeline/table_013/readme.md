Test Case: test_table_013
-------------------------

    Sdenario being tested:
        To use large field greater than 128 bits ( 136-bits here) as action argument as action argument.

    Description:
        Encap the IPV6 header fields from table mentioned fields, for a matched ipv6 hop_src_addr field.
        Transmit the packet back on the same port.
        Copy the source MAC address of the received packet into the destination MAC address
        and transmit the packet back on the same port for the unmatched action.

    Verification:
        Packet verification should happen according to the description.
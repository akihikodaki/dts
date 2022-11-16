Test Case: test_table_010
-------------------------

    Scenario being tested:
        To verify an action with an IPv6 address as an argument.

    Description:
        Copy the ipv6 version flow classification field, payload length and destination address
        from table mentioned field to headers, for a matched ipv6 destination address field.
        Transmit the packet back on the same port.
        Copy the source MAC address of the received packet into the destination MAC address
        and transmit the packet back on the same port for the unmatched action.

    Verification:
        Packet verification should happen according to the description.
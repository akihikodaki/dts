Test Case: test_jump_004
------------------------

    Instructions being tested:
        jmph LABEL

    Description:
        For the received packet, if its destination MAC address matches with any entry in the table (a hit), do not change the packet contents.
        For a miss, copy the source MAC address into destination MAC address.Transmit the packet back on the same port.

    Verification:
        For a table hit, contents of transmitted packet should be same as received. For a miss, the source and destination MAC address of
        transmitted packet should be same.

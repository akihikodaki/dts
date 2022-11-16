Test Case: test_shl_001
-------------------------

    Instructions being tested:
        shl m.field m.field

    Description:
        For the received packet, left shift the destination MAC address by 4 and transmit the packet back on the same port.

    Verification:
        Destination MAC address of the transmitted packet should be shifted left by 4 with respect to the destination MAC address of the received packet.

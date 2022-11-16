Test Case: test_shr_001
-------------------------

    Instructions being tested:
        shr m.field m.field

    Description:
        For the received packet, right shift the destination MAC address by 4 and transmit the packet back on the same port.

    Verification:
        Destination MAC address of the transmitted packet should be shifted right by 4 with respect to the destination MAC address of the received packet.

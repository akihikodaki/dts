Test Case: test_shr_006
-----------------------

    Instructions being tested:
        shr h.field immediate_value

    Description:
        For the received packet, right shift the destination MAC address by 4 and transmit the packet back on the same port.

    Verification:
        Destination MAC address of the transmitted packet should be shifted right by 4 with respect to the destination MAC address of the received packet.

Test Case: test_add_006
-----------------------

    Instruction being tested:
        add m.field m.field

    Description:
        For the received packet, add the source MAC address to the destination MAC address and transmit it back on the same port.

    Verification:
        Destination MAC address of the transmitted packet should be the sum of source and destination MAC addresses of the received packet.

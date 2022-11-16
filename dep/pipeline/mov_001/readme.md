
Test Case: test_mov_001
-----------------------

    Instruction being tested:
        mov h.field h.field

    Description:
        Copy the source MAC address, destination MAC address and destination IP
        address of the received packet into the destination IP address, source
        MAC address and destination MAC address fields respectively and transmit
        the packet back on the same port.

    Verification:
        For the received packet, the source MAC address, destination MAC
        address and destination IP address should be copied into the
        destination IP address, source MAC address and destination MAC address
        fields respectively and the packet should be transmitted back on the
        same port.

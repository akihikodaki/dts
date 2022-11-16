Test Case: test_xor_004
-----------------------

    Instruction being tested:
        xor m.field h.field

    Description:
	Update destination MAC address with bitwise xor of source and destination MAC address, then transmit the packet back on the same port.

    Verification:
	Destination MAC address of the received packet should be bitwise xor of source and destination MAC addresses.

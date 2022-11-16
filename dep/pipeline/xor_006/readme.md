Test Case: test_xor_006
-----------------------

    Instructions being tested:
	xor m.field t.field

    Description:
	Transmit the packet on the port which is result of bitwise xor of received port and the value present in the table.

    Verification:
	Packet should be received on the port which is result of bitwise xor of received port and table entry, for example if the packet is received on port 0 and table has entry 1 then packet will be received at port 1.

Test Case: test_and_002
-----------------------

    Instructions being tested:
	and m.field t.field

    Description:
	For a packet with matching destination MAC address, bitwise AND the received port metadata with the value stored in the table.

    Verification:
	Packet should be received on the port which is the result of logical AND of received port and value stored in the table.

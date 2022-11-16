Test Case: test_or_008
-----------------------

    Instructions being tested:
	or m.field t.field

	Description:
	For a packet with matching destination MAC address, bitwise OR the received port metadata with the value stored in the table.

	Verification:
	Packet should be received on the port which is the result of logical OR of received port and value stored in the table.

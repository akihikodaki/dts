Test Case: test_sub_007
-----------------------

    Instructions being tested:
	sub h.field t.field

	Description
	For a packet with matching destination MAC address, Reduce the TTL of the packet by the value in the table and transmit the packet in the same port.

	Verification:
	TTL value of the received packet is decremented by the value stored in the table.

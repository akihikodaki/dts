
Test Case: test_or_001
-----------------------

	Instructions being tested:
		or h.field t.field

	Description:
		For a packet with matching destination MAC address, bitwise OR the
		destination IP address with the action data of matching rule in the
		table and transmit the packet back on the same port.

    Verification:
		Received packet should have the destination IP address updated as per
		the matching rule in the table.

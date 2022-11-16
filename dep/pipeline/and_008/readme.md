
Test Case: test_and_008
-----------------------

	Instructions being tested:
		and h.field t.field

	Description:
		For a packet with matching destination MAC address, destination IP
		address will be logically AND with the matching entry action data in
		the table.

    Verification:
		Packet should be received on the same port and destination IP address
		should be logically and with the matching entry action data in the
		table.

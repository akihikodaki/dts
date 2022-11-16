
Test Case: test_xor_007
-----------------------

	Instructions being tested:
		xor h.field t.field

	Description:
		For a packet with matching destination MAC address, logically XOR the
		destination IP address with the action data of the matching rule in the
		table.

	Verification:
		For a packet with matching destination MAC address, destination IP
		address should be logically XOR with the action data of the matching
		rule in the table.

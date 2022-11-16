Test Case: test_shr_007
-----------------------

    Instructions being tested:
	shr h.field t.field

	Description:
	For a packet with matching destination IP address, source IP address is shifted right by the value stored in the table.

	Verification:
	Source IP address of the received packet on the same port will be shifted right by the amount mentioned in the table.

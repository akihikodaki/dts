Test Case: test_shl_007
-----------------------

    Instructions being tested:
	shl h.field t.field

	Description:
	For a packet with matching destination IP address, source IP is shifted left by the value stored in the table.

	Verification:
	Source IP address of the received packet on the same port will be shifted left by the amount mentioned in the table

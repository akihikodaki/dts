Test Case: test_sub_008
-----------------------

    Instructions being tested:
	sub m.field t.field

	Description:
	For a packet with matching destination IP address, Decrement the source IP address by the value present in the table and send the packet on the same port.

	Verification:
	Source IP address of the received packet will have decremented by the value stored in the table.

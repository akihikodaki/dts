Test Case: test_jump_047
-----------------------

    Instructions being tested:
	 jmplt LABEL m.field t.field


	Description:
	For a packet with matching destination IP address, if the Ethertype of the packet is less than the entry in the table, then packet will be transmitted back to the same port after decrementing its ttl, else the packet is dropped.
	Verification:
	Packets with ethertype less than table entry are received.

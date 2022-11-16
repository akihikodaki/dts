Test Case: test_jump_031
-----------------------

    Instructions being tested:
	 jmpeq LABEL t.field immediate_value


	Description
	In this test case, for a given tcp destination port, if the destination ip address in the table is equal to the immediate value then packet is transmitted after decrementing ttl of the packet, else packet is dropped.
	Verification
	Behaviour should be as per description

Test Case: test_jump_043
-----------------------

    Instructions being tested:
	 jmpneq LABEL t.field immediate_value


	Description
	In this test case, for a given tcp destination port, if the destination ip address in the table entry is not equal to the immediate value then packet is transmitted after decrementing the ttl, else packet is dropped.
	Verification
	Behaviour should be as per description

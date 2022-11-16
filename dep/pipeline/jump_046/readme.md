Test Case: test_jump_046
-----------------------

    Instructions being tested:
	 jmplt LABEL t.field immediate_data


	Description
	In this testcase, for a given destiantion ip address of the packet if the tcp acknoledgement no in the table  is the less than immediate value then packet will be transmitted back to the same port with by decrementing ttl. else packet is dropped.

	Verification
	Behaviour should be as per description

Test Case: test_jump_028
-----------------------

    Instructions being tested:
	jmpeq LABEL t.field t.field


	Description
	In this testcase, for a given tcp destination port mentioned in the table, if the tcp sequence number in that table is equal to the tcp acknoledgement number in the table then packet will be transmitted back to the same port, else packet is dropped.
	Verification
	Packets with tcp destination, in the table has tcp sequence no and tcp acknoledgment no are equal are received.

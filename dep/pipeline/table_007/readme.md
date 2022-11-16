Test Case: test_table_007
-------------------------
    Instruction to be tested
        table (default_action action args none | ARGS VALUE ... [const])

    Description:
        This testcase verify the parameterizes defult action. In this testcase the packets which miss
		table lookup have its ethernet header updated.

    Verification:
        Packet which is not matching is should have updated value of ethernet header.

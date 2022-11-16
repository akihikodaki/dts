Test Case: test_table_006
-------------------------
    Instruction to be tested
        table (default_action action args none | ARGS VALUE ... [const])

    Description:
        This testcase verify the parameterized default action. Along with that this testcase also
		verifies the endianess of the data. In this testcase whenever any lookup miss. We will
		add vxlan header on the top of the packet.

    Verification:
        Packet which is not matching is should have vxlan header on the top of the packet.

Test Case: test_xor_001
-----------------------

    Instruction being tested:
        xor m.field immediate_value

    Description:
        Receive a packet on some port_id and transmit it on port_id obtained by bitwise xor of received port_id and one.

    Verification:
        Check the transmitted packet on port_id obtained by bitwise xor of received port_id and one.

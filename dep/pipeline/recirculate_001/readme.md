Test Case: test_recirculate_001
-----------------------

    Instruction being tested:
        recircid m.field
        recirculate

    Description:
        Recirculate the packet for N(5) times, until the pass(recirc_id) value is equal to N.
        The UDP source port is incremented by one(1) for each recirculation.

    Verification:
        The packet should be sent out on the same port that it received.
        The UDP source port of the packet should be increment by 5.
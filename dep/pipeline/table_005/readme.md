Test Case: test_table_005
-------------------------
    Instruction to be tested
        table (default_action action args none | ARGS VALUE ... [const])

    Description:
        Default action arguments are none. Whenever packet is missed then its MAC destination address is updated

    Verification:
        Packet which is not matching is should have updated value of MAC address.

Test Case: test_learner_003
-----------------------

    Instruction being tested:
        learner TABLE_NAME (default_action ACTION_NAME args none | ARGS_BYTE_ARRAY [ const ])

    Description:
		The testcase verify the parametrized default action. A packet is sent that miss
		the table lookup. The received packet will have updated value of MAC source address.

    Verification:
        Simulate the test as per the description. Behaviour should be as described.

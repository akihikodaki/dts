Test Case: test_learner_001
-----------------------

    Instruction being tested:
        learner TABLE_NAME

    Description:
		If lookup miss then rule should be added and packet is dropped.
		The rule added will be to transmit the packet back to the same port.
		If the same key is looked upon again then the packet will follow the added rule.

    Verification:
        Simulate the test as per the description. Behaviour should be as described.

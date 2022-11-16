Test Case: test_learner_006
-----------------------

    Instruction being tested:
        forget

    Description:
		If lookup miss then rule should be added and packet is trasmitted back to the same port.
		When the lookup hit then rule is forgetten and packet is dropped.

    Verification:
        Simulate the test as per the description. Behaviour should be as described.

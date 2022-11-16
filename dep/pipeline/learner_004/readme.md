Test Case: test_learner_004
-----------------------

    Instruction being tested:
        learner TABLE_NAME (default_action ACTION_NAME args none | ARGS_BYTE_ARRAY [ const ])

    Description:
		In this testcase we verify the default action parameters value. This testcase verify
		endianess of the action parameters. The packet which miss the table lookup will be
		updated with a vxlan header. The default action have parameter that need to convert
		into network byte order also there are some parameters which no need to convert.
		This will verify the endianess conversion of the action data.

    Verification:
        The packet are sent which will miss the table lookup. The received packet will have
		vxlan header on the top of the packet.

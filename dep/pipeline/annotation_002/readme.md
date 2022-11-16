Test Case: test_annotation_002
-----------------------

    Scenario being tested:
        SPEC file don't have any defaultonly and tableonly annotations.
        The actions mentioned in the SPEC file are listed/configured properly in rule file.
        The application should run without any errors and packet verification must happen accordingly.

    Verification:
        Packet should get verified according to configured rules in the table file.

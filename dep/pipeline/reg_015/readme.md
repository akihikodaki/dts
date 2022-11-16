
Test Case: test_reg_015
-----------------------

    Instruction being tested:
        regwr REGARRAY t.field h.field

    Description:
        Write specific locations of register array by sending a packet to DUT
        and using the above command to write. Verify the values written by
        reading those locations using regrd CLI command.

    Verification:
        The values read via regrd CLI command should match with those
        previously written.

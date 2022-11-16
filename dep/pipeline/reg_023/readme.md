
Test Case: test_reg_023
-----------------------

    Instruction being tested:
        regwr REGARRAY imm_value m.field

    Description:
        Write specific locations of register array by sending a packet to DUT
        and using this instruction to write. Verify the values written by
        reading those locations using regrd CLI command.

    Verification:
        The values read via regrd CLI command should match with those
        previously written.

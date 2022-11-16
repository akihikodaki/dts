
Test Case: test_reg_039
-----------------------

    Instruction being tested:
        regadd REGARRAY imm_value m.field

    Description:
        Write some values to specific locations of register array via regwr
        CLI command. Send a packet to DUT for updating the previously written
        locations using this instruction. Verify the updated values by reading
        them via regrd CLI command.

    Verification:
        The values read via regrd CLI command should be equal to the addition
        of values sent via packet and those initially written using regwr CLI
        command.

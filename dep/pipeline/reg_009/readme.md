
Test Case: test_reg_009
-----------------------

    Instruction being tested:
        regrd m.field REGARRAY imm_value

    Description:
        Write some values to specific locations of register array via "regwr"
        CLI command. Using the above instruction, read the written values and
        write those values to other locations of register array.
        Verify reading these values through regrd CLI command.

    Verification:
        Values read through regrd CLI command should match the values written
        via regwr CLI command.

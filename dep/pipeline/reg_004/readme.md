
Test Case: test_reg_004
-----------------------

    Instruction being tested:
        regrd h.field REGARRAY t.field

    Description:
        Write some values to specific locations of register array via "regwr"
        CLI command and verify reading the values through this instruction.

    Verification:
        Values read through this instruction should match the values written
        via regwr CLI command.

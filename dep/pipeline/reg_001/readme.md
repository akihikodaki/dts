
Test Case: test_reg_001
-----------------------

    CLI commands being tested:
        pipeline <pipeline_name> regrd <register_array_name> <index>
	    pipeline <pipeline_name> regwr <register_array_name> <index> <value>

    Description:
        Read initial zero value of certain location of register array using "regrd" CLI command.
        Update that value to a new value through "regwr" CLI command.
        Read updated value of that location of register array using "regrd" CLI command.

    Verification:
        regrd command should read the correct value of register array.
        regwr command should modify register array location with the required value.

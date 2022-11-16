
Test Case: test_met_001
-----------------------

    Instruction being tested:
        meter METARRAY m.field h.field imm_val m.field

	CLI commands being tested:
		pipeline <pipeline_name> meter profile <profile_name> add cir <cir> pir <pir> cbs <cbs> pbs <pbs>
		pipeline <pipeline_name> meter profile <profile_name> delete
		pipeline <pipeline_name> meter <meter_array_name> from <index0> to <index1> reset
		pipeline <pipeline_name> meter <meter_array_name> from <index0> to <index1> set profile <profile_name>

    Description:
        Use a meter of certain size. Assign a particular incoming flow (packets
		having a certain destination MAC address) to a meter index. Set a meter
		profile to that same meter index. Send packet burst to DUT at a rate
		more than the supported CBS + PBS as well as at a rate less than
		CBS + PBS. Change the meter profile and repeat the same test. Now reset
		that meter index and check the default profile using the same test.

    Verification:
        Packets received on Port 0 (Green packets), Port 1 (Yellow packets) &
		Port 2 (Red packets) should comply with the meter profile used in
		the DUT.

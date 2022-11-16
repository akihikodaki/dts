
Test Case: test_met_014
-----------------------

    Instruction being tested:
        metprefetch METARRAY m.field

    Description:
        Use a meter of certain size. Assign a particular incoming flow (packets
		having a certain destination MAC address) to a meter index. Set a meter
		profile to that same meter index. Send packet burst to DUT at a rate
		more than the supported CBS + PBS as well as at a rate less than
		CBS + PBS.

    Verification:
        Packets received on Port 0 (Green packets), Port 1 (Yellow packets) &
		Port 2 (Red packets) should comply with the meter profile used in
		the DUT.

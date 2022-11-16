Test Case: test_add_003
-----------------------

    Instruction being tested:
        add m.field immediate_value

    Description:
        Increment the port_id by 1 and transmit the packet on that port_id.

    Verification:
	Packet should be received on the increamented port, for example if packet received by DUT on port 0 then it will be transmitted by DUT on port 1.

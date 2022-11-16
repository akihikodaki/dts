Test Case: test_add_007
-----------------------

    Instructions being tested:
	add h.field t.field


    Description:
	For a packet with matching destination MAC address, source IP address is added with the entry in table and updated source IP address is tranmitted on the same port.

    Verification:
	Packet will be received on the same port and source IP address will be sum of previous IP source address and table entry.

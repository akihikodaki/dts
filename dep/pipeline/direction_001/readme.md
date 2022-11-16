Test Case: test_direction_001
-----------------------------

    Description:
        Packet processing can be conditioned based on the packet flow direction.
	Each port either belongs to network or host side as per PNA specification.

    Verification:
        Send the same packet to all the ports, the packets expected to received on the same port.
	The packets from the HOST direction has been updated with specific source(0x005544332211)
	and destination(0x00eeddccbbaa) MAC address. Packets from NETWORK direction updated with
	source (0x001122334455) and destinateion(0x00AABBCCDDEE) MAC address.

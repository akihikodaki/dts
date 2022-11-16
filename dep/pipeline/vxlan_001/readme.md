Use Case: test_vxlan_001
-----------------------

    Instructions being used:
	rx, extract, table, dma h.field t.field (4 level), mov m.field t.field, add h.field h.field, ckadd h.field h.field,  mov h.field immediate_data, emit, tx


    Description:
	For a packet with matching destination MAC address, Packet is converted into Vxlan header packet. Input packet is with ethernet and IPv4 header and output packet will have outer ethernet, outer IPv4, outer UDP, outer Vxlan , ethernet and IPv4 headers. Packet details will be updated from the table entry corrosponding to the destination MAC address.

    Verification:
	Behavious as per description.

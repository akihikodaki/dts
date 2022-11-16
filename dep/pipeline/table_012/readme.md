Test Case: test_table_012
-------------------------

    Sdenario being tested:
        To use large field 64 < x-bits < 128 bit ( x = 80-bits here) as action argument as action argument.

    Description:
        Copy the ipv4 length, identification number, flags offset, time to live, protocol and
        checksum from table mentioned field to headers, for a matched ipv4 len_id_flags_tt_protocol_checksum field.
        Transmit the packet back on the same port.
        Copy the source MAC address of the received packet into the destination MAC address
        and transmit the packet back on the same port for the unmatched action.

    Verification:
        Packet verification should happen according to the description.
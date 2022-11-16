Test Case: test_mirror_003
-----------------------

    CLI being tested:
        pipeline PIPELINE0 mirror slots <max_slots> sessions <max_sessions>
        pipeline PIPELINE0 mirror session <session_id> port <port_id> clone [slow] truncate [truncate_length]

    Instruction being tested:
        mirror m.field m.field

    Description:
        Mirror(clone) all the packet that are received with UDP destination port 5000.
        The mirroring type is slow (copy of buffer) and truncates the packet data
        according to the configured length before sending the packet on mirror port.

        Based on the configuration, truncate length is,
        a) ZERO, then the mirror packet length is orignial packet length.
        b) lesser than the original packet length then the mirror packet length is truncate length.
        c) greater than the orginal packet length then the mirror packet length is original packet length.

    Verification:
        The packet should be sent out on the same port that it received.
        The mirror copy of the packet should be sent out on the configured mirror port.
        The mirrored packet length should match configured truncated criteria.
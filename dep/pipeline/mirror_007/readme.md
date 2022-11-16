Test Case: test_mirror_007
-----------------------

    CLI being tested:
        pipeline PIPELINE0 mirror slots <max_slots> sessions <max_sessions>
        pipeline PIPELINE0 mirror session <session_id> port <port_id> clone [slow/fast] truncate <truncate_length>

    Instruction being tested:
        mirror m.field m.field

    Description:
        Check mirroring for the packet that are received with UDP destination port 500.

    Verification:
        The packet should be sent out on the same port that it received.
        The mirror copy of the packet should not be sent out on the mirror port.
Test Case: test_mirror_001
-----------------------

    CLI being tested:
        pipeline PIPELINE0 mirror slots <max_slots> sessions <max_sessions>
        pipeline PIPELINE0 mirror session <session_id> port <port_id> clone [fast] truncate <truncate_length>

    Instruction being tested:
        mirror m.field m.field

    Description:
        Mirror(clone) all the packet that are received with UDP destination port 5000.
        The mirroring type is fast(reference of buffer).

    Verification:
        The packet should be sent out on the same port that it received.
        The mirror copy of the packet should be sent out on the configured mirror port.
        The mirrored packet content, should be same as the original transmitted packet.
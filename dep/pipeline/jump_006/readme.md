Test Case: test_jump_006
------------------------

    Instructions being tested:
        jmpa LABEL ACTION

    Description:
        For received packet, if its destination MAC doesn't match with any entry in table (a miss), drop the packet. Else (a hit) perform
        the action specified for the match. Take a jump based on the action performed for the match. For packet with matching action
        specified in jump instruction do not change its contents, for packets copy the destination MAC to source MAC. Transmit the packet
        back on the same port.

    Verification:
        Behavior should be as per the description.

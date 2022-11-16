Test Case: test_jump_013
------------------------

    Instructions being tested:
        jmplt LABEL h.field immediate_value

    Description:
        For the received packet, if the ttl value is less than 0x50, decrement it and transmit the packet back on the same
        port. Else drop the packet.

    Verification:
        If the received packet had the ttl value less than 0x50, then the transmitted packet should have ttl value one less
        than it. Else the received packet should be dropped.

Test Case: invalidate_001
------------------------

    Instructions being tested:
        invalidate h.header

    Description:
        For the received packet, if its ether type is 0x0800, transmit it back on the same port. Else drop the packet.

    Verification:
        Packets received with ether type 0x0800 should be reverted back as it is on the same port. All other packets should be dropped.

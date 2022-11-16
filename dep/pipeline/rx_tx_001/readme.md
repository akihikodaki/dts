Test Case: test_rx_tx_001
-------------------------

    Instructions being tested:
        rx m.field
        tx m.field

    Description:
        For the received packet, without modifying it, transmit the packet back on the same port.

    Verification:
        The transmitted packet should be same as that of the received packet.

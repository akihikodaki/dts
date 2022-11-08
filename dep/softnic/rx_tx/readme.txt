Test Case: rx_tx
-----------------------
Description:
    This test is to verify packet transmission by the Soft NIC driver. In this test we have two pipeline connected using ring
    port. First pipeline takes packet from physical port and put the packet in ring port. And second pipeline takes packet
    from ring port and send the packet out to the physical port.
Verification:
    The received packets should be same as the transmitted packets.

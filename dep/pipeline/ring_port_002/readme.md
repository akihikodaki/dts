
Test Case: test_ring_port_002
-----------------------------

    Feature being tested:
        ring SWX port

    Description:
        Use two pipelines, one acting as producer (pipeline 0) and other acting
		as consumer (pipeline 1). Pipeline 0 will swap the MAC addresses of
		incoming packet and send the packet to pipeline 1. Pipeline 1 will send
		the packet to the link port.

    Verification:
        Received packet will have swapped mac addresses and received on the same
		port.

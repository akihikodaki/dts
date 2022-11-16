
Test Case: test_ring_port_001
-----------------------------

    Feature being tested:
        ring SWX port

    Description:
        Use two pipelines, one acting as producer (pipeline 0) and other acting
		as consumer (pipeline 1). Pipeline 0 will swap the MAC addresses of
		incoming packet and send the packet to pipeline 1. Pipeline 1 will do
		vxlan encapsulation of incoming packet based on the configured rules
		and send it to appropriate port.

    Verification:
        Send a packet to DUT with MAC addresses swapped so that pipeline 1 will
		receive packet hitting the configured rule. Pipeline 1 should act
		appropriately on that packet.

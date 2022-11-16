Test Case: test_learner_013
-----------------------

    Scenario being tested:
        Learner table with key structure type as a metadata, key element alignment as
        contiguous and key size < 64 bytes.

    Description:
        The test case receives Ethernet -> IPv4 -> UDP -> VXLAN -> Ethernet -> IPv4 -> UDP
        packet sequence as an input. The first packet will take the default action and learn
        the respective action. The second packet is resent before the expiration of timeout,
        executing the learnt action.

    Verification:
        The packet verification for the testcase should happen according to the description.
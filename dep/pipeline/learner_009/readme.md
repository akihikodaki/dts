Test Case: test_learner_009
-----------------------

    Scenario being tested:
        The learnt action is not provided with rearm instuction.

    Description:
        The learner table, has timeout configurations as 30,60 and 120 seconds.
        For the first packet, the application expects a miss, a default action will
        be taken place. The default action will add/learn entry with timeout as 60 seconds.
        The default action will transmit packet to port 0.
        The testcase waits for 30 seconds time.
        The same packet is sent again, this time we expect the learnt action to take place.
        The learnt action will transmit the packet to port 1. Even though, the same packet is
        hit, as Rearm instruction is not mentioned in learnt action, the expectation is the timer
        should not be updated.
        The testcase then waits for 40 seconds more to expire the added time. The packet is sent again
        with the expectation of a Miss and a default action course with output port as 0.

    Verification:
        The packet verification for the testcase should happen according to the description.
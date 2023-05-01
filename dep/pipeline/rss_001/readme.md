
Test Case: test_rss_001
-----------------------

    Instruction being tested:
        rss rss_obect_name m.field h.field h.field

    Scenario being tested:
        To verify Receive Side Scaling (RSS) hash algorithm support
        over an n-tuple set of fields read from the packet headers
        by using the "rss" instruction.

    Description:
        Initially, the application is run without providing any RSS
        key. Through, control plane, RSS key is provided and test
        case expect the packet out on Port 0. The RSS key is changed
        from control plane and for the similar packet we expect the
        packet out on Port 1, as RSS computed hash changes.

    Verification:
        Packet verification should happen according to the description.

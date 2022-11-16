
Test Case: test_lpm_004
-----------------------

    Description: Test routing scenarios with LPM match type

        Input packets on ports 0 .. 3:
            IPv4 dest_addr has all bits randomized (mask is 0.0.0.0)

        Expected output packet distribution on ports 0 .. 3:
            Port 0 = 25%
            Port 1 = 25%
            Port 2 = 37.5%
            Port 3 = 12.5%

    Verification
        Actual output packet distribution on output ports 0 .. 3 should match the expected.

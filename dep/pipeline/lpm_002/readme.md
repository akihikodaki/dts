
Test Case: test_lpm_002
-------------------------

    Description: Test routing scenarios with LPM match type

        # Scenario 1
            Input packets on ports 0 .. 3:
                IPv4 dest_addr has all bits randomized (mask is 0.0.0.0)

            Expected output packet distribution on ports 0 .. 3:
                Port 0 = 25%; Port 1 = 25%; Port 2 = 25%; Port 3 = 25%

        # Scenario 2
            Input packets on ports 0 .. 3:
                IPv4 dest_addr has all bits randomized (mask is 0.0.0.0)

            Expected output packet distribution on ports 0 .. 3:
                Port 0 = 50%; Port 1 = 25%; Port 2 = 12.5%; Port 3 = 12.5%

    Verification
        Actual output packet distribution on ports 0 .. 3 should the expected.

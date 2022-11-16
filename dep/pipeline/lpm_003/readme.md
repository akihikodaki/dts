
Test Case: test_lpm_003
-------------------------

    Description: Test routing scenarios with LPM match type

        Input packets on ports 0 .. 3:
            IPv4 dest_addr has all bits randomized (mask is 0.0.0.0)

        Expected output packet distribution on ports 0 .. 3:
            Port 0 = 12.5% + 25%   = 37.5%  (i.e. 3/8 = 6/16)
            Port 1 = 12.5% + 12.5% = 25%    (i.e. 1/4 = 4/16)
            Port 2 = 12.5% + 6.25% = 18.75% (i.e. 3/16)
            Port 3 = 12.5% + 6.25% = 18.75% (i.e. 3/16)

    Verification
        Actual output packet distribution on ports 0 .. 3 should match the expected.

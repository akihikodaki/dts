Test Case: test_learner_017
-----------------------

    Scenario being tested:
        Learner table with key structure type as a metadata, key element alignment as
        non-contiguous and key size < 64 bytes.

    Description:
        The test case is a error-validation scenario. The application should throw a
        'Learner table configuration error' as non-contiguous key alignment in Learner
        table is a non-valid scenario.

    Verification:
        The application should throw an error mentioned in the description.
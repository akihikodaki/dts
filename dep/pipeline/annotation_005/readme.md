Test Case: test_annotation_005
-----------------------

    Scenario being tested:
        The SPEC file contains an action which is annotated as tableonly but used as default in SPEC.

    Verification:
        Application should not run and throw error
        "Error -22 at line xx: Table configuration error."

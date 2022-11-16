Test Case: test_hash_001
-----------------------

    Instruction being tested:
        hash jhash m.field m.field m.field

    Description:
        jhash algorithm is used to calculte the hash.

    Verification:
        Packet is transmitted to the output port on the basis of hash value calculated. last two bits of the hash value
		are used send the packet to a particular port.

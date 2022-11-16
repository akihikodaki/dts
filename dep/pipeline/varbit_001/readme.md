
Test Case: test_profile_001
---------------------------

    Description:
        This illustrates the way to work with variable size headers. The assumed input packet is
        Ethernet/IPv4/UDP, with the IPv4 header containing between 0 and 40 bytes of options. To
        locate the start of the UDP header, the size of the IPv4 header needs to be detected first,
        which is done by reading the first byte of the IPv4 header that carries the 4-bit Internet
        Header Length (IHL) field; this read is done with the "lookahead" instruction, which does
        not advance the extract pointer within the input packet buffer. Once the size of the IPv4
        header options is known for the current packet, the IPv4 header is extracted by using the
        two-argument "extract" instruction. Then the UDP header is extracted and modified.

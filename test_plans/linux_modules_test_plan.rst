.. # BSD LICENSE
    #
    # Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
    # Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions
    # are met:
    #
    #   * Redistributions of source code must retain the above copyright
    #     notice, this list of conditions and the following disclaimer.
    #   * Redistributions in binary form must reproduce the above copyright
    #     notice, this list of conditions and the following disclaimer in
    #     the documentation and/or other materials provided with the
    #     distribution.
    #   * Neither the name of Intel Corporation nor the names of its
    #     contributors may be used to endorse or promote products derived
    #     from this software without specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==================
Linux Driver Tests
==================

This file contains multiple test suites to avoid a single unsupported
kernel module causing the entire test suite to fail. These test suites
cover a variety of kernel modules and are built to check their function
both in use as root and as an unprivileged user. All of the test suites
run the same tests. In the documentation for test cases, <MODULE> will
represent the name of the module being tested. <DEV INTERFACE> will
represent the character interface under /dev/ for the interface.

Prerequisites
=============

There are two prerequisites. First, all of the drivers that you wish
to test must be compiled and installed so that they are available through
modprobe. Secondly, there should be a user on the dut which has the same
password as the primary account for dts. This account will be used as the
unprivileged user, but it still should have permission to lock at least
1 GiB of memory to ensure that it can lock all of the process memory.

Test Suites
===========

There is 1 test suite per module, the modules are as follows:

    * VFIO-PCI
    * UIO PCI GENERIC
    * IGB UIO

Test Case: TX RX
====================
This test case runs as root and is designed to check the basic functioning
of the module. It checks whether packets can be sent and received.

Remove old module ::

    # rmmod <MODULE>

Add the new one ::

    # modprobe <MODULE>

Bind the interface to the driver ::

    # usertools/dpdk-devbind.py --force --bind=<MODULE> xxxx:xx:xx.x

Start testpmd in a loop configuration ::

    # ./<build_target>/app/dpdk-testpmd  -l 1,2 -n 4 -a xxxx:xx:xx.x \
       -- -i --port-topology=loop

Start packet forwarding ::

    testpmd> start

Start a packet capture on the tester::

    # tcpdump -i (interface) ether src (tester mac address)

Send some packets to the dut and check that they are properly sent back into
the packet capture on the tester.

Test Case: TX RX Userspace
==========================
This test case runs as the unprivileged user and is designed to check the
basic functioning of the module. It checks whether packets can be sent
and received when running dpdk applications as a normal user. # means
that a command is run as root. $ means that a command is run as the user.
The igb_uio module requires that the iova mode is in virtual address mode,
which can be done by adding the flag "--iova-mode va" as an eal option to
testpmd.

Remove old module ::

    # rmmod <MODULE>

Add the new one ::

    # modprobe <MODULE>

Bind the interface to the driver ::

    # usertools/dpdk-devbind.py --force --bind=<MODULE> xxxx:xx:xx.x

Grant permissions for all users to access the new character device ::

    # setfacl -m u:dtsunprivilegedtester:rwx <DEV INTERFACE>

Start testpmd in a loop configuration ::

    $ ./<build_target>/app/dpdk-testpmd  -l 1,2 -n 4 -a xxxx:xx:xx.x --in-memory \
       -- -i --port-topology=loop

Start packet forwarding ::

    testpmd> start

Start a packet capture on the tester::

    # tcpdump -i (interface) ether src (tester mac address)

Send some packets to the dut and check that they are properly sent back into
the packet capture on the tester.

Test Case: Hello World
======================
This is a more basic test of functionality as a normal user than the
TX RX Userspace case. It simply involves running a short, hello-world-like
program on each core before shutting down. # means that a command is run
as root. $ means that a command is run as the user. The igb_uio module
requires that the iova mode is in virtual address mode, which can be done
by adding the flag "--iova-mode va" as an eal option to the hello world
application.

Compile the application ::

    make: # cd $RTE_SDK/examples/helloworld && make
    meson: meson configure -Dexamples=helloworld <build_target>;ninja -C <build_target>

Run the application ::

    make: $ $RTE_SDK/examples/helloworld/build/helloworld-shared --in-memory
    meson: $ ./<build_target>/examples/dpdk-helloworld --in-memory

Check for any error states or reported errors.


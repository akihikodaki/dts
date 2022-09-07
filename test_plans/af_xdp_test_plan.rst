.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=========================
DPDK PMD for AF_XDP Tests
=========================

Description
===========

AF_XDP is a socket type that was introduced in kernel 4.18.
It is designed to pass network traffic from the driver in the kernel up to user space
as fast and efficiently as possible, but still abiding by all the usual robustness,
isolation and security properties that Linux provides.

The test plan contains 15 tests, 7 of which are focused on performance and the remaining
8 are focused on validating functionality.

To scale up throughput, one can configure an AF_XDP PMD to use multiple queues.
To configure the underlying network device with multiple queues, use ethtool::

    ethtool -L <interface_name> combined <number_of_queues_desired>

In order for input traffic to be spread among the queues of an interface ensure a scheme
such as Receive Side Scaling (RSS) is in use. Generally, a random traffic profile will
ensure an even spread. More information on RSS can be found here:
https://www.kernel.org/doc/Documentation/networking/scaling.txt

If desired one can also set explicit rules to ensure the spread if the underlying network
device supports it. For example the below will ensure incoming packets with UDP source port
1234 will land on queue 0 and those with port 5678 will land on queue 1::

    ethtool -N eth0 rx-flow-hash udp4 fn
    ethtool -N eth0 flow-type udp4 src-port 1234 dst-port 4242 action 0
    ethtool -N eth0 flow-type udp4 src-port 5678 dst-port 4243 action 1

For each queue in an AF_XDP test there are two pieces of work to consider:

#. The DPDK thread processing the queue (userspace: testpmd application and AF_XDP PMD)
#. The driver thread processing the queue (kernelspace: kernel driver for the NIC)

#1 and #2 can be pinned to either the same core or to separate cores.
Pinning #1 involves using the DPDK EAL parameters '-c' '-l' or '--lcores'.
Pinning #2 involves configuring /proc/irq/<irq_no> where irq_no is the IRQ number associated
with the queue on your device, which can be obtained by querying /proc/interrupts. Some
network devices will have helper scripts available to simplify this process, such as the
set_irq_affinity.sh script which will be referred to in this test plan.

Pinning to separate cores will generally yield better throughput due to more computing
power being available for the packet processing.
When separate cores are used it is suggested that the 'busy_budget=0' argument is added
to the AF_XDP PMD vdev string. This disables the 'preferred busy polling' feature of the
AF_XDP PMD. It is disabled because it only aids performance for single-core tests (app
threads and IRQs pinned to the same core) and as such should be disabled for tests where
the threads and IRQs are pinned to different cores.
When pinning to the same core the busy polling feature is used and along with it the
following netdev configuration options should be set for each netdev in the test::

    echo 2 | sudo tee /sys/class/net/eth0/napi_defer_hard_irqs
    echo 200000 | sudo tee /sys/class/net/eth0/gro_flush_timeout

These settings allow for a user to defer interrupts to be enabled and instead schedule
the NAPI context from a watchdog timer. When the NAPI context is being processed by a
softirq, the softirq NAPI processing will exit early to allow the busy-polling to be
performed. If the application stops performing busy-polling via a system call, the
watchdog timer defined by gro_flush_timeout will timeout, and regular softirq handling
will resume. This all leads to better single-core performance. More information can be
found at:
https://lwn.net/Articles/837010/

The AF_XDP PMD provides two different configurations for a multiple queue test:

#. Single PMD with multiple queues
#. Multiple PMDs each with one or multiple queues.

For example, if an interface is configured with four queues::

    ethtool -L eth0 combined 4

One can configure the PMD(s) in multiple ways, for example:

Single PMD four queues::

    --vdev=net_af_xdp0,iface=eth0,queue_count=4

Two PMDs each with two queues::

    --vdev=net_af_xdp0,iface=eth0,queue_count=2 --vdev=net_af_xdp1,iface=eth0,start_queue=2,queue_count=2

Four PMDs each with one queue::

    --vdev=net_af_xdp0,iface=eth0 --vdev=net_af_xdp1,iface=eth0,start_queue=1 \
    --vdev=net_af_xdp1,iface=eth0,start_queue=2 --vdev=net_af_xdp1,iface=eth0,start_queue=3

The throughput can be measured by issuing the 'show port stats all' command on the testpmd CLI
and taking note of the throughput value::

    testpmd> show port stats all

    ######################## NIC statistics for port 0  ########################
    RX-packets: 31534568   RX-missed: 0          RX-bytes:  1892074080
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 31534504   TX-errors: 0          TX-bytes:  1892070240

    Throughput (since last show)
    Rx-pps:      1967817          Rx-bps:    944552192
    Tx-pps:      1967817          Tx-bps:    944552192
    ############################################################################

To ensure packets were distributed to all queues in a test, use the 'show port xstats all'
interactive testpmd command which will show the distribution. For example in a two-queue test::

    testpmd> show port xstats all
    ###### NIC extended statistics for port 0
    rx_good_packets: 317771192
    tx_good_packets: 317771128
    rx_good_bytes: 19066271520
    tx_good_bytes: 19066267680
    rx_missed_errors: 0
    rx_errors: 0
    tx_errors: 0
    rx_mbuf_allocation_errors: 0
    rx_q0_packets: 158878968
    rx_q0_bytes: 9532738080
    rx_q0_errors: 0
    rx_q1_packets: 158892224
    rx_q1_bytes: 9533533440
    rx_q1_errors: 0
    tx_q0_packets: 158878904
    tx_q0_bytes: 9532734240
    tx_q1_packets: 158892224
    tx_q1_bytes: 9533533440

Above we can see that packets were received on Rx queue 0 (rx_q0_packets) and Rx queue 1
(rx_q1_packets) and transmitted on Tx queue 0 (tx_q0_packets) and Tx queue 1 (tx_q1_packets).

Alternatively if not using testpmd interactive mode, one can display the xstats at a specific
interval by adding the following to their testpmd command line::

    --display-xstats=<xstat_name>,<interval> --stats-period=<interval>

For example to display the statistics for Rx queue 0 and Rx queue 1 every 1s, use::

    --display-xstats=rx_q0_packets,rx_q1_packets,1 --stats-period=1

The functional tests validate the different options available for the AF_XDP PMD which are
decribed in the DPDK documentation:
https://doc.dpdk.org/guides/nics/af_xdp.html#options


Prerequisites
=============

#. Hardware::

    2 Linux network interfaces each connected to a traffic generator port::

    eth0 <---> Traffic Generator Port 0
    eth1 <---> Traffic Generator Port 1

   For optimal performance ensure the interfaces are connected to the same NUMA node as the application
   cores used in the tests. This test plan assumes the interfaces are connected to NUMA node 0 and thatc
   cores 0-8 are also on NUMA node 0.

#. Kernel v5.15 or later with the CONFIG_XDP_SOCKETS option set.

#. libbpf (<=v0.7.0) and libxdp (>=v1.2.2) libraries installed and discoverable via pkg-config::

    pkg-config libbpf --modversion
    pkg-config libxdp --modversion

   The environment variables LIBXDP_OBJECT_PATH and PKG_CONFIG_PATH should be set
   appropriately.
   LIBXDP_OBJECT_PATH should be set to the location of where libxdp placed its bpf
   object files. This is usually in /usr/local/lib/bpf or /usr/local/lib64/bpf.
   PKG_CONFIG_PATH should include the path to where the libxdp and libbpf .pc files
   are located.

#. Build DPDK::

    cd dpdk
    meson --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

#. Method to pin the IRQs for the networking device.
   This test plan assumes an i40e device and as such the set_irq_affinity.sh script will be used.
   The script can be found in the i40e sourceforge project.
   If no script is available for your device, you will need to manually edit /proc/irq/<irq_no>.
   More information can be found here: https://www.kernel.org/doc/html/latest/core-api/irq/irq-affinity.html


Test case 1: perf_one_port_multiqueue_and_same_irqs
===================================================

This test configures one PMD with two queues.
It uses two application cores (0 and 1) and pins the IRQs for each queue to those same cores.

#. Set the hardware queues::

      ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd with two queues::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-2 --no-pci --main-lcore=2 \
      --vdev net_af_xdp0,iface=eth0,queue_count=2 \
      -- -i --a --nb-cores=2 --rxq=2 --txq=2 --forward-mode=macswap

#. Assign the kernel cores::

      ./set_irq_affinity 0-1 eth0

#. Send packets with random IP addresses and different packet sizes from 64 bytes to 1518 bytes by packet generator.
   Check the throughput and ensure packets were distributed to the two queues.

Test case 2: perf_one_port_multiqueue_and_separate_irqs
=======================================================

This test configures one PMD with two queues.
It uses two application cores (2 and 3) and pins the IRQs for each queue to separate non-application cores (0 and 1).

#. Set the hardware queues::

      ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 0 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 0 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd with two queues::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 --no-pci --main-lcore=4 \
      --vdev net_af_xdp0,iface=eth0,queue_count=2,busy_budget=0 \
      --log-level=pmd.net.af_xdp:8 \
      -- -i --a --nb-cores=2 --rxq=2 --txq=2 --forward-mode=macswap

#. Assign the kernel cores::

      ./set_irq_affinity 0-1 eth0

#. Send packets with random IP addresses and different packet sizes from 64 bytes to 1518 bytes by packet generator.
   Check the throughput and ensure packets were distributed to the two queues.

Test case 3: perf_one_port_multiqueues_with_two_vdev
====================================================

This test configures two PMDs each with four queues.
It uses eight application cores (0 to 7) and pins the IRQs for each queue to those same cores.

#. Set the hardware queues::

      ethtool -L eth0 combined 8

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-8 --no-pci --main-lcore=8 \
    --vdev net_af_xdp0,iface=eth0,queue_count=4 \
    --vdev net_af_xdp1,iface=eth0,start_queue=4,queue_count=4 \
    --log-level=pmd.net.af_xdp:8 \
    -- -i -a --nb-cores=8 --rxq=4 --txq=4 --forward-mode=macswap

#. Assign the kernel cores::

    ./set_irq_affinity 0-7 eth0

#. Send packets with random IP addresses and different packet sizes from 64 bytes to 1518 bytes by packet generator.
   Check the throughput and ensure packets were distributed to the eight queues.

Test case 4: perf_one_port_single_queue_and_separate_irqs
=========================================================

This test configures one PMD with one queue.
It uses one application core (1) and pins the IRQs for the queue to a separate non-application core (0).

#. Set the hardware queues::

      ethtool -L eth0 combined 1

#. Configure busy polling settings::

      echo 0 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 0 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 --no-pci --main-lcore=2 \
    --vdev net_af_xdp0,iface=eth0,queue_count=1,busy_budget=0 \
    --log-level=pmd.net.af_xdp:8 \
    -- -i -a --nb-cores=1 --rxq=1 --txq=1 --forward-mode=macswap

#. Assign the kernel core::

    ./set_irq_affinity 0 eth0

#. Send packets with random IP addresses and different packet sizes from 64 bytes to 1518 bytes by packet generator.
   Check the throughput and ensure packets were distributed to the queue.

Test case 5: perf_one_port_single_queue_with_two_vdev
=====================================================

This test configures two PMDs each with one queue.
It uses two application cores (2 and 3) and pins the IRQs for each queue to separate non-application cores (0 and 1).

#. Set the hardware queues::

      ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 0 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 0 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 --no-pci --main-lcore=4 \
    --vdev net_af_xdp0,iface=eth0,queue_count=1,busy_budget=0 \
    --vdev net_af_xdp1,iface=eth0,start_queue=1,queue_count=1,busy_budget=0 \
    --log-level=pmd.net.af_xdp:8 \
    -- -i -a --nb-cores=2 --rxq=1 --txq=1 --forward-mode=macswap

#. Assign the kernel cores::

    ./set_irq_affinity 0-1 eth0

#. Send packets with random IP addresses and different packet sizes from 64 bytes to 1518 bytes by packet generator.
   Check the throughput and ensure packets were distributed to the two queues.


Test case 6: perf_two_port_and_same_irqs
========================================

This test configures two PMDs each with one queue from different interfaces (eth0 and eth1).
It uses two application cores (0 and 1) and pins the IRQs for each queue to those same cores.

#. Set the hardware queues::

    ethtool -L eth0 combined 1
    ethtool -L eth1 combined 1

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout
      echo 2 >> /sys/class/net/eth1/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth1/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 0-2 --no-pci --main-lcore=2  \
    --vdev net_af_xdp0,iface=eth0 --vdev net_af_xdp1,iface=eth1 \
    --log-level=pmd.net.af_xdp:8 \
    -- -i --a --nb-cores=2 --rxq=1 --txq=1 --forward-mode=macswap

#. Assign the kernel cores::

    ./set_irq_affinity 0 eth0
    ./set_irq_affinity 1 eth1

#. Send packets with random IP addresses and different packet sizes from 64 bytes to 1518 bytes by packet generator to both ports.
   Check the throughput and ensure packets were distributed to the queue on each port.


Test case 7: perf_two_port_and_separate_irqs
============================================

This test configures two PMDs each with one queue from different interfaces (eth0 and eth1).
It uses two application cores (2 and 3) and pins the IRQs for each queue to separate non-application cores (0 and 1).

#. Set the hardware queues::

    ethtool -L eth0 combined 1
    ethtool -L eth1 combined 1

#. Configure busy polling settings::

      echo 0 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 0 >> /sys/class/net/eth0/gro_flush_timeout
      echo 0 >> /sys/class/net/eth1/napi_defer_hard_irqs
      echo 0 >> /sys/class/net/eth1/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-4 --no-pci --main-lcore=4 \
    --vdev net_af_xdp0,iface=eth0,busy_budget=0 \
    --vdev net_af_xdp1,iface=eth1,busy_budget=0 \
    --log-level=pmd.net.af_xdp:8 \
    -- -i --a --nb-cores=2 --rxq=1 --txq=1 --forward-mode=macswap

#. Assign the kernel cores::

    ./set_irq_affinity 0 eth0
    ./set_irq_affinity 1 eth1

#. Send packets with random IP addresses and different packet sizes from 64 bytes to 1518 bytes by packet generator to both ports.
   Check the throughput and ensure packets were distributed to the queue on each port.


Test case 8: func_start_queue
=============================
This test creates a socket on a queue other than the default queue (0) and verifies that packets land on it.

#. Set the hardware queues::

    ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --no-pci \
    --log-level=pmd.net.af_xdp,debug \
    --vdev=net_af_xdp0,iface=eth0,start_queue=1 \
    --forward-mode=macswap

#. Send packets with random IP addresses by packet generator.
   Ensure packets were distributed to the queue.


Test case 9: func_queue_count
=============================
This test creates a socket on 2 queues (0 and 1) and verifies that packets land on both of them.

#. Set the hardware queues::

    ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --no-pci \
    --log-level=pmd.net.af_xdp,debug \
    --vdev=net_af_xdp0,iface=eth0,queue_count=2 -- --rxq=2 --txq=2 \
    --forward-mode=macswap

#. Send packets with random IP addresses by packet generator.
   Ensure packets were distributed to the two queues.


Test case 10: func_shared_umem_1pmd
===================================
This test makes the UMEM 'shared' between two sockets using one PMD and verifies that packets land on both of them.

#. Set the hardware queues::

    ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --no-pci \
    --log-level=pmd.net.af_xdp,debug \
    --vdev=net_af_xdp0,iface=eth0,queue_count=2,shared_umem=1 \
    -- --rxq=2 --txq=2 \
    --forward-mode=macswap

#. Check for the log ``eth0,qid1 sharing UMEM``

#. Send packets with random IP addresses by packet generator.
   Ensure packets were distributed to the queue.


Test case 11: func_shared_umem_2pmd
===================================
This test makes the UMEM 'shared' between two sockets using two PMDs and verifies that packets land on both of them.

#. Set the hardware queues::

    ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --no-pci \
    --vdev=net_af_xdp0,iface=eth0,shared_umem=1 \
    --vdev=net_af_xdp1,iface=eth0,start_queue=1,shared_umem=1 \
    --log-level=pmd.net.af_xdp,debug \
    --forward-mode=macswap

#. Check for the log ``eth0,qid1 sharing UMEM``

#. Send packets with random IP addresses by packet generator.
   Ensure packets were distributed to the two queues.


Test case 12: func_busy_budget
==============================
This test configures the busy polling budget to 0 which disables busy polling and verifies that packets land on the socket.

#. Set the hardware queues::

    ethtool -L eth0 combined 1

#. Configure busy polling settings::

      echo 0 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 0 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --no-pci \
    --vdev=net_af_xdp0,iface=eth0,busy_budget=0 \
    --log-level=pmd.net.af_xdp,debug \
    --forward-mode=macswap

#. Check for the log ``Preferred busy polling not enabled``

#. Send packets with random IP addresses by packet generator.
   Ensure packets were distributed to the queue.


Test case 13: func_xdp_prog
===========================
This test loads a custom xdp program on the network interface, rather than using the default program that comes packaged with libbpf/libxdp.

#. Create a file `xdp_example.c` with the following contents::

    #include <linux/bpf.h>
    #include <bpf/bpf_helpers.h>

    struct bpf_map_def SEC("maps") xsks_map = {
            .type = BPF_MAP_TYPE_XSKMAP,
            .max_entries = 64,
            .key_size = sizeof(int),
            .value_size = sizeof(int),
    };

    static unsigned int idx;

    SEC("xdp-example")

    int xdp_sock_prog(struct xdp_md *ctx)
    {
            int index = ctx->rx_queue_index;

            /* Drop every other packet */
            if (idx++ % 2)
                    return XDP_DROP;
            else
                    return bpf_redirect_map(&xsks_map, index, XDP_PASS);
    }

#. Compile the program::

    clang -O2 -Wall -target bpf -c xdp_example.c -o xdp_example.o

#. Set the hardware queues::

    ethtool -L eth0 combined 1

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --no-pci \
    --vdev=net_af_xdp0,iface=eth0,xdp_prog=xdp_example.o \
    --log-level=pmd.net.af_xdp,debug \
    --forward-mode=macswap

#. Check for the log ``Successfully loaded XDP program xdp_example.o with fd <fd>``

#. Send packets with random IP addresses by packet generator.
   Ensure some packets were distributed to the queue.


Test case 14: func_xdp_prog_mq
==============================
This test loads a custom xdp program on the network interface with two queues and then creates a PMD with sockets on those two queues.
It assumes the custom program compilation outlined in the previous test has been completed.

#. Set the hardware queues::

    ethtool -L eth0 combined 2

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --no-pci \
    --vdev=net_af_xdp0,iface=eth0,xdp_prog=xdp_example.o,queue_count=2 \
    --log-level=pmd.net.af_xdp,debug -- \
    --rxq=2 --txq=2 \
    --forward-mode=macswap

#. Check for the log ``Successfully loaded XDP program xdp_example.o with fd <fd>``

#. Send packets with random IP addresses by packet generator.
   Ensure some packets were distributed to the two queues.


Test case 15: func_secondary_prog
=================================
This test launches two processes - a primary and a secondary DPDK process.
It verifies that the secondary process can communicate with the primary by running the "show port info all" command in the secondary and ensuring that the port info matches that of the PMD in the primary process.

#. Set the hardware queues::

    ethtool -L eth0 combined 1

#. Configure busy polling settings::

      echo 2 >> /sys/class/net/eth0/napi_defer_hard_irqs
      echo 200000 >> /sys/class/net/eth0/gro_flush_timeout

#. Start testpmd (primary)::

    /root/dpdk/build/app/dpdk-testpmd --no-pci \
    --vdev=net_af_xdp0,iface=eth0 \
    --log-level=pmd.net.af_xdp,debug \
    -- --forward-mode=macswap -a -i

#. Start testpmd (secondary)::

    /root/dpdk/build/app/dpdk-testpmd --no-pci \
    --proc-type=auto \
    --log-level=pmd.net.af_xdp,debug \
    -- -i -a

#. execute the CLI command ``show port info all`` in the secondary process and ensure that you can see the port info of the net_af_xdp0 PMD from the primary process.
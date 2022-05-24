.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

============================================
DPDK Telemetry API Tests
============================================

This test for Telemetry API  for Service Assurance can be run on linux userspace.
The application which initializes packet forwarding will act as the server, sending metrics
to the requesting application which acts as the client.

In DPDK, applications can be used to initialize the ``telemetry`` as a virtual device.
To view incoming traffic on featured ports, the application should be run first (ie. after
ports are configured).Once the application is running, the service assurance agent
(for example the collectd plugin) should be run to begin querying the API.

A client connects their Service Assurance application to the DPDK application via a UNIX
socket. Once a connection is established,a client can send JSON messages to the DPDK
application requesting metrics via another UNIX client.This request is then handled and parsed
if valid. The response is then formatted in JSON and sent back to the requesting client

Hardwares::
------------
I40E driver NIC  or ixgbe driver NIC

Prerequisites
=============

1. Enable the telemetry API by modifying the following config option before building DPDK::

	Python >= 2.5
	Jansson library for JSON serialization, libjansson should be available
	RTE_LIB_TELEMETRY is 1 by default in <build_target>/rte_build_config.h:
	  #define RTE_LIB_TELEMETRY 1

    Build DPDK:
    CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
    ninja -C <build_target>

2. Configiure PF

	modprobe uio;
	insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko;

3.   Launch testpmd as the primary application with the ``telemetry``
	./<build_target>/app/dpdk-testpmd --telemetry

4.   Launch the ``telemetry`` python script with a client filepath :

	 python usertools/dpdk-telemetry-client.py /var/run/some_client

5. Build should include both  make and mesion static/shared

	For meson build -return to DPDK directory and create a meson folder:
	cd build
	ninja
	This will compile DPDK via the meson build system
	For make build is normal build

Test case: basic connection for testpmd and telemetry client::
==================================================================

1. bind two ports and build

  $./usertools/dpdk-devbind.py --bind=igb_uio 18:00.0 18:00.1

2. Run Testpmd with 2 ports

  $ ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c f -n 4  --telemetry -- -i

   For the building meson shared and make shared . tested command should be used  when run on ubuntu OS
   make share and meson version::
   $ ./<build_target>/app/dpdk-testpmd  -c f -n 4 -d librte_mempool_ring.so -d librte_telemetry.so --telemetry --socket-mem=1024,1024 -- -i

 3.Run Python terminal:
	python dpdk-telemetry-client.py
	enter 1/2/ :

 4. check and verify any error show on testpmd

Test case:  Stats of 2 ports for testpmd and telemetry with same type nic
=======================================================================================

1.bind two ports
  $./usertools/dpdk-devbind.py --bind=igb_uio 18:00.0 18:00.1

2. Run Testpmd with 2 ports

  $ ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --telemetry  -- -i

3.Run Python terminal:

	python ./usertools/dpdk-telemetry-client.py
	enter 1/2/ :

4.check and verify any error show on testpmd

5.set rx/tx configration by testpmd

	testpmd-> stop
	testpmd> show port xstats all

6. telemetry client ,enter 1/2

7. check  the xstats all and  the metrics be displayed on the client terminal in JSON format

	a.	Ensure # of ports stats being returned == # of ports
	b.	Ensure packet counts (eg rx_good_packets) is 0
	c.   Ensure extended NIC stats are shown (depends on PMD used for testing, refer to ixgbe/i40e tests for PMD xstats)
	d.	Ensure extended NIC stats are 0 (eg: rx_q0_packets == 0)

Test case:  Stats of 2 ports for testpmd and telemetry with different  type nic
=======================================================================================

1.bind two ports
  $./usertools/dpdk-devbind.py --bind=igb_uio 18:00.0 88:00.1

2. Run Testpmd with 2 ports

  $ ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --telemetry  -- -i

3.Run Python terminal:

	python ./usertools/dpdk-telemetry-client.py
	enter 1/2/ :

4.check and verify any error show on testpmd

5.set rx/tx configration by testpmd

	testpmd-> stop
	testpmd> show port xstats all

6. telemetry client ,enter 1/2

7. check  the xstats all and  the metrics be displayed on the client terminal in JSON format

	a.	Ensure # of ports stats being returned == # of ports
	b.	Ensure packet counts (eg rx_good_packets) is 0
	c.   Ensure extended NIC stats are shown (depends on PMD used for testing, refer to ixgbe/i40e tests for PMD xstats)
	d.	Ensure extended NIC stats are 0 (eg: rx_q0_packets == 0)

Test case:  Stats of 4 ports for testpmd and telemetry with same type nic
=======================================================================================

1.bind two ports
  $./usertools/dpdk-devbind.py --bind=igb_uio 18:00.0 18:00.1 b1:00.0 b1:00.1

2. Run Testpmd with 2 ports

  $ ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --telemetry  -- -i

3.Run Python terminal:

	python ./usertools/dpdk-telemetry-client.py
	enter 1/2/

4.check and verify any error show on testpmd

5.set rx/tx configration by testpmd

	testpmd-> stop
	testpmd> show port xstats all

6. telemetry client ,enter 1/2

7. check  the xstats all and  the metrics be displayed on the client terminal in JSON format

	a.	Ensure # of ports stats being returned == # of ports
	b.	Ensure packet counts (eg rx_good_packets) is 0
	c.   Ensure extended NIC stats are shown (depends on PMD used for testing, refer to ixgbe/i40e tests for PMD xstats)
	d.	Ensure extended NIC stats are 0 (eg: rx_q0_packets == 0)

Test case:  Stats of 4 ports for testpmd and telemetry with different  type nic
=======================================================================================

1.bind two ports
  $./usertools/dpdk-devbind.py --bind=igb_uio 18:00.0 18.00.1 88:00.0 88:00.1

2. Run Testpmd with 2 ports

  $ ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --telemetry  -- -i

3.Run Python terminal:

	python ./usertools/dpdk-telemetry-client.py
	enter 1/2/ :

4.check and verify any error show on testpmd

5.set rx/tx configration by testpmd

	testpmd-> stop
	testpmd> show port xstats all

6. telemetry client ,enter 1/2

7. check  the xstats all and  the metrics be displayed on the client terminal in JSON format

	a.	Ensure # of ports stats being returned == # of ports
	b.	Ensure packet counts (eg rx_good_packets) is 0
	c.   Ensure extended NIC stats are shown (depends on PMD used for testing, refer to ixgbe/i40e tests for PMD xstats)
	d.	Ensure extended NIC stats are 0 (eg: rx_q0_packets == 0)
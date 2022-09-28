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

Test case: read nic Laser Power via dpdk
========================================

1.Bind ports to dpdk::

      ./usertools/dpdk-devbind.py --bind=vfio-pci 18:00.0 18.00.1

2.Launch the dpdk testpmd with teltmetry::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --telemetry  -- -i

3.Launch the telemetry client::

      python ./usertools/dpdk-telemetry.py

4.Excute command in telemtry client::

      --> /ethdev/module_eeprom,<port number>

      take a example:/ethdev/module_eeprom,0
      {"/ethdev/module_eeprom": {"Identifier": "0x03 (SFP)", "Extended identifier": "0x04 (GBIC/SFP defined by 2-wire
       interface ID)", "Connector": "0x07 (LC)", "Transceiver codes": "0x10 0x00 0x00 0x01 0x00 0x00 0x00 0x00 0x00",
        "Transceiver type": "10G Ethernet: 10G Base-SR; Ethernet: 1000BASE-SX", "Encoding": "0x06 (64B/66B)", "BR,
        Nominal": "10300MBd", "Rate identifier": "0x00 (unspecified)", "Length (SMF,km)": "0km", "Length (SMF)":
        "0m", "Length (50um)": "80m", "Length (62.5um)": "30m", "Length (Copper)": "0m", "Length (OM3)": "300m",
        "Laser wavelength": "850nm", "Vendor name": "Intel Corp", "Vendor OUI": "00:1b:21", "Vendor PN":
        "AFBR-703SDZ-IN2", "Vendor rev": "G2.3", "Option values": "0x00 0x3a", "Option": "RX_LOS implemented;
        TX_FAULT implemented; TX_DISABLE implemented; RATE_SELECT implemented", "BR margin, max": "0%", "BR margin,
        min": "0%", "Vendor SN": "AD1345A04JR", "Date code": "131108", "Optical diagnostics support": "Yes", "Laser
        bias current": "5.942 mA", "Laser output power": "0.6703 mW / -1.74 dBm", "Receiver signal average optical
        power": "0.8002 mW / -0.97 dBm", "Module temperature": "38.50 degrees C / 101.30 degrees F", "Module
        voltage": "3.3960 V", "Alarm/warning flags implemented": "Yes", "Laser bias current high alarm": "Off",
        "Laser bias current low alarm": "Off", "Laser bias current high warning": "Off", "Laser bias current low
        warning": "Off", "Laser output power high alarm": "Off", "Laser output power low alarm": "Off", "Laser output
        power high warning": "Off", "Laser output power low warning": "Off", "Module temperature high alarm": "Off",
        "Module temperature low alarm": "Off", "Module temperature high warning": "Off", "Module temperature low
        warning": "Off", "Module voltage high alarm": "Off", "Module voltage low alarm": "Off", "Module voltage
        high warning": "Off", "Module voltage low warning": "Off", "Laser rx power high alarm": "Off", "Laser rx
        power low alarm": "Off", "Laser rx power high warning": "On", "Laser rx power low warning": "Off", "Laser
        bias current high alarm threshold": "10.500 mA", "Laser bias current low alarm threshold": "2.500 mA",
        "Laser bias current high warning threshold": "10.500 mA", "Laser bias current low warning threshold": "2
        .500 mA", "Laser output power high alarm threshold": "2.0000 mW / 3.01 dBm", "Laser output power low alarm
        threshold": "0.0600 mW / -12.22 dBm", "Laser output power high warning threshold": "0.7900 mW / -1.02 dBm",
        "Laser output power low warning threshold": "0.0850 mW / -10.71 dBm", "Module temperature high alarm
        threshold": "85.00 degrees C / 185.00 degrees F", "Module temperature low alarm threshold": "-5.00 degrees
        C / 23.00 degrees F", "Module temperature high warning threshold": "80.00 degrees C / 176.00 degrees F",
        "Module temperature low warning threshold": "0.00 degrees C / 32.00 degrees F", "Module voltage high
        alarm threshold": "3.6000 V", "Module voltage low alarm threshold": "3.1300 V", "Module voltage high
        warning threshold": "3.4600 V", "Laser rx power high alarm threshold": "2.0000 mW / 3.01 dBm", "Laser rx
        power low alarm threshold": "0.0000 mW / -inf dBm", "Laser rx power high warning threshold": "0.7900 mW /
        -1.02 dBm", "Laser rx power low warning threshold": "0.0200 mW / -16.99 dBm"}}

5.check the testpmd and telemetry show info same as 'ethtool -m'::

      ethtool -m ens25f1 | grep 'Laser output power'
      Laser output power                        : 0.6703 mW / -1.74 dBm

.. note::

   refer to command 'ethtool -m' of ethtool v5.4

Test case: check Laser Power in different optical modules
=========================================================

1.set port 0 and port 1 with diffent optical modules

2.Launch the dpdk testpmd with teltmetry::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --telemetry  -- -i

3.Launch the telemetry client::

      python ./usertools/dpdk-telemetry.py

4.Excute command in telemtry client::

      --> /ethdev/module_eeprom,0
      --> /ethdev/module_eeprom,1

5.check port 0 and port 1 have different Laser Power

Test case: check Laser Power in same optical modules
====================================================

1.set port 0 and port 1 with same optical modules

2.Launch the dpdk testpmd with teltmetry::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --telemetry  -- -i

3.Launch the telemetry client::

      python ./usertools/dpdk-telemetry.py

4.Excute command in telemtry client::

      --> /ethdev/module_eeprom,0
      --> /ethdev/module_eeprom,1

5.check port 0 and port 1 have same Laser Power

.. note::

   the laser power will change slightly with the voltage and temperature

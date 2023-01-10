.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

=======================
Userspace Ethtool Tests
=======================

This feature is designed to provide one rte_ethtool shim layer based on
rte_ethdev API. The Ethtool sample application shows an implementation
of an ethtool-like API and provides a console environment that allows
its use to query and change Ethernet card parameters. The Ethtool sample
is based upon a simple L2 frame reflector.

Prerequisites
=============

notice: On Intel® Ethernet 700 Series, test case "test_dump_driver_info"
need a physical link disconnect, this case must do manually at this condition.

Assume port 0 and 1 are connected to the traffic generator, to run the test
application in linux app environment with 4 lcores, 2 ports::

    ethtool -c f -n 4

The sample should be validated on Intel® Ethernet 700 Series, Intel® Ethernet 800 Series, 82599 and i350 Nics.

other requirements:

#. igxbe driver (version >= 4.3.13).
#. ethtool of linux is the default reference tool.
#. md5sum is a tool to do dumped bin format file comparison.
#. insert two nic cards on No.0 socket

Test Case: Dump driver information test
=======================================

User "drvinfo" command to dump driver information and then check that
dumped information, which are dumped separately by dpdk's ethtool and
linux's ethtool, were exactly the same::

    EthApp> drvinfo
    Port 0 driver: net_ixgbe (ver: DPDK 17.02.0-rc0)
    bus-info: 0000:84:00.0
    firmware-version: 0x61bf0001
    Port 1 driver: net_ixgbe (ver: DPDK 17.02.0-rc0)
    bus-info: 0000:84:00.1
    firmware-version: 0x61bf0001

Use "link" command to dump all ports link status.
Notice:: On Intel® Ethernet 700 Series, link detect need a physical link disconnect::

    EthApp> link
    Port 0: Up
    Port 1: Up

Change tester port link status to down and re-check link status::

    EthApp> link
    Port 0: Down
    Port 1: Down

Send a few packets to l2fwd and check that command "portstats" dumps correct
port statistics::

    EthApp> portstats 0
    Port 0 stats
       In: 1 (64 bytes)
      Out: 1 (64 bytes)

Test Case: Retrieve eeprom test
===============================

Unbind ports from igb_uio and bind them to default driver.
Dump eeprom binary by linux's ethtool and dpdk's ethtool separately::

   ethtool --eeprom-dump INTF_0 raw on > ethtool_eeprom_0.bin
   ethtool --eeprom-dump INTF_1 raw on > ethtool_eeprom_1.bin

.. note::
   In case on ixgbe NIC to read the eeprom, please use 'length' parameter to reduce size to 0x4000.
   For example: ethtool --eeprom-dump {INTF} length 0x4000.

Retrieve eeprom on specified port using dpdk's ethtool and
compare csum with the file dumped by ethtool::

    EthApp> eeprom 0 eeprom_0.bin
    EthApp> eeprom 1 eeprom_1.bin

    md5sum ethtool_eeprom_0.bin
    md5sum eeprom_0.bin

compare md5sum value of the two bin files.

Test Case: Retrieve register test
=================================

Retrieve register on specified port::

    EthApp> regs 0 reg_0.bin
    EthApp> regs 1 reg_1.bin

Unbind ports from igb_uio and bind them to default driver::

    dpdk/tools/dpdk_nic_bind.py --bind=ixgbe x:xx.x

Check that dumped register information is correct::

   ethtool -d INTF_0 raw off file reg_0.bin
   ethtool -d INTF_1 raw off file reg_0.bin

Test Case: Ring param test
==========================

Dump port 0 ring size by ringparam command and check numbers are correct::

   EthApp> ringparam  0
   Port 0 ring parameters
     Rx Pending: 128 (256 max)
     Tx Pending: 4096 (4096 max)

Change port 0 ring size by ringparam command and then verify Rx/Tx function::

   EthApp> ringparam  0 256 2048

Recheck ring size by ringparam command::

   EthApp> ringparam  0
   Port 0 ring parameters
     Rx Pending: 256 (256 max)
     Tx Pending: 2048 (4096 max)

send packet by scapy on Tester::

   check tx/rx packets
   EthApp>  portstats 0

Test Case: Mac address test
===========================
Use "macaddr" command to dump port mac address and then check that dumped
information is exactly the same as ifconfig do.

set a new mac address by dpdk's ethtool, send and sniff packet and check packet
forwarded status::

    EthApp> macaddr 0
    Port 0 MAC Address: XX:XX:XX:XX:XX:XX
    EthApp> macaddr 1
    Port 1 MAC Address: YY:YY:YY:YY:YY:YY

Check multicast macaddress will not be validated.::

    EthApp> validate 01:00:00:00:00:00
    Address is not unicast

Check all zero macaddress will not be validated::

    EthApp> validate 00:00:00:00:00:00
    Address is not unicast

Use "macaddr" command to change port mac address and then check mac changed::

    EthApp> validate 00:10:00:00:00:00
    Address is unicast

    EthApp> macaddr 0 00:10:00:00:00:00
    MAC address changed
    EthApp> macaddr 0
    Port 0 MAC Address: 00:10:00:00:00:00

Verified mac address in forwarded packets has been changed.

Test Case: Port config test
===========================
Use "stop" command to stop port0. Send packets to port0 and verify no packet
received::

    EthApp> stop 0

Use "open" command to re-enable port0. Send packets to port0 and verify
packets received and forwarded::

    EthApp> open 0

Test case: Mtu config test
==========================
Use "mtu" command to change port 0 mtu from default 1519 to 9000 on Tester's port.

Send packet size over 1519 and check that packet will be detected as error::

    EthApp> mtu 0 1519
    Port 0 stats
       In: 0 (0 bytes)
      Out: 0 (0 bytes)
      Err: 1

Change mtu to default value and send packet size over 1519 and check that
packet will normally be received.

Test Case: Pause tx/rx test(performance test)
=============================================

Enable port 0 Rx pause frame and then create two packets flows on IXIA port.
One flow is 100000 normally packet and the second flow is pause frame.
Check that dut's port 0 Rx speed dropped status. For example, 82599 will drop
from 14.8Mpps to 7.49Mpps::

    EthApp> pause 0 rx

Use "pause" command to print dut's port pause status, check that dut's port 0 rx
has been paused::

    EthApp> pause 0
    Port 0: Rx Paused

Release pause status of port 0 rx and then restart port 0, check that packets Rx
speed is normal::

    EthApp> pause 0 none
    EthApp>

Pause port 0 TX pause frame::

    EthApp> pause 0 tx

Use "pause" command to print port pause status, check that port 0 tx has been
paused::

    EthApp> pause 0
    Port 0: Tx Paused

Enable flow control in IXIA port and send packets from IXIA with line rate.
Record line rate before send packet.
Check that IXIA receive flow control packets and IXIA transmit speed dropped.
IXIA Rx packets more then Tx packets to check that received pause frame.Compare
the line rates in the time before and after the Pause packets are injected

Unpause port 0 tx and restart port 0. Then send packets to port0, check that
packets forwarded normally from port 0::

    EthApp> pause 0 none
    EthApp> stop 0
    EthApp> open 0

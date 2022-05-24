.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

============================================
Sample Application Tests: Keep Alive Example
============================================

The Keep Alive application is a simple example of a heartbeat/watchdog for packet processing cores. It demonstrates how to detect ‘failed’ DPDK cores and notify a fault management entity of this failure. Its purpose is to ensure the failure of the core does not result in a fault that is not detectable by a management entity.

Overview
========

The application demonstrates how to protect against ‘silent outages’ on packet processing cores. A Keep Alive Monitor Agent Core (master) monitors the state of packet processing cores (worker cores) by dispatching pings at a regular time interval (default is 5ms) and monitoring the state of the cores. Cores states are: Alive, MIA, Dead or Buried. MIA indicates a missed ping, and Dead indicates two missed pings within the specified time interval. When a core is Dead, a callback function is invoked to restart the packet processing core; A real life application might use this callback function to notify a higher level fault management entity of the core failure in order to take the appropriate corrective action.

Note: Only the worker cores are monitored. A local (on the host) mechanism or agent to supervise the Keep Alive Monitor Agent Core DPDK core is required to detect its failure.

Note: This application is based on the L2 Forwarding Sample Application (in Real and Virtualized Environments). As such, the initialization and run-time paths are very similar to those of the L2 forwarding application.

Compiling the Application
=========================

To compile the application:
See the DPDK Getting Started Guide for possible RTE_TARGET values.
Build the application::

   meson configure -Dexamples=l2fwd-keepalive x86_64-native-linuxapp-gcc
   ninja -C x86_64-native-linuxapp-gcc

Running the Application
=======================

The application has a number of command line options::

   ./<build_target>/examples/dpdk-l2fwd-keepalive [EAL options] -- -p PORTMASK [-q NQ] [-K PERIOD] [-T PERIOD]

where,

* p PORTMASK: A hexadecimal bitmask of the ports to configure
* q NQ: A number of queues (=ports) per lcore (default is 1)
* K PERIOD: Heartbeat check period in ms(5ms default; 86400 max)
* T PERIOD: statistics will be refreshed each PERIOD seconds (0 to disable, 10 default, 86400 maximum).

To run the application in linuxapp environment with 4 lcores, 16 ports 8 RX queues per lcore and a ping interval of 10ms, issue the command::

    ./<build_target>/examples/dpdk-l2fwd-keepalive -c f -n 4 -- -q 8 -p ffff -K 10

Refer to the DPDK Getting Started Guide for general information on running applications and the Environment Abstraction Layer (EAL) options.

.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2011-2019 Intel Corporation

==================
QoS Metering Tests
==================
The QoS meter sample application is an example that demonstrates the use of
DPDK to provide QoS marking and metering, as defined by RFC2697 for Single
Rate Three Color Marker (srTCM) and RFC 2698 for Two Rate Three Color
Marker (trTCM) algorithm.

The detailed description of the application items and mode can be found in
https://doc.dpdk.org/guides/sample_app_ug/qos_metering.html

Prerequisites
=============
The DUT must have two 10G Ethernet ports connected to two ports of IXIA.

Assume two DUT 10G Ethernet ports' pci device id is as the following,

dut_port_0 : "0000:05:00.0"
dut_port_1 : "0000:05:00.1"

1. Compile DPDK and sample

2. Bind two ports to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1

3. The default metering mode is defined in dpdk/examples/qos_meter/main.c::

    #define APP_MODE        APP_MODE_SRTCM_COLOR_BLIND

   The input color of packets depends on the value "APP_PKT_COLOR_POS",
   which is defined in dpdk/examples/qos_meter/main.c too::

    #define APP_PKT_COLOR_POS               5

   The change will descripted in each case.

4. The policy table is defined in dpdk/examples/qos_meter/main.h::

    policer_table[RTE_COLORS][RTE_COLORS] =
    {
        { GREEN, RED, RED},
        { DROP, YELLOW, RED},
        { DROP, DROP, RED}
    };

   In which::

    GREEN = 0; YELLOW = 1; RED = 2; DROP = 3.

   So the policy action is decided by input_color and output_color.

5. The application is constrained to use a single core in the EAL core mask
   and 2 ports only in the application port mask (first port from the port
   mask is used for RX and the other port in the core mask is used for TX)::

    ./<build_target>/examples/dpdk-qos_meter -c 1 -n 4 -- -p 0x3

Test Case: srTCM blind input color RED
======================================
1. The input color of packets depends on the value "APP_PKT_COLOR_POS".
   The default value is 5, caculate the input_color is "RED"

2. Use the default setting, the packets are 64 bytes Ethernet frames,
   and the metering mode is srTCM blind.
   Assuming the input traffic is generated at line rate and all packets
   are 64 bytes Ethernet frames (IPv4 packet size of 46 bytes) and green,
   the expected output traffic should be marked as shown in the following
   table:

   +-------------+--------------+---------------+------------+
   |     Mode    | Green (Mpps) | Yellow (Mpps) | Red (Mpps) |
   +-------------+--------------+---------------+------------+
   | srTCM blind | 1            | 1             | 12.88      |
   +-------------+------------------------------+------------+
   | srTCM color | 1            | 1             | 12.88      |
   +-------------+------------------------------+------------+
   | trTCM blind | 1            | 0.5           | 13.38      |
   +-------------+------------------------------+------------+
   | trTCM color | 1            | 0.5           | 13.38      |
   +-------------+------------------------------+------------+
   |     FWD     | 14.88        | 0             | 0          |
   +-------------+------------------------------+------------+

   The data is caculated by "cir = 1000000 * 46, .cbs = 2048, .ebs = 2048".
   The linerate is 14.88Mpps, 1Mpps packets output_color are marked Green,
   13.88Mpps packets output_color are marked Red and Yellow.
   mapping the policer_table[2][0](DROP), policer_table[2][1](YELLOW)
   and policer_table[2][2](RED).
   So the valid frames received on the peer IXIA port is 13.88(Mpps).

Test Case: srTCM blind input color GREEN
========================================
1. The input color of packets depends on the value "APP_PKT_COLOR_POS".
   Set::

    #define APP_PKT_COLOR_POS               3

   Caculate the input_color is "GREEN".

2. Use the default setting, the packets are 64 bytes Ethernet frames,
   and the metering mode is srTCM blind.
   All the packets are mapped to the first row policer_table[0][0](GREEN),
   and policer_table[0][1](RED) and policer_table[0][2](RED).
   So the valid frames received on the peer IXIA port is 14.88(Mpps).

Test Case: srTCM aware input color RED
======================================
1. The input color of packets depends on the value "APP_PKT_COLOR_POS".
   Set::

    #define APP_PKT_COLOR_POS               5

   Caculate the input_color is "RED".

2. Use the default setting, the packets are 64 bytes Ethernet frames,
   and the metering mode is srTCM aware::

    #define APP_MODE        APP_MODE_SRTCM_COLOR_AWARE

3. In Color-Aware mode, if the input color is red, then output color is red too.
   See the RFC 2697 file.
   The linerate is 14.88Mpps, all packets output_color are marked red,
   mapping the policer_table[2][2](RED).
   So the valid frames received on the peer IXIA port is 14.88(Mpps).

Test Case: trTCM blind mode
===========================
1. The input color of packets depends on the value "APP_PKT_COLOR_POS".
   Set::

    #define APP_PKT_COLOR_POS               5

   Caculate the input_color is "RED".

2. Use the default setting, the packets are 64 bytes Ethernet frames,
   and the metering mode is trTCM blind::

    #define APP_MODE        APP_MODE_TRTCM_COLOR_BLIND

3. In Color-Blind mode, the output color has nothing to do with input color.
   See the RFC 2698 file.
   The linerate is 14.88Mpps, 1Mpps packets output_color are marked Green,
   0.5Mpps packets are marked yellow, 13.38Mpps packets output_color are marked Red.
   Mapping the policer_table[2][0](DROP), policer_table[2][1](DROP)
   and policer_table[2][2](RED).
   So the valid frames received on the peer IXIA port is 13.38(Mpps).

4. If Set::

    #define APP_PKT_COLOR_POS               4

   Caculate the input_color is "YELLOW".
   Mapping the policer_table[1][0](DROP), policer_table[1][1](YELLOW)
   and policer_table[1][2](RED).
   The valid frames received on the peer IXIA port is 13.88(Mpps).

5. If Set::

    #define APP_PKT_COLOR_POS               3

   Caculate the input_color is "GREEN".
   Mapping the policer_table[0][0](GREEN), policer_table[0][1](RED)
   and policer_table[0][2](RED).
   The valid frames received on the peer IXIA port is 14.88(Mpps).

Test Case: trTCM aware mode
===========================
1. The input color of packets depends on the value "APP_PKT_COLOR_POS".
   Set::

    #define APP_PKT_COLOR_POS               5

   Caculate the input_color is "RED".

2. Use the default setting, the packets are 64 bytes Ethernet frames,
   and the metering mode is trTCM aware::

    #define APP_MODE        APP_MODE_TRTCM_COLOR_AWARE

3. See the RFC 2698 file.
   If the packet has been precolored as red or if Tp(t)-B < 0, the packet is red,
   So all packets output_color are marked Red.
   Mapping the policer_table[2][2](RED).
   So the valid frames received on the peer IXIA port is 14.88(Mpps).

4. If Set::

    #define APP_PKT_COLOR_POS               4

   Caculate the input_color is "YELLOW".
   If the packet has been precolored as yellow or if Tc(t)-B < 0,
   the packet is yellow and Tp is decremented by B
   So all packets output_color are marked yellow.
   Mapping the policer_table[2][2](YELLOW).
   The valid frames received on the peer IXIA port is 14.88(Mpps).

5. If Set::

    #define APP_PKT_COLOR_POS               3

   Caculate the input_color is "GREEN".
   See the RFC 2698 file, all packets output_color are marked green.
   The valid frames received on the peer IXIA port is 14.88(Mpps).

Test Case: srTCM blind changed CBS and EBS
==========================================
1. Use the default settings::

    #define APP_MODE        APP_MODE_SRTCM_COLOR_BLIND
    #define APP_PKT_COLOR_POS               5

   Caculate the input_color is "RED".

2. Set app_srtcm_params::

    .cbs = 64,
    .ebs = 512

3. The metering mode is srTCM blind.
   The packets are 64 bytes Ethernet frames, the IPv4 packet size of 46 bytes.
   The linerate is 14.88Mpps, 1.01Mpps packets output_color are marked Green and yellow,
   13.87Mpps packets output_color are marked red.
   Mapping the policer_table[2][0]/[2][1](DROP) and policer_table[2][2](RED).
   So the valid frames received on the peer IXIA port is 13.87(Mpps).
   The drop percent is 6.79%

4. The packets are 82 bytes Ethernet frames, the IPv4 packet size of 64 bytes.
   The linerate is 12.255 Mpps, the valid frames received on the peer IXIA port is 11.530Mpps.
   The drop percent is 5.92%.
   If set policer_table[2][0] "GREEN",
   the valid frames received on the peer IXIA port is 12.142Mpps.
   The drop percent is 0.92%.
   So the packets whose output color are marked green are 5%, yellow 0.92%, red 94.08%.

5. The packets are 83 bytes Ethernet frames, the IPv4 packet size of 65 bytes > cbs.
   The linerate is 12.135 Mpps, the valid frames received on the peer IXIA port is 11.422Mpps.
   The drop percent is 5.88%.
   If set policer_table[2][0] "GREEN",
   the valid frames received on the peer IXIA port is still 11.422Mpps.
   So the packets whose output color are marked green are 0%, yellow 5.88%, red 94.12%.

6. The packets are 146 bytes Ethernet frames, the IPv4 packet size of 128 bytes.
   The linerate is 7.530 Mpps, the valid frames received on the peer IXIA port is 7.168Mpps.
   The dropped packets are marked yellow, others are marked red.
   The drop percent is 4.81%.

7. The packets are 530 bytes Ethernet frames, the IPv4 packet size of 512 bytes.
   The linerate is 2.272 Mpps, the valid frames received on the peer IXIA port is 2.191Mpps.
   The dropped packets are marked yellow, others are marked red.
   The drop percent is 3.57%.

8. The packets are 531 bytes Ethernet frames, the IPv4 packet size of 513 bytes > ebs.
   The linerate is 2.268 Mpps, the valid frames received on the peer IXIA port is 2.268Mpps.
   All the packets are marked red.
   The drop percent is 0%.

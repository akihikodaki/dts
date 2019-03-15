# <COPYRIGHT_TAG>

"""
DPDK Test suite.

Test Load Balancer.

"""

import dts
from packet import Packet
from test_case import TestCase
import utils
import time


class TestLoadbalancer(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Load Balancer prerequisites.
        """
        # Verify that enough ports are available
        global dutPorts
        # Based on h/w type, choose how many ports to use
        dutPorts = self.dut.get_ports(self.nic)

        # Verify that enough ports are available
        self.verify(len(dutPorts) >= 4, "Insufficient ports for testing")

        cores = self.dut.get_core_list("all")
        self.verify(len(cores) >= 5, "Insufficient cores for testing")
        self.cores = self.dut.get_core_list("1S/5C/1T")
        self.coremask = utils.create_mask(self.cores)

        global rx_port0, rx_port1, rx_port2, rx_port3, trafficFlow
        rx_port0 = self.tester.get_local_port(dutPorts[0])
        rx_port1 = self.tester.get_local_port(dutPorts[1])
        rx_port2 = self.tester.get_local_port(dutPorts[2])
        rx_port3 = self.tester.get_local_port(dutPorts[3])

        """
        Designation the traffic flow is the same as LPM rules, send and receive packet verification:
            0: 1.0.0.0/24 => 0;
            1: 1.0.1.0/24 => 1;
            2: 1.0.2.0/24 => 2;
            3: 1.0.3.0/24 => 3;
        """
        trafficFlow = {
            "Flow1": [rx_port0, "1.0.0.1"],
            "Flow2": [rx_port1, "1.0.1.1"],
            "Flow3": [rx_port2, "1.0.2.1"],
            "Flow4": [rx_port3, "1.0.3.1"],
        }

        out = self.dut.send_expect("make -C examples/load_balancer", "#")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_load_balancer(self):
        """
        --rx: Set the receive port, queue and main core;
        --tx: Set the send port and main core;
        --w: specify 4 workers lcores,
        --lpm: IPv4 routing table,
        --bsz: The number of packet is 10 for transceivers,
        --pos-lb: Position of the 1-byte header field within the input packet that is used to
        determine the worker ID for each packet
        """

        cmd = './examples/load_balancer/build/load_balancer -l {0}-{1} -n 4 -- --rx "(0,0,{2}),(1,0,{2}),(2,0,{2}),(3,0,{2})" '\
              '--tx "(0,{2}),(1,{2}),(2,{2}),(3,{2})" --w "{3},{4},{5},{6}" '\
              '--lpm "1.0.0.0/24=>0;1.0.1.0/24=>1;1.0.2.0/24=>2;1.0.3.0/24=>3;" '\
              '--bsz "(10, 10), (10, 10), (10, 10)" --pos-lb 29'.format(self.cores[0], self.cores[4], self.cores[0], self.cores[1], self.cores[2], self.cores[3], self.cores[4])

        self.dut.send_expect(cmd, 'main loop.')

        # Verify the traffic flow according to Ipv4 route table
        for flow in trafficFlow.keys():
            rx_port = trafficFlow[flow][0]

            for i in range(len(dutPorts)):
                dstport = self.tester.get_local_port(dutPorts[i])
                pkt_count = 10
                inst = self.tester.tcpdump_sniff_packets(intf=self.tester.get_interface(rx_port), timeout=10, count=pkt_count)

                pkt = Packet()
                dst_mac = self.dut.get_mac_address(dutPorts[i])
                pkt.config_layer('ether', {'dst': dst_mac})
                pkt.config_layer('ipv4', {'src': "0.0.0.1", 'dst': trafficFlow[flow][1]})
                pkt.send_pkt(tx_port=self.tester.get_interface(dstport), count=10)
                # Wait for the sniffer to finish.
                time.sleep(5)

                pkts = self.tester.load_tcpdump_sniff_packets(inst)
                len_pkts = len(pkts)

                self.verify(len_pkts == pkt_count, "Packet number is wrong")
                for packet in pkts:
                    result = str(packet.pktgen.pkt.show)
                    self.verify("Ether" in result, "No packet received")
                    self.verify("src=0.0.0.1" + " dst=" + trafficFlow[flow][1] in result, "Wrong IP address")
                    self.verify("dst=%s" % dst_mac in result, "No packet received or packet missed")

        self.dut.send_expect("^C", "#")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass

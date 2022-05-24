# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019-2020 Intel Corporation
#

import os
import re
import time

from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestAfXdp(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # self.verify(self.nic in ("I40E_40G-QSFP_A"), "the port can not run this suite")

        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")

        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        self.header_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["udp"]

        self.logger.info(
            "you can config packet_size in file %s.cfg," % self.suite_name
            + "in region 'suite' like packet_sizes=[64, 128, 256]"
        )
        # get the frame_sizes from cfg file
        if "packet_sizes" in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()["packet_sizes"]

        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.pktgen_helper = PacketGeneratorHelper()

        self.dut.restore_interfaces()
        self.irqs_set = self.dut.new_session(suite="irqs-set")

    def set_up(self):
        pass

    def set_port_queue(self, intf):
        self.dut.send_expect(
            "ethtool -L %s combined %d" % (intf, self.nb_cores / self.port_num), "# "
        )

    def config_stream(self, rx_port, frame_size):
        tgen_input = []

        dst_mac = self.dut.get_mac_address(self.dut_ports[rx_port])
        pkt = Packet(pkt_len=frame_size)
        pkt.config_layers(
            [
                ("ether", {"dst": dst_mac}),
                ("ipv4", {"dst": "192.168.%d.1" % (rx_port + 1), "proto": 255}),
            ]
        )
        pcap = os.path.join(
            self.out_path, "af_xdp_%d_%d_%d.pcap" % (self.port_num, rx_port, frame_size)
        )
        pkt.save_pcapfile(None, pcap)
        tgen_input.append((rx_port, rx_port, pcap))

        return tgen_input

    def config_rule_stream(self, rule_index, frame_size):
        tgen_input = []

        rule = self.rule[rule_index]
        pkt = Packet(pkt_len=frame_size)
        pkt.config_layers([("udp", {"src": rule[-2], "dst": rule[-1]})])
        pcap = os.path.join(self.out_path, "af_xdp_%d_%d.pcap" % (rule[-2], frame_size))
        pkt.save_pcapfile(None, pcap)
        tgen_input.append((rule[0], rule[0], pcap))

        return tgen_input

    def ethtool_set_rule(self):
        rule_id, rule = 1, []
        for i in range(self.port_num):
            intf = self.dut.ports_info[i]["port"].get_interface_name()
            self.irqs_set.send_expect("ethtool -N %s rx-flow-hash udp4 fn" % intf, "# ")
            self.irqs_set.send_expect(
                "ethtool -N %s flow-type udp4 src-port 4243 dst-port 4243 action 0 loc %d"
                % (intf, rule_id),
                "# ",
            )
            self.irqs_set.send_expect(
                "ethtool -N %s flow-type udp4 src-port 4242 dst-port 4242 action 1 loc %d"
                % (intf, rule_id + 1),
                "# ",
            )
            rule.append((i, intf, rule_id, 4243, 4243))
            rule.append((i, intf, rule_id + 1, 4242, 4242))
            rule_id += 2
            time.sleep(1)
        self.rule = rule

    def ethtool_del_rule(self):
        for each in self.rule:
            self.irqs_set.send_expect(
                "ethtool -N %s delete %d" % (each[1], each[2]), "# "
            )

    def get_core_list(self):
        core_config = "1S/%dC/1T" % (
            self.nb_cores + 1 + max(self.port_num, self.vdev_num) * self.queue_number
        )
        self.core_list = self.dut.get_core_list(core_config, socket=self.ports_socket)

    def assign_port_core(self, separate=True):
        if separate:
            core_list = self.core_list[
                -max(self.port_num, self.vdev_num) * self.queue_number :
            ]
        else:
            core_list = self.core_list[
                : -max(self.port_num, self.vdev_num) * self.queue_number
            ][-max(self.port_num, self.vdev_num) * self.queue_number :]

        for i in range(self.port_num):
            intf = self.dut.ports_info[i]["port"].get_interface_name()
            cores = ",".join(
                core_list[i * self.queue_number : (i + 1) * self.queue_number]
            )
            if self.port_num == 1 and self.vdev_num == 2:
                cores = ",".join(core_list)
            command = "%s/set_irq_affinity %s %s" % ("/root", cores, intf)
            out = self.irqs_set.send_expect(command, "# ")
            self.verify(
                "No such file or directory" not in out,
                "can not find the set_irq_affinity in dut root",
            )
            time.sleep(1)

    def get_vdev_list(self):
        vdev_list = []

        if self.port_num == 1:
            intf = self.dut.ports_info[0]["port"].get_interface_name()
            self.set_port_queue(intf)
            time.sleep(1)
            for i in range(self.vdev_num):
                vdev = ""
                vdev = "net_af_xdp%d,iface=%s,start_queue=%d,queue_count=%d" % (
                    i,
                    intf,
                    i * self.queue_number,
                    self.queue_number,
                )
                vdev_list.append(vdev)
        else:
            for i in range(self.port_num):
                vdev = ""
                intf = self.dut.ports_info[i]["port"].get_interface_name()
                self.set_port_queue(intf)
                vdev = "net_af_xdp%d,iface=%s" % (i, intf)
                vdev_list.append(vdev)

        return vdev_list

    def launch_testpmd(self, fwd_mode="", topology="", rss_ip=False):
        self.get_core_list()

        vdev = self.get_vdev_list()

        if topology:
            topology = "--port-topology=%s" % topology
        if fwd_mode:
            fwd_mode = "--forward-mode=%s" % fwd_mode
        if rss_ip:
            rss_ip = "--rss-ip"
        else:
            rss_ip = ""

        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list[
                : -max(self.port_num, self.vdev_num) * self.queue_number
            ],
            vdevs=vdev,
            no_pci=True,
        )
        app_name = self.dut.apps_name["test-pmd"]
        command = (
            app_name
            + " %s --log-level=pmd.net.af_xdp:8 -- -i %s %s --auto-start --nb-cores=%d --rxq=%d "
            "--txq=%d %s"
            % (
                eal_params,
                fwd_mode,
                rss_ip,
                self.nb_cores,
                self.queue_number,
                self.queue_number,
                topology,
            )
        )

        self.logger.info("start testpmd")
        self.dut.send_expect(command, "testpmd> ", 120)

    def create_table(self, index=1):
        if self.port_num == 2 or index == 2:
            self.table_header = [
                "FrameSize(B)",
                "Queue number",
                "Port0 Throughput(Mpps)",
                "Port0 % linerate",
                "Port1 Throughput(Mpps)",
                "Port1 % linerate",
            ]
        else:
            self.table_header = [
                "FrameSize(B)",
                "Queue number",
                "Port Throughput(Mpps)",
                "Port % linerate",
            ]
        self.result_table_create(self.table_header)

    def update_table_info(self, *param):
        for each in param:
            self.result_table_add(each)

    def calculate_avg_throughput(self, frame_size, tgen_input, fwd_mode):
        """
        send packet and get the throughput
        """
        # set traffic option
        traffic_opt = {"delay": 5}

        # clear streams before add new streams
        self.tester.pktgen.clear_streams()

        # run packet generator
        fields_config = {
            "ip": {
                "dst": {"action": "random"},
            },
        }
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, 100, fields_config, self.tester.pktgen
        )
        _, pps = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=traffic_opt
        )

        Mpps = pps / 1000000.0

        if fwd_mode != "rxonly":
            self.verify(
                Mpps > 0, "can not receive packets of frame size %d" % (frame_size)
            )
        throughput = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))

        return Mpps, throughput

    def check_packets_of_each_port(self, port_index):
        """
        check each port has receive packets
        """
        info = re.findall("Forward statistics for port %d" % port_index, self.out)
        index = self.out.find(info[0])
        rx = re.search("RX-packets:\s*(\d*)", self.out[index:])
        tx = re.search("TX-packets:\s*(\d*)", self.out[index:])
        rx_packets = int(rx.group(1))
        tx_packets = int(tx.group(1))
        self.verify(
            rx_packets > 0 and tx_packets > 0,
            "rx-packets:%d, tx-packets:%d" % (rx_packets, tx_packets),
        )

    def check_packets_of_each_queue(self, port_index):
        """
        check port queue has receive packets
        """
        for queue_index in range(0, self.queue_number):
            queue_info = re.findall(
                "RX\s*Port=\s*%d/Queue=\s*%d" % (port_index, queue_index), self.out
            )
            queue = queue_info[0]
            index = self.out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", self.out[index:])
            tx = re.search("TX-packets:\s*(\d*)", self.out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(
                rx_packets > 0 and tx_packets > 0,
                "The port %s queue %d, rx-packets:%d, tx-packets:%d"
                % (port_index, queue_index, rx_packets, tx_packets),
            )

    def check_packets_of_all_queue(self, port_num):
        """
        check all queue has receive packets
        """
        for port_index in range(0, port_num):
            self.check_packets_of_each_queue(port_index)

    def send_and_verify_throughput(self, pkt_type="", fwd_mode=""):
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (
                self.running_case,
                frame_size,
            )
            self.logger.info(info)

            result = [frame_size, self.queue_number]

            if pkt_type.lower() == "udp":
                num = len(self.rule)
            else:
                num = self.port_num

            for i in range(num):
                if pkt_type.lower() == "udp":
                    tgen_input = self.config_rule_stream(i, frame_size)
                else:
                    tgen_input = self.config_stream(i, frame_size)

                Mpps, throughput = self.calculate_avg_throughput(
                    frame_size, tgen_input, fwd_mode
                )
                result.append(Mpps)
                result.append(throughput)

                self.out = self.dut.send_expect("stop", "testpmd> ", 60)

                if self.queue_number == 1:
                    self.check_packets_of_each_port(i)
                elif self.vdev_num == 2:
                    self.check_packets_of_all_queue(2)
                else:
                    self.check_packets_of_each_queue(i)

                self.dut.send_expect("start", "testpmd> ", 60)

            self.update_table_info(result)

            # check the throughput between two port
            if len(result) == 6:
                self.verify(
                    round((result[-2] - result[-4]) / result[-4], 2) <= 0.1,
                    "The gap is too big btween two port's throughput",
                )

    def test_perf_one_port_single_queue_and_separate_irqs(self):
        """
        single port test with PMD and IRQs are pinned to separate cores
        """
        self.nb_cores = 1
        self.queue_number = 1
        self.port_num = 1
        self.vdev_num = 1

        self.create_table()
        self.launch_testpmd(topology="loop")
        self.assign_port_core()
        self.send_and_verify_throughput()

        self.result_table_print()

    def test_perf_one_port_multiqueue_and_separate_irqs(self):
        """
        multiqueue test with PMD and IRQs are pinned to separate cores
        """
        self.nb_cores = 2
        self.queue_number = 2
        self.port_num = 1
        self.vdev_num = 1

        self.create_table()
        self.launch_testpmd(topology="loop")
        self.assign_port_core()
        self.send_and_verify_throughput()

        self.result_table_print()

    def test_perf_one_port_multiqueue_and_same_irqs(self):
        """
        multiqueue test with PMD and IRQs pinned to same cores
        """
        self.nb_cores = 2
        self.queue_number = 2
        self.port_num = 1
        self.vdev_num = 1

        self.create_table()
        self.launch_testpmd(topology="loop")
        self.assign_port_core(separate=False)
        self.send_and_verify_throughput()

        self.result_table_print()

    def test_perf_two_port_and_separate_irqs(self):
        """
        two port test with PMD and IRQs are pinned to separate cores
        """
        self.nb_cores = 2
        self.queue_number = 1
        self.port_num = 2
        self.vdev_num = 2

        self.create_table()
        self.launch_testpmd(topology="loop")
        self.assign_port_core()
        self.send_and_verify_throughput()

        self.result_table_print()

    def test_perf_two_port_and_same_irqs(self):
        """
        two ports test with PMD and IRQs pinned to same cores
        """
        self.nb_cores = 2
        self.queue_number = 1
        self.port_num = 2
        self.vdev_num = 2

        self.create_table()
        self.launch_testpmd(topology="loop")
        self.assign_port_core(separate=False)
        self.send_and_verify_throughput()

        self.result_table_print()

    def test_perf_one_port_single_queue_with_two_vdev(self):
        """
        one port with two vdev and single queue test
        """
        self.nb_cores = 2
        self.queue_number = 1
        self.port_num = 1
        self.vdev_num = 2

        self.create_table(2)
        self.launch_testpmd(topology="loop")
        self.assign_port_core()
        self.ethtool_set_rule()
        self.send_and_verify_throughput(pkt_type="udp")
        self.ethtool_del_rule()

        self.result_table_print()

    def test_perf_one_port_multiqueues_with_two_vdev(self):
        """
        one port with two vdev and multi-queues test
        """
        self.nb_cores = 8
        self.queue_number = 4
        self.port_num = 1
        self.vdev_num = 2

        self.create_table()
        self.launch_testpmd(topology="loop", rss_ip=True)
        self.assign_port_core()
        self.send_and_verify_throughput()

        self.result_table_print()

    def tear_down(self):
        self.dut.send_expect("quit", "#", 60)

    def tear_down_all(self):
        self.dut.kill_all()

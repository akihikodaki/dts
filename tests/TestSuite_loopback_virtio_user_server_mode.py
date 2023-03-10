# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
DPDK Test suite.
Test loopback virtio-user server mode
"""
import copy
import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestLoopbackVirtioUserServerMode(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.core_config = "1S/6C/1T"
        self.queue_number = 1
        self.nb_cores = 1
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.verify(
            self.cores_num >= 6, "There has not enought cores to test this case"
        )
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.core_list_user = self.core_list[0:3]
        self.core_list_host = self.core_list[3:6]
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.app_pdump = self.dut.apps_name["pdump"]
        self.dump_pcap = "/root/pdump-rx.pcap"
        self.dump_pcap_q0 = "/root/pdump-rx-q0.pcap"
        self.dump_pcap_q1 = "/root/pdump-rx-q1.pcap"

        self.vhost_user = self.dut.new_session(suite="vhost_user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        # Prepare the result table
        self.table_header = [
            "Mode",
            "Pkt_size",
            "Throughput(Mpps)",
            "Queue Number",
            "Cycle",
        ]
        self.result_table_create(self.table_header)

    def lanuch_vhost_testpmd(self, queue_number=1, nb_cores=1, extern_params=""):
        """
        start testpmd on vhost
        """
        eal_params = "--vdev 'net_vhost0,iface=vhost-net,client=1,queues={}'".format(
            queue_number
        )
        param = "--rxq={} --txq={} --nb-cores={} {}".format(
            queue_number, queue_number, nb_cores, extern_params
        )
        self.vhost_user_pmd.start_testpmd(
            self.core_list_host,
            param=param,
            no_pci=True,
            ports=[],
            eal_param=eal_params,
            prefix="vhost",
            fixed_prefix=True,
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def lanuch_virtio_user_testpmd(self, args, set_fwd_mac=True, expected="testpmd> "):
        """
        start testpmd of virtio user
        """
        eal_param = "--vdev 'net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net,server=1,queues=1,{}'".format(
            args["version"]
        )
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if "vectorized_path" in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        param = "--rxq=1 --txq=1 --no-numa"
        self.virtio_user_pmd.start_testpmd(
            cores=self.core_list_user,
            param=param,
            eal_param=eal_param,
            no_pci=True,
            ports=[],
            prefix="virtio",
            fixed_prefix=True,
            expected=expected,
        )
        if set_fwd_mac:
            self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    def lanuch_vhost_testpmd_with_multi_queue(self, extern_params="", set_fwd_mac=True):
        """
        start testpmd with multi qeueue
        """
        eal_params = "--vdev 'eth_vhost0,iface=vhost-net,client=1,queues={}'".format(
            self.queue_number
        )
        param = "--rxq={} --txq={} --nb-cores={} {}".format(
            self.queue_number, self.queue_number, self.nb_cores, extern_params
        )
        self.vhost_user_pmd.start_testpmd(
            self.core_list_host,
            param=param,
            no_pci=True,
            ports=[],
            eal_param=eal_params,
            prefix="vhost",
            fixed_prefix=True,
        )
        if set_fwd_mac:
            self.vhost_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    def lanuch_virtio_user_testpmd_with_multi_queue(
        self, mode, extern_params="", set_fwd_mac=True, vectorized_path=False
    ):
        """
        start testpmd of virtio user
        """
        eal_param = "--vdev 'net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net,server=1,queues={},{}'".format(
            self.queue_number, mode
        )
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if "vectorized_path" in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        if vectorized_path:
            eal_param += " --force-max-simd-bitwidth=512"
        param = "{} --nb-cores={} --rxq={} --txq={}".format(
            extern_params, self.nb_cores, self.queue_number, self.queue_number
        )
        self.virtio_user_pmd.start_testpmd(
            cores=self.core_list_user,
            param=param,
            eal_param=eal_param,
            no_pci=True,
            ports=[],
            prefix="virtio",
            fixed_prefix=True,
        )
        if set_fwd_mac:
            self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    def start_to_send_packets(self, session_rx, session_tx):
        """
        start the testpmd of vhost-user and virtio-user
        start to send packets
        """
        session_rx.send_command("start", 3)
        session_tx.send_expect("start tx_first 32", "testpmd> ", 30)

    def start_to_send_8k_packets(self, session_rx, session_tx):
        """
        start the testpmd of vhost-user and virtio-user
        start to send 8k packets
        """
        session_rx.send_command("start", 3)
        session_tx.send_expect("set txpkts 2000,2000,2000,2000", "testpmd> ", 30)
        session_tx.send_expect("start tx_first 32", "testpmd> ", 30)

    def start_to_send_8k_packets_csum(self, session_tx):
        """
        start the testpmd of vhost-user, start to send 8k packets
        """
        session_tx.send_expect("set fwd csum", "testpmd> ", 30)
        session_tx.send_expect("set txpkts 2000,2000,2000,2000", "testpmd> ", 30)
        session_tx.send_expect("set burst 1", "testpmd> ", 30)
        session_tx.send_expect("start tx_first 1", "testpmd> ", 10)
        session_tx.send_expect("stop", "testpmd> ", 10)

    def start_to_send_960_packets_csum(self, session_tx):
        """
        start the testpmd of vhost-user, start to send 8k packets
        """
        session_tx.send_expect("set fwd csum", "testpmd> ", 10)
        session_tx.send_expect("set txpkts 64,128,256,512", "testpmd> ", 10)
        session_tx.send_expect("set burst 1", "testpmd> ", 10)
        session_tx.send_expect("start tx_first 1", "testpmd> ", 3)
        session_tx.send_expect("stop", "testpmd> ", 10)

    def check_port_throughput_after_port_stop(self):
        """
        check the throughput after port stop
        """
        loop = 1
        while loop <= 5:
            out = self.vhost_user_pmd.execute_cmd("show port stats 0", "testpmd>", 60)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            if result == "0":
                break
            time.sleep(3)
            loop = loop + 1
        self.verify(
            result == "0", "port stop failed, it alse can recevie data after stop."
        )

    def check_port_link_status_after_port_restart(self):
        """
        check the link status after port restart
        """
        loop = 1
        while loop <= 5:
            out = self.vhost_user_pmd.execute_cmd(
                "show port info all", "testpmd> ", 120
            )
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if "down" not in port_status:
                break
            time.sleep(3)
            loop = loop + 1

        self.verify("down" not in port_status, "port can not up after restart")

    def check_link_status(self, side, status):
        out = side.send_expect("show port info 0", "testpmd> ", 120)
        res = re.search("Link\s*status:\s*(\S*)", out)
        self.verify(
            res.group(1) == status,
            "The status not right on virtio side after vhost quit, status: %s"
            % res.group(1),
        )

    def port_restart(self):
        self.vhost_user_pmd.execute_cmd("stop", "testpmd> ", 120)
        self.vhost_user_pmd.execute_cmd("port stop 0", "testpmd> ", 120)
        self.check_port_throughput_after_port_stop()
        self.vhost_user_pmd.execute_cmd("clear port stats all", "testpmd> ", 120)
        self.vhost_user_pmd.execute_cmd("port start 0", "testpmd> ", 120)
        self.check_port_link_status_after_port_restart()
        self.vhost_user_pmd.execute_cmd("start tx_first 32", "testpmd> ", 120)

    def port_restart_send_8k_packets(self):
        self.vhost_user_pmd.execute_cmd("stop", "testpmd> ", 120)
        self.vhost_user_pmd.execute_cmd("port stop 0", "testpmd> ", 120)
        self.check_port_throughput_after_port_stop()
        self.vhost_user_pmd.execute_cmd("clear port stats all", "testpmd> ", 120)
        self.vhost_user_pmd.execute_cmd("port start 0", "testpmd> ", 120)
        self.check_port_link_status_after_port_restart()
        self.vhost_user_pmd.execute_cmd(
            "set txpkts 2000,2000,2000,2000", "testpmd> ", 120
        )
        self.vhost_user_pmd.execute_cmd("start tx_first 32", "testpmd> ", 120)

    def launch_pdump_to_capture_pkt(self, multi_queue=False):
        """
        bootup pdump in dut
        """
        self.pdump_session = self.dut.new_session(suite="pdump")
        if not multi_queue:
            cmd = (
                self.app_pdump
                + " "
                + "-v --file-prefix=virtio -- "
                + "--pdump  'device_id=net_virtio_user0,queue=*,rx-dev=%s,mbuf-size=8000'"
            )
            self.pdump_session.send_expect(cmd % (self.dump_pcap), "Port")
        else:
            cmd = (
                self.app_pdump
                + " "
                + "-v --file-prefix=virtio -- "
                + "--pdump  'device_id=net_virtio_user0,queue=0,rx-dev=%s,mbuf-size=8000' "
                + "--pdump  'device_id=net_virtio_user0,queue=1,rx-dev=%s,mbuf-size=8000'"
            )
            self.pdump_session.send_expect(
                cmd % (self.dump_pcap_q0, self.dump_pcap_q1), "Port"
            )

    def check_packet_payload_valid(self, pkt_len, multi_queue=False):
        """
        check the payload is valid
        """
        self.pdump_session.send_expect("^c", "# ", 60)
        time.sleep(3)
        if not multi_queue:
            self.dut.session.copy_file_from(
                src="%s" % self.dump_pcap, dst="%s" % self.dump_pcap
            )
            pkt = Packet()
            pkts = pkt.read_pcapfile(self.dump_pcap)
            expect_data = str(pkts[0]["Raw"])

            for i in range(len(pkts)):
                self.verify(
                    len(pkts[i]) == pkt_len,
                    "virtio-user0 receive packet's length not equal %s Byte" % pkt_len,
                )
                check_data = str(pkts[i]["Raw"])
                self.verify(
                    check_data == expect_data,
                    "the payload in receive packets has been changed from %s" % i,
                )

        else:
            for pacp in [self.dump_pcap_q0, self.dump_pcap_q1]:
                self.dut.session.copy_file_from(src="%s" % pacp, dst="%s" % pacp)
                pkt = Packet()
                pkts = pkt.read_pcapfile(pacp)
                expect_data = str(pkts[0]["Raw"])

                for i in range(len(pkts)):
                    self.verify(
                        len(pkts[i]) == pkt_len,
                        "virtio-user0 receive packet's length not equal %s Byte"
                        % pkt_len,
                    )
                    check_data = str(pkts[i]["Raw"])
                    self.verify(
                        check_data == expect_data,
                        "the payload in receive packets has been changed from %s" % i,
                    )

    def relanuch_vhost_testpmd_send_packets(self, extern_params):

        self.vhost_user_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.logger.info("now reconnet from vhost")
        self.lanuch_vhost_testpmd_with_multi_queue(
            extern_params=extern_params, set_fwd_mac=False
        )
        self.launch_pdump_to_capture_pkt(multi_queue=True)
        self.start_to_send_8k_packets_csum(self.vhost_user)
        self.check_packet_payload_valid(self.pkt_len, multi_queue=True)

    def relanuch_vhost_testpmd_send_960_packets(self, extern_params):

        self.vhost_user_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.logger.info("now reconnet from vhost")
        self.lanuch_vhost_testpmd_with_multi_queue(
            extern_params=extern_params, set_fwd_mac=False
        )
        self.launch_pdump_to_capture_pkt(multi_queue=True)
        self.start_to_send_960_packets_csum(self.vhost_user)
        self.check_packet_payload_valid(pkt_len=960, multi_queue=True)

    def relanuch_virtio_testpmd_with_multi_path(self, mode, case_info, extern_params):

        self.virtio_user_pmd.execute_cmd("stop")
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)
        self.logger.info(case_info)
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params, set_fwd_mac=False
        )
        self.virtio_user_pmd.execute_cmd("set fwd csum")
        self.virtio_user_pmd.execute_cmd("start")
        self.launch_pdump_to_capture_pkt(multi_queue=True)
        self.start_to_send_8k_packets_csum(self.vhost_user)
        self.check_packet_payload_valid(self.pkt_len, multi_queue=True)

        self.relanuch_vhost_testpmd_send_packets(extern_params)

    def relanuch_virtio_testpmd_with_non_mergeable_path(
        self,
        mode,
        case_info,
        extern_params,
        vectorized_path=False,
    ):
        self.virtio_user_pmd.execute_cmd("stop")
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)
        self.logger.info(case_info)
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode,
            extern_params=extern_params,
            set_fwd_mac=False,
            vectorized_path=vectorized_path,
        )
        self.virtio_user_pmd.execute_cmd("set fwd csum")
        self.virtio_user_pmd.execute_cmd("start")
        self.launch_pdump_to_capture_pkt(multi_queue=True)

        self.start_to_send_960_packets_csum(
            self.vhost_user,
        )
        self.check_packet_payload_valid(pkt_len=960, multi_queue=True)

        self.relanuch_vhost_testpmd_send_960_packets(extern_params)

    def relanuch_vhost_testpmd_with_multi_queue(self):
        self.vhost_user_pmd.execute_cmd(
            "stop",
        )
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.check_link_status(self.virtio_user, "down")
        self.lanuch_vhost_testpmd_with_multi_queue()

    def relanuch_virtio_testpmd_with_multi_queue(self, mode, extern_params=""):
        self.virtio_user_pmd.execute_cmd(
            "stop",
        )
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)
        self.check_link_status(self.vhost_user, "down")
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode, extern_params)

    def calculate_avg_throughput(self, case_info, cycle, Pkt_size=True):
        """
        calculate the average throughput
        """
        results = 0.0
        results_row = []
        self.vhost_user_pmd.execute_cmd("show port stats all", "testpmd>", 60)
        for i in range(10):
            out = self.vhost_user_pmd.execute_cmd("show port stats all", "testpmd>", 60)
            time.sleep(1)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        results_row.append(case_info)
        if Pkt_size:
            self.verify(Mpps > 5, "port can not receive packets")
            results_row.append("64")
        else:
            self.verify(Mpps > 1, "port can not receive packets")
            results_row.append("8k")

        results_row.append(Mpps)
        results_row.append(self.queue_number)
        results_row.append(cycle)
        self.result_table_add(results_row)
        self.logger.info(results_row)

    def check_packets_of_each_queue(self):
        """
        check all the queue has receive packets
        """
        out = self.vhost_user_pmd.execute_cmd("stop", "testpmd> ", 60)
        for queue_index in range(0, self.queue_number):
            queue = "Queue= %d" % queue_index
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(
                rx_packets > 0 and tx_packets > 0,
                "The queue %d rx-packets or tx-packets is 0, rx-packets:%s, tx-packets:%s"
                % (queue_index, rx_packets, tx_packets),
            )

    def close_all_testpmd(self):
        """
        close testpmd about vhost-user and virtio-user
        """
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)

    def close_all_session(self):
        """
        close session of vhost-user and virtio-user
        """
        self.dut.close_session(self.virtio_user)
        self.dut.close_session(self.vhost_user)

    def test_server_mode_launch_virtio11_first(self):
        """
        Test Case 1: basic test for packed ring server mode, launch virtio-user first
        """
        self.queue_number = 1
        self.nb_cores = 1
        virtio_pmd_arg = {
            "version": "packed_vq=1,in_order=0,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.lanuch_virtio_user_testpmd(
            virtio_pmd_arg,
            set_fwd_mac=False,
            expected="waiting for client connection...",
        )
        self.lanuch_vhost_testpmd()
        self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput("lanuch virtio first", "")
        self.result_table_print()
        self.close_all_testpmd()

    def test_server_mode_launch_virtio_first(self):
        """
        Test Case 2: basic test for split ring server mode, launch virtio-user first
        """
        self.queue_number = 1
        self.nb_cores = 1
        virtio_pmd_arg = {
            "version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip",
        }
        self.lanuch_virtio_user_testpmd(
            virtio_pmd_arg,
            set_fwd_mac=False,
            expected="waiting for client connection...",
        )
        self.lanuch_vhost_testpmd()
        self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput("lanuch virtio first", "")
        self.result_table_print()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_mergeable_path(self):
        """
        Test Case 3: reconnect test with virtio 1.0 mergeable path and server mode
        """
        self.queue_number = 8
        self.nb_cores = 2
        case_info = "virtio1.0 mergeable path"
        mode = "in_order=0,mrg_rxbuf=1"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet", Pkt_size=False)

        # reconnet from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_8k_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost", Pkt_size=False)

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(
            case_info, "reconnet from virtio_user", Pkt_size=False
        )

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart_send_8k_packets()
        self.calculate_avg_throughput(case_info, "after port restart", Pkt_size=False)

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_inorder_mergeable_path(self):
        """
        Test Case 4: reconnect test with virtio 1.0 inorder mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.0 inorder mergeable path"
        mode = "in_order=1,mrg_rxbuf=1"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet", Pkt_size=False)

        # reconnet from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_8k_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost", Pkt_size=False)

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(
            case_info, "reconnet from virtio_user", Pkt_size=False
        )

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart_send_8k_packets()
        self.calculate_avg_throughput(case_info, "after port restart", Pkt_size=False)

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_inorder_non_mergeable_path(self):
        """
        Test Case 5: reconnect test with virtio 1.0 inorder non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.0 inorder non_mergeable path"
        mode = "in_order=1,mrg_rxbuf=0"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_non_mergeable_path(self):
        """
        Test Case 6: reconnect test with virtio 1.0 non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.0 non_mergeable path"
        mode = "in_order=0,mrg_rxbuf=0,vectorized=1"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_vector_rx_path(self):
        """
        Test Case 7: reconnect test with virtio 1.0 vector_rx path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.0 vector_rx path"
        mode = "in_order=0,mrg_rxbuf=0,vectorized=1"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_mergeable_path(self):
        """
        Test Case 8: reconnect test with virtio 1.1 mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.1 mergeable path"
        mode = "packed_vq=1,in_order=0,mrg_rxbuf=1"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet", Pkt_size=False)

        # reconnect from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_8k_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost", Pkt_size=False)

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(
            case_info, "reconnet from virtio user", Pkt_size=False
        )

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart_send_8k_packets()
        self.calculate_avg_throughput(case_info, "after port restart", Pkt_size=False)

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_non_mergeable_path(self):
        """
        Test Case 9: reconnect test with virtio 1.1 non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.1 non_mergeable path"
        mode = "packed_vq=1,in_order=0,mrg_rxbuf=0"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_inorder_mergeable_path(self):
        """
        Test Case 10: reconnect test with virtio 1.1 inorder mergeable path and server mode
        """
        self.queue_number = 8
        self.nb_cores = 2
        case_info = "virtio1.1 inorder mergeable path"
        mode = "packed_vq=1,in_order=1,mrg_rxbuf=1"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet", Pkt_size=False)

        # reconnect from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_8k_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost", Pkt_size=False)

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_8k_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(
            case_info, "reconnet from virtio user", Pkt_size=False
        )

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart_send_8k_packets()
        self.calculate_avg_throughput(case_info, "after port restart", Pkt_size=False)

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_inorder_non_mergeable_path(self):
        """
        Test Case 11: reconnect test with virtio 1.1 inorder non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.1 inorder non_mergeable path"
        mode = "packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1"
        extern_params = "--rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_inorder_vectorized_path(self):
        """
        Test Case 12: reconnect test with virtio 1.1 inorder vectorized path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = "virtio1.1 inorder vectorized path"
        mode = "packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1"
        extern_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info("now reconnet from vhost")
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost_user)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user")
        self.relanuch_virtio_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params
        )
        self.start_to_send_packets(self.vhost_user, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info("now vhost port restart")
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_packed_all_path_payload_check(self):
        """
        Test Case 13: loopback packed ring all path payload check test using server mode and multi-queues
        """
        self.queue_number = 8
        self.nb_cores = 1
        extern_params = "--txd=1024 --rxd=1024"
        case_info = "packed ring mergeable inorder path"
        mode = "mrg_rxbuf=1,in_order=1,packed_vq=1"

        self.lanuch_vhost_testpmd_with_multi_queue(
            extern_params=extern_params, set_fwd_mac=False
        )
        self.logger.info(case_info)
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params, set_fwd_mac=False
        )
        self.virtio_user_pmd.execute_cmd("set fwd csum")
        self.virtio_user_pmd.execute_cmd("start")
        self.launch_pdump_to_capture_pkt(multi_queue=True)
        self.start_to_send_8k_packets_csum(self.vhost_user)

        # 5. Check all the packets length is 8000 Byte in the pcap file
        self.pkt_len = 8000
        self.check_packet_payload_valid(self.pkt_len, multi_queue=True)

        # reconnet from vhost
        self.relanuch_vhost_testpmd_send_packets(extern_params)

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user with other path")
        case_info = "packed ring mergeable path"
        mode = "mrg_rxbuf=1,in_order=0,packed_vq=1"
        self.relanuch_virtio_testpmd_with_multi_path(mode, case_info, extern_params)

        case_info = "packed ring non-mergeable path"
        mode = "mrg_rxbuf=0,in_order=0,packed_vq=1"
        self.relanuch_virtio_testpmd_with_non_mergeable_path(
            mode, case_info, extern_params
        )

        case_info = "packed ring inorder non-mergeable path"
        mode = "mrg_rxbuf=0,in_order=1,packed_vq=1"
        self.relanuch_virtio_testpmd_with_non_mergeable_path(
            mode, case_info, extern_params
        )

        case_info = "packed ring vectorized path"
        mode = "mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1"
        self.relanuch_virtio_testpmd_with_non_mergeable_path(
            mode, case_info, extern_params, vectorized_path=True
        )

        case_info = "packed ring vectorized path and ring size is not power of 2"
        mode = "mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025"
        extern_param = "--txd=1025 --rxd=1025"
        self.relanuch_virtio_testpmd_with_non_mergeable_path(
            mode, case_info, extern_param, vectorized_path=True
        )

        self.close_all_testpmd()

    def test_server_mode_reconnect_with_split_all_path_payload_check(self):
        """
        Test Case 14: loopback split ring all path payload check test using server mode and multi-queues
        """
        self.queue_number = 8
        self.nb_cores = 1
        extern_params = "--txd=1024 --rxd=1024"
        case_info = "split ring mergeable inorder path"
        mode = "mrg_rxbuf=1,in_order=1"

        self.lanuch_vhost_testpmd_with_multi_queue(
            extern_params=extern_params, set_fwd_mac=False
        )
        self.logger.info(case_info)
        self.lanuch_virtio_user_testpmd_with_multi_queue(
            mode=mode, extern_params=extern_params, set_fwd_mac=False
        )
        self.virtio_user_pmd.execute_cmd("set fwd csum")
        self.virtio_user_pmd.execute_cmd("start")
        self.launch_pdump_to_capture_pkt(multi_queue=True)
        self.start_to_send_8k_packets_csum(self.vhost_user)

        # 5. Check all the packets length is 8000 Byte in the pcap file
        self.pkt_len = 8000
        self.check_packet_payload_valid(self.pkt_len, multi_queue=True)

        # reconnet from vhost
        self.relanuch_vhost_testpmd_send_packets(extern_params)

        # reconnet from virtio
        self.logger.info("now reconnet from virtio_user with other path")
        case_info = "split ring mergeable path"
        mode = "mrg_rxbuf=1,in_order=0"
        self.relanuch_virtio_testpmd_with_multi_path(mode, case_info, extern_params)

        case_info = "split ring non-mergeable path"
        mode = "mrg_rxbuf=0,in_order=0"
        extern_param = extern_params + " --enable-hw-vlan-strip"
        self.relanuch_virtio_testpmd_with_non_mergeable_path(
            mode, case_info, extern_param
        )

        case_info = "split ring inorder non-mergeable path"
        mode = "mrg_rxbuf=0,in_order=1"
        self.relanuch_virtio_testpmd_with_non_mergeable_path(
            mode, case_info, extern_params
        )

        case_info = "split ring vectorized path"
        mode = "mrg_rxbuf=0,in_order=0,vectorized=1"
        self.relanuch_virtio_testpmd_with_non_mergeable_path(
            mode, case_info, extern_params
        )

        self.close_all_testpmd()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_all_session()

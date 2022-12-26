# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
DPDK Test suite.
Benchmark pvp qemu test with 3 RX/TX PATHs,
includes Mergeable, Normal, Vector_RX.
Cover virtio 1.0 and virtio 0.95.Also cover
port restart test with each path
"""
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.test_case import TestCase
from framework.virt_common import VM


class TestPVPQemuMultiPathPortRestart(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64, 128, 256, 512, 1024, 1280, 1518]
        self.core_config = "1S/3C/1T"
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        # get core mask
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.vm_dut = None
        self.virtio1_mac = "52:54:00:00:00:01"

        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.number_of_ports = 1
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        # Prepare the result table
        self.table_header = [
            "FrameSize(B)",
            "Mode",
            "Throughput(Mpps)",
            "% linerate",
            "Cycle",
        ]
        self.result_table_create(self.table_header)

        self.vhost = self.dut.new_session(suite="vhost-user")

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        vdev = [r"'net_vhost0,iface=vhost-net,queues=1'"]
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list, prefix="vhost", ports=[self.pci_info], vdevs=vdev
        )
        para = " -- -i --nb-cores=1 --txd=1024 --rxd=1024"
        command_line_client = self.path + eal_params + para
        self.vhost.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 120)
        self.vhost.send_expect("start", "testpmd> ", 120)

    def start_vm_testpmd(self, path):
        """
        start testpmd in vm depend on different path
        """
        if path == "mergeable":
            command = (
                self.path + "-c 0x3 -n 3 -- -i " + "--nb-cores=1 --txd=1024 --rxd=1024"
            )
        elif path == "normal":
            command = (
                self.path
                + "-c 0x3 -n 3 -- -i "
                + "--tx-offloads=0x0 --enable-hw-vlan-strip "
                + "--nb-cores=1 --txd=1024 --rxd=1024"
            )
        elif path == "vector_rx":
            command = (
                self.path
                + "-c 0x3 -n 3 -a %s,vectorized=1 -- -i "
                + "--nb-cores=1 --txd=1024 --rxd=1024"
            ) % self.vm_dut.get_port_pci(0)
        self.vm_dut.send_expect(command, "testpmd> ", 30)
        self.vm_dut.send_expect("set fwd mac", "testpmd> ", 30)
        self.vm_dut.send_expect("start", "testpmd> ", 30)

    def start_one_vm(self, modem=0, mergeable=0):
        """
        start qemu
        """
        self.vm = VM(self.dut, "vm0", "vhost_sample")
        vm_params = {}
        vm_params["driver"] = "vhost-user"
        vm_params["opt_path"] = "./vhost-net"
        vm_params["opt_mac"] = self.virtio1_mac
        if modem == 1 and mergeable == 0:
            vm_params[
                "opt_settings"
            ] = "disable-modern=false,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024"
        elif modem == 1 and mergeable == 1:
            vm_params[
                "opt_settings"
            ] = "disable-modern=false,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024"
        elif modem == 0 and mergeable == 0:
            vm_params[
                "opt_settings"
            ] = "disable-modern=true,mrg_rxbuf=off,rx_queue_size=1024,tx_queue_size=1024"
        elif modem == 0 and mergeable == 1:
            vm_params[
                "opt_settings"
            ] = "disable-modern=true,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024"
        self.vm.set_vm_device(**vm_params)

        try:
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def check_port_throughput_after_port_stop(self):
        """
        check the throughput after port stop
        """
        loop = 1
        while loop <= 5:
            out = self.vhost.send_expect("show port stats 0", "testpmd>", 60)
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
            out = self.vhost.send_expect("show port info all", "testpmd> ", 120)
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if "down" not in port_status:
                break
            time.sleep(3)
            loop = loop + 1

        self.verify("down" not in port_status, "port can not up after restart")

    def port_restart(self):
        self.vhost.send_expect("stop", "testpmd> ", 120)
        self.vhost.send_expect("port stop 0", "testpmd> ", 120)
        self.check_port_throughput_after_port_stop()
        self.vhost.send_expect("clear port stats all", "testpmd> ", 120)
        self.vhost.send_expect("port start all", "testpmd> ", 120)
        self.check_port_link_status_after_port_restart()
        self.vhost.send_expect("start", "testpmd> ", 120)

    def update_table_info(self, case_info, frame_size, Mpps, throughtput, Cycle):
        results_row = [frame_size]
        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(throughtput)
        results_row.append(Cycle)
        self.result_table_add(results_row)

    @property
    def check_value(self):
        check_dict = dict.fromkeys(self.frame_sizes)
        linerate = {
            64: 0.075,
            128: 0.10,
            256: 0.10,
            512: 0.20,
            1024: 0.35,
            1280: 0.40,
            1518: 0.45,
        }
        for size in self.frame_sizes:
            speed = self.wirespeed(self.nic, size, self.number_of_ports)
            check_dict[size] = round(speed * linerate[size], 2)
        return check_dict

    def calculate_avg_throughput(self, frame_size):
        """
        start to send packet and get the throughput
        """
        pkt = Packet(pkt_type="IP_RAW", pkt_len=frame_size)
        pkt.config_layer("ether", {"dst": "%s" % self.dst_mac})
        pkt.save_pcapfile(self.tester, "%s/pvp_multipath.pcap" % (self.out_path))

        tgenInput = []
        port = self.tester.get_local_port(self.dut_ports[0])
        tgenInput.append((port, port, "%s/pvp_multipath.pcap" % self.out_path))
        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgenInput, 100, None, self.tester.pktgen
        )
        # set traffic option
        traffic_opt = {"delay": 5}
        _, pps = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=traffic_opt
        )
        Mpps = pps / 1000000.0
        self.verify(
            Mpps > self.check_value[frame_size],
            "%s of frame size %d speed verify failed, expect %s, result %s"
            % (self.running_case, frame_size, self.check_value[frame_size], Mpps),
        )
        throughput = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))
        return Mpps, throughput

    def send_and_verify(self, case_info):
        """
        start to send packets and verify it
        """
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (
                self.running_case,
                frame_size,
            )
            self.logger.info(info)

            Mpps, throughput = self.calculate_avg_throughput(frame_size)
            self.update_table_info(
                case_info, frame_size, Mpps, throughput, "Before Restart"
            )

            self.port_restart()
            Mpps, throughput = self.calculate_avg_throughput(frame_size)
            self.update_table_info(
                case_info, frame_size, Mpps, throughput, "After Restart"
            )

    def close_all_testpmd(self):
        """
        close testpmd about vhost-user and vm_testpmd
        """
        self.vhost.send_expect("quit", "#", 60)
        self.vm_dut.send_expect("quit", "#", 60)

    def close_session(self):
        """
        close session of vhost-user
        """
        self.dut.close_session(self.vhost)

    def test_perf_pvp_qemu_mergeable_mac(self):
        """
        performance for [frame_sizes] and restart port on virtio 0.95 mergeable path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(modem=0, mergeable=1)
        self.start_vm_testpmd(path="mergeable")
        self.send_and_verify("virtio0.95 mergeable")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_normal_mac(self):
        """
        performance for [frame_sizes] and restart port ob virtio0.95 normal path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(modem=0, mergeable=0)
        self.start_vm_testpmd(path="normal")
        self.send_and_verify("virtio0.95 normal")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_vector_rx_mac(self):
        """
        performance for [frame_sizes] and restart port on virtio0.95 vector_rx
        """
        self.start_vhost_testpmd()
        self.start_one_vm(modem=0, mergeable=0)
        self.start_vm_testpmd(path="vector_rx")
        self.send_and_verify("virtio0.95 vector_rx")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_mergeable_mac(self):
        """
        performance for [frame_sizes] and restart port on virtio1.0 mergeable path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(modem=1, mergeable=1)
        self.start_vm_testpmd(path="mergeable")
        self.send_and_verify("virtio1.0 mergeable")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_normal_path(self):
        """
        performance for [frame_sizes] and restart port on virito1.0 normal path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(modem=1, mergeable=0)
        self.start_vm_testpmd(path="normal")
        self.send_and_verify("virtio1.0 normal")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_vector_rx_mac(self):
        """
        performance for frame_sizes and restart port on virtio1.0 vector rx
        """
        self.start_vhost_testpmd()
        self.start_one_vm(modem=1, mergeable=0)
        self.start_vm_testpmd(path="vector_rx")
        self.send_and_verify("virtio1.0 vector_rx")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_mergeable_mac_restart_100_times(self):
        """
        restart port 100 times on virtio1.0 mergeable path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(modem=1, mergeable=1)
        self.start_vm_testpmd(path="mergeable")

        case_info = "virtio1.0 mergeable"
        Mpps, throughput = self.calculate_avg_throughput(64)
        self.update_table_info(case_info, 64, Mpps, throughput, "Before Restart")
        for cycle in range(100):
            self.logger.info("now port restart  %d times" % (cycle + 1))
            self.port_restart()
            Mpps, throughput = self.calculate_avg_throughput(64)
            self.update_table_info(
                case_info, 64, Mpps, throughput, "After port restart"
            )

        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.close_session()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """

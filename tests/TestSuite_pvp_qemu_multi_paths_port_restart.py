# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
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
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.number_of_ports = 1
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        # Prepare the result table
        self.table_header = [
            "FrameSize(B)",
            "Mode",
            "Throughput(Mpps)",
            "% linerate",
            "Cycle",
        ]
        self.result_table_create(self.table_header)

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        eal_param = "--vdev 'eth_vhost0,iface=vhost-net,queues=1'"
        param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.vhost_user_pmd.start_testpmd(
            cores=self.core_list,
            eal_param=eal_param,
            param=param,
            prefix="vhost-user",
            fixed_prefix=True,
            ports=[self.pci_info],
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    def start_vm_testpmd(self, path):
        """
        start testpmd in vm depend on different path
        """
        self.vm0_pmd = PmdOutput(self.vm_dut)
        self.vm0_pci = self.vm_dut.get_port_pci(0)
        self.vm_core_config = "1S/2C/1T"
        self.vm_core_list = self.vm_dut.get_core_list(config=self.vm_core_config)
        eal_param = "-a %s" % (self.vm0_pci)
        param = "--nb-cores=1 --txd=1024 --rxd=1024"
        if path == "mergeable":
            eal_param = eal_param
            param = param
        elif path == "normal":
            eal_param = eal_param
            param = "--tx-offloads=0x0 --enable-hw-vlan-strip " + param
        elif path == "vector_rx":
            eal_param = eal_param + ",vectorized=1"
            param = param
        self.vm0_pmd.start_testpmd(
            cores=self.vm_core_list, eal_param=eal_param, param=param, fixed_prefix=True
        )
        self.vm0_pmd.execute_cmd("set fwd mac")
        self.vm0_pmd.execute_cmd("start")

    def start_one_vm(self, disable_modern=False, mrg_rxbuf=False, packed=False):
        """
        start qemu
        """
        self.vm = VM(self.dut, "vm0", "vhost_sample")
        vm_params = {}
        vm_params["driver"] = "vhost-user"
        vm_params["opt_path"] = "%s/vhost-net" % self.base_dir
        vm_params["opt_mac"] = self.virtio1_mac
        disable_modern_param = "true" if disable_modern else "false"
        mrg_rxbuf_param = "on" if mrg_rxbuf else "off"
        packed_param = ",packed=on" if packed else ""
        vm_params[
            "opt_settings"
        ] = "disable-modern=%s,mrg_rxbuf=%s,rx_queue_size=1024,tx_queue_size=1024%s" % (
            disable_modern_param,
            mrg_rxbuf_param,
            packed_param,
        )
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
            out = self.vhost_user_pmd.execute_cmd("show port stats 0")
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
            out = self.vhost_user_pmd.execute_cmd("show port info all")
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if "down" not in port_status:
                break
            time.sleep(3)
            loop = loop + 1

        self.verify("down" not in port_status, "port can not up after restart")

    def port_restart(self):
        self.vhost_user_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("port stop 0")
        self.check_port_throughput_after_port_stop()
        self.vhost_user_pmd.execute_cmd("clear port stats all")
        self.vhost_user_pmd.execute_cmd("port start all")
        self.check_port_link_status_after_port_restart()
        self.vhost_user_pmd.execute_cmd("start")

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
        self.vhost_user_pmd.quit()
        self.vm0_pmd.quit()

    def close_session(self):
        """
        close session of vhost-user
        """
        self.dut.close_session(self.vhost_user)

    def test_perf_pvp_qemu_mergeable_mac(self):
        """
        Test Case 1: pvp test with virtio 0.95 mergeable path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=True, mrg_rxbuf=True, packed=False)
        self.start_vm_testpmd(path="mergeable")
        self.send_and_verify("virtio0.95 mergeable")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_normal_mac(self):
        """
        Test Case 2: pvp test with virtio 0.95 normal path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=True, mrg_rxbuf=False, packed=False)
        self.start_vm_testpmd(path="normal")
        self.send_and_verify("virtio0.95 normal")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_vector_rx_mac(self):
        """
        Test Case 3: pvp test with virtio 0.95 vrctor_rx path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=True, mrg_rxbuf=False, packed=False)
        self.start_vm_testpmd(path="vector_rx")
        self.send_and_verify("virtio0.95 vector_rx")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_mergeable_mac(self):
        """
        Test Case 4: pvp test with virtio 1.0 mergeable path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=False, mrg_rxbuf=True, packed=False)
        self.start_vm_testpmd(path="mergeable")
        self.send_and_verify("virtio1.0 mergeable")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_normal_path(self):
        """
        Test Case 5: pvp test with virtio 1.0 normal path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=False, mrg_rxbuf=False, packed=False)
        self.start_vm_testpmd(path="normal")
        self.send_and_verify("virtio1.0 normal")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_vector_rx_mac(self):
        """
        Test Case 6: pvp test with virtio 1.0 vrctor_rx path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=False, mrg_rxbuf=False, packed=False)
        self.start_vm_testpmd(path="vector_rx")
        self.send_and_verify("virtio1.0 vector_rx")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_with_virtio_11_mergeable_mac(self):
        """
        Test Case 7: pvp test with virtio 1.1 mergeable path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=False, mrg_rxbuf=True, packed=True)
        self.start_vm_testpmd(path="mergeable")
        self.send_and_verify("virtio1.1 mergeable")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_with_virtio_11_normal_path(self):
        """
        Test Case 8: pvp test with virtio 1.1 normal path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=False, mrg_rxbuf=False, packed=True)
        self.start_vm_testpmd(path="normal")
        self.send_and_verify("virtio1.1 normal")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_with_virtio_11_vector_rx_mac(self):
        """
        Test Case 9: pvp test with virtio 1.1 vrctor_rx path
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=False, mrg_rxbuf=False, packed=True)
        self.start_vm_testpmd(path="vector_rx")
        self.send_and_verify("virtio1.1 vector_rx")
        self.close_all_testpmd()
        self.result_table_print()
        self.vm.stop()

    def test_perf_pvp_qemu_modern_mergeable_mac_restart_10_times(self):
        """
        Test Case 10: pvp test with virtio 1.0 mergeable path restart 10 times
        """
        self.start_vhost_testpmd()
        self.start_one_vm(disable_modern=False, mrg_rxbuf=True, packed=False)
        self.start_vm_testpmd(path="mergeable")

        case_info = "virtio1.0 mergeable"
        Mpps, throughput = self.calculate_avg_throughput(64)
        self.update_table_info(case_info, 64, Mpps, throughput, "Before Restart")
        for cycle in range(10):
            self.logger.info("now port restart %d times" % (cycle + 1))
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

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_session()

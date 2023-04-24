# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import re
import time

from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE, UPDATE_EXPECTED, load_global_setting
from framework.test_case import TestCase
from framework.virt_common import VM


class TestVhostPVPDiffQemuVersion(TestCase):
    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.pf = self.dut_ports[0]
        # Get the port's socket
        netdev = self.dut.ports_info[self.pf]["port"]
        self.socket = netdev.get_nic_socket()
        self.cores_num = len(
            [n for n in self.dut.cores if int(n["socket"]) == self.socket]
        )
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            self.cores_num >= 3, "There has not enought cores to test this suite"
        )
        self.cores = self.dut.get_core_list("1S/3C/1T", socket=self.socket)
        self.vm_dut = None
        self.packet_params_set()
        self.logger.info(
            "You can config all the path of qemu version you want to"
            + " tested in the conf file %s.cfg" % self.suite_name
        )
        self.logger.info(
            "You can config packet_size in file %s.cfg," % self.suite_name
            + " in region 'suite' like packet_sizes=[64, 128, 256]"
        )
        res = self.verify_qemu_version_config()
        self.verify(res is True, "The path of qemu version in config file not right")
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.nb_ports = 1
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.gap = self.get_suite_cfg()["accepted_tolerance"]
        self.vhost_user = self.dut.new_session(suite="vhost-user")

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -I qemu-system-x86_64", "#", 20)
        self.throughput = dict()
        self.test_result = []
        self.table_header = [
            "QemuVersion",
            "FrameSize(B)",
            "Throughput(Mpps)",
            "LineRate(%)",
        ]

    def packet_params_set(self):
        self.frame_sizes = [64, 128, 256, 512, 1024, 1280, 1518]
        # get the frame_sizes from cfg file
        if "packet_sizes" in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()["packet_sizes"]
        self.virtio1_mac = "52:54:00:00:00:01"
        self.src1 = "192.168.4.1"
        self.dst1 = "192.168.3.1"

    def get_qemu_list_from_config(self):
        """
        get the config of qemu path in vm params
        """
        config_qemu = False
        params_num = len(self.vm.params)
        for qemu_index in range(params_num):
            if list(self.vm.params[qemu_index].keys())[0] == "qemu":
                qemu_num = len(self.vm.params[qemu_index]["qemu"])
                config_qemu = True
                break
        self.verify(
            config_qemu is True,
            "Please config qemu path which you want to test in conf gile",
        )
        self.qemu_pos = qemu_index
        self.qemu_list = self.vm.params[qemu_index]["qemu"]

    def verify_qemu_version_config(self):
        """
        verify the config has config enough qemu version
        """
        self.vm = VM(self.dut, "vm0", self.suite_name)
        self.vm.load_config()
        # get qemu version list from config file
        self.get_qemu_list_from_config()
        qemu_num = len(self.qemu_list)
        for i in range(qemu_num):
            qemu_path = self.qemu_list[i]["path"]
            out = self.dut.send_expect("ls %s" % qemu_path, "#")
            if "No such file or directory" in out:
                self.logger.error(
                    "No emulator [ %s ] on the DUT [ %s ]"
                    % (qemu_path, self.dut.get_ip_address())
                )
                return False
            out = self.dut.send_expect("[ -x %s ];echo $?" % qemu_path, "# ")
            if out != "0":
                self.logger.error(
                    "Emulator [ %s ] not executable on the DUT [ %s ]"
                    % (qemu_path, self.dut.get_ip_address())
                )
                return False
            out = self.dut.send_expect("%s --version" % qemu_path, "#")
            result = re.search("QEMU\s*emulator\s*version\s*(\d*.\d*)", out)
            version = result.group(1)
            # update the version info to self.qemu_list
            self.qemu_list[i].update({"version": "qemu-%s" % version})
        self.qemu_versions = list()
        for i in self.qemu_list:
            self.qemu_versions.append(i["version"])
        # print all the qemu version you config
        config_qemu_version = ""
        for i in range(len(self.qemu_list)):
            config_qemu_version += self.qemu_list[i]["version"] + " "
        self.logger.info(
            "The suite will test the qemu version of: %s" % config_qemu_version
        )
        return True

    def rm_vm_qemu_path_config(self):
        """
        According it has config all qemu path, so pop the qemu path info in params
        when start the vm set the qemu path info
        """
        params_num = len(self.vm.params)
        for qemu_index in range(params_num):
            if list(self.vm.params[qemu_index].keys())[0] == "qemu":
                qemu_num = len(self.vm.params[qemu_index]["qemu"])
                break
        self.verify(qemu_index < params_num, "Please config qemu path in conf gile")
        self.vm.params.pop(qemu_index)

    def start_one_vm(self, qemu_path, qemu_mode):
        """
        start vm
        """
        self.vm = VM(self.dut, "vm0", self.suite_name)
        vm_params = {}
        vm_params["driver"] = "vhost-user"
        vm_params["opt_path"] = "%s/vhost-net" % self.base_dir
        vm_params["opt_mac"] = self.virtio1_mac
        if qemu_mode == 0:
            vm_params["opt_settings"] = "disable-modern=true,mrg_rxbuf=on"
        elif qemu_mode == 1:
            vm_params["opt_settings"] = "disable-modern=false,mrg_rxbuf=on"
        elif qemu_mode == 2:
            vm_params["opt_settings"] = "disable-modern=false,mrg_rxbuf=on,packed=on"
        self.vm.set_vm_device(**vm_params)
        self.vm.load_config()
        self.rm_vm_qemu_path_config()
        # set qemu version info
        self.vm.set_qemu_emulator(qemu_path)
        # Due to we have change the params info before,
        # so need to start vm with load_config=False
        try:
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def start_vhost_testpmd(self):
        """
        Launch the vhost testpmd
        """
        vdev = [r"'eth_vhost0,iface=%s/vhost-net,queues=1'" % self.base_dir]
        eal_params = self.dut.create_eal_parameters(
            cores=self.cores, prefix="vhost", ports=[self.pci_info], vdevs=vdev
        )
        para = " -- -i --nb-cores=1 --txd=1024 --rxd=1024"
        command_line_client = self.path + eal_params + para
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 30)
        self.vhost_user.send_expect("set fwd mac", "testpmd> ", 30)
        self.vhost_user.send_expect("start", "testpmd> ", 30)

    def vm_testpmd_start(self):
        """
        Start testpmd in vm
        """
        if self.vm_dut is not None:
            vm_testpmd = (
                self.path + " -c 0x3 -n 3" + " -- -i --nb-cores=1 --txd=1024 --rxd=1024"
            )
            self.vm_dut.send_expect(vm_testpmd, "testpmd> ", 20)
            self.vm_dut.send_expect("set fwd mac", "testpmd> ", 20)
            self.vm_dut.send_expect("start", "testpmd> ")

    def perf_test(self, qemu_version, vlan_id1=0):
        self.result_table_create(self.table_header)
        self.throughput[qemu_version] = {}
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (
                self.running_case,
                frame_size,
            )
            self.logger.info(info)
            payload = frame_size - HEADER_SIZE["eth"] - HEADER_SIZE["ip"]
            flow = '[Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="%s",dst="%s")/("X"*%d)]' % (
                self.virtio1_mac,
                vlan_id1,
                self.src1,
                self.dst1,
                payload,
            )
            self.tester.scapy_append(
                'wrpcap("%s/pvp_diff_qemu_version.pcap", %s)' % (self.out_path, flow)
            )
            self.tester.scapy_execute()

            tgenInput = []
            port = self.tester.get_local_port(self.pf)
            tgenInput.append(
                (port, port, "%s/pvp_diff_qemu_version.pcap" % self.out_path)
            )
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgenInput, 100, None, self.tester.pktgen
            )
            # set traffic option
            traffic_opt = {
                "delay": 5,
                "duration": self.get_suite_cfg()["test_duration"],
            }
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=traffic_opt
            )
            Mpps = pps / 1000000.0
            line_rate = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))
            self.throughput[qemu_version][frame_size] = Mpps
            # update print table info
            data_row = [
                qemu_version,
                frame_size,
                str(Mpps),
                str(line_rate),
            ]
            self.result_table_add(data_row)
        self.result_table_print()

    def close_testpmd_and_qemu(self):
        """
        stop testpmd in vhost and qemu
        close the qemu
        """
        self.vm_dut.send_expect("quit", "#", 20)
        self.vhost_user.send_expect("quit", "#", 20)
        self.vm.stop()
        self.dut.send_expect("killall -I %s" % self.testpmd_name, "#", 20)
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    def test_perf_vhost_pvp_diff_qemu_version_virtio95_mergeable_path(self):
        """
        Test Case 1: PVP multi qemu version test with virtio 0.95 mergeable path
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        for i in range(len(self.qemu_list)):
            qemu_path = self.qemu_list[i]["path"]
            qemu_version = self.qemu_list[i]["version"]
            self.start_vhost_testpmd()
            self.logger.info("now testing the qemu path of %s" % qemu_path)
            self.start_one_vm(qemu_path=qemu_path, qemu_mode=0)
            self.vm_testpmd_start()
            vlan_id1 = 1000
            self.perf_test(qemu_version, vlan_id1)
            self.close_testpmd_and_qemu()
        self.handle_expected()
        self.handle_results()

    def test_perf_vhost_pvp_diff_qemu_version_virtio10_mergeable_path(self):
        """
        Test Case 2: PVP test with virtio 1.0 mergeable path
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        for i in range(len(self.qemu_list)):
            qemu_path = self.qemu_list[i]["path"]
            qemu_version = self.qemu_list[i]["version"]
            self.start_vhost_testpmd()
            self.logger.info("now testing the qemu path of %s" % qemu_path)
            self.start_one_vm(qemu_path=qemu_path, qemu_mode=1)
            self.vm_testpmd_start()
            vlan_id1 = 1000
            self.perf_test(qemu_version, vlan_id1)
            self.close_testpmd_and_qemu()
        self.handle_expected()
        self.handle_results()

    def test_perf_vhost_pvp_diff_qemu_version_virtio11_mergeable_path(self):
        """
        Test Case 3: PVP test with virtio 1.1 mergeable path
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        for i in range(len(self.qemu_list)):
            qemu_path = self.qemu_list[i]["path"]
            qemu_version = self.qemu_list[i]["version"]
            self.start_vhost_testpmd()
            self.logger.info("now testing the qemu path of %s" % qemu_path)
            self.start_one_vm(qemu_path=qemu_path, qemu_mode=2)
            self.vm_testpmd_start()
            vlan_id1 = 1000
            self.perf_test(qemu_version, vlan_id1)
            self.close_testpmd_and_qemu()
        self.handle_expected()
        self.handle_results()

    def handle_expected(self):
        """
        Update expected numbers to configurate file: $DTS_CFG_FOLDER/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for qemu_version in self.qemu_versions:
                for frame_size in self.frame_sizes:
                    self.expected_throughput[qemu_version][frame_size] = round(
                        self.throughput[qemu_version][frame_size], 3
                    )

    def handle_results(self):
        """
        results handled process:
        1, save to self.test_results
        2, create test results table
        """
        # save test results to self.test_result
        header = self.table_header
        header.append("Expected Throughput(Mpps)")
        header.append("Status")
        self.result_table_create(self.table_header)
        for qv in self.qemu_list:
            qemu_version = qv["version"]
            for frame_size in self.frame_sizes:
                wirespeed = self.wirespeed(self.nic, frame_size, self.nb_ports)
                ret_data = {}
                ret_data[header[0]] = qemu_version
                ret_data[header[1]] = str(frame_size)
                _real = float(self.throughput[qemu_version][frame_size])
                _exp = float(self.expected_throughput[qemu_version][frame_size])
                ret_data[header[2]] = "{:.3f}".format(_real)
                ret_data[header[3]] = "{:.3f}%".format(_real * 100 / wirespeed)
                ret_data[header[4]] = "{:.3f}".format(_exp)
                gap = _exp * -self.gap * 0.01
                if _real > _exp + gap:
                    ret_data[header[5]] = "PASS"
                else:
                    ret_data[header[5]] = "FAIL"
                self.test_result.append(ret_data)

        for test_result in self.test_result:
            table_row = list()
            for i in range(len(header)):
                table_row.append(test_result[header[i]])
            self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()
        self.verify(
            "FAIL" not in self.test_result,
            "Excessive gap between test results and expectations",
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)

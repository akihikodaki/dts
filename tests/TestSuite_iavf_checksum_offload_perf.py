# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

"""
DPDK Test suite.
"""

import os
import re
import time

from framework.exception import VerifyFailure
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestIavfChecksumOffloadPerf(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        PMD prerequisites.
        """
        self.verify(
            self.nic
            in [
                "I40E_25G-25G_SFP28",
                "I40E_40G-QSFP_A",
                "ICE_100G-E810C_QSFP",
                "ICE_25G-E810C_SFP",
                "ICE_25G-E810_XXV_SFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "At least 1 port is required to test")
        self.socket = self.dut.get_numa_id(self.dut_ports[0])

        self.core_offset = 3
        self.test_content = self.get_test_content_from_cfg(self.get_suite_cfg())
        # Get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        self.vfs_mac = ["00:12:34:56:78:0%d" % (i + 1) for i in self.dut_ports]
        self.pmdout = PmdOutput(self.dut)
        # Create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.vf_port_info = {}
        self.vf_create()

    def set_up(self):
        """
        Run before each test case.
        It's more convenient to load suite configuration here than
        set_up_all in debug mode.
        """
        self.test_result = {"header": [], "date": []}

    def parse_test_config(self, config):
        """
        [n]C/[mT]-[i]Q
            n: how many physical core use for polling.
            m: how many cpu thread use for polling, if Hyper-threading disabled
            in BIOS, m equals n, if enabled, m is 2 times as n.
            i: how many queues use per port, so total queues = i x nb_port
        """
        pat = "(.*)/(.*)-(.*)"
        result = re.findall(pat, config)
        if not result:
            msg = f"{config} is wrong format, please check"
            raise VerifyFailure(msg)
        cores, threads, queue = result[0]
        _thread_num = int(int(threads[:-1]) // int(cores[:-1]))

        _thread = str(_thread_num) + "T"
        _cores = str(self.core_offset + int(cores[:-1])) + "C"
        cores_config = "/".join(["1S", _cores, _thread])
        queues_per_port = int(queue[:-1])
        return cores_config, _thread_num, queues_per_port

    def get_test_configs(self, test_parameters):
        configs = []
        frame_sizes_grp = []
        nb_desc = self.get_suite_cfg().get("rxtx_queue_size")
        for test_item, frame_sizes in sorted(test_parameters.items()):
            _frame_sizes = [int(frame_size) for frame_size in frame_sizes]
            frame_sizes_grp.extend([int(item) for item in _frame_sizes])
            cores, thread_num, queues = self.parse_test_config(test_item)
            corelist = self.dut.get_core_list(cores, self.socket)
            core_list = corelist[(self.core_offset - 1) * thread_num :]
            if "2T" in cores:
                core_list = core_list[1:2] + core_list[0::2] + core_list[1::2][1:]
            _core_list = core_list[thread_num - 1 :]
            configs.append(
                [
                    test_item,
                    _core_list,
                    [
                        " --txd={0} --rxd={0}".format(nb_desc)
                        + " --rxq={0} --txq={0}".format(queues)
                        + " --nb-cores={}".format(len(core_list) - thread_num)
                        + " --enable-rx-cksum"
                    ],
                ]
            )
        return configs, sorted(set(frame_sizes_grp))

    def get_test_content_from_cfg(self, test_content):
        configs, frame_sizes = self.get_test_configs(test_content["test_parameters"])
        test_content["configs"] = configs
        test_content["frame_sizes"] = frame_sizes
        return test_content

    def vf_create(self):
        """
        Require enough PF ports, create 1 VF from each PF.
        """
        # Get vf assign method
        vf_driver = self.test_content.get("vf_driver")
        if vf_driver is None:
            vf_driver = self.drivername
        for port_id in self.dut_ports:
            pf_driver = self.dut.ports_info[port_id]["port"].default_driver
            self.dut.generate_sriov_vfs_by_port(port_id, 1, driver=pf_driver)
            pf_pci = self.dut.ports_info[port_id]["port"].pci
            sriov_vfs_port = self.dut.ports_info[port_id].get("vfs_port")
            if not sriov_vfs_port:
                msg = f"failed to create vf on dut port {pf_pci}"
                self.logger.error(msg)
                continue
            self.vf_port_info[port_id] = {
                "pf_pci": pf_pci,
                "vf_pci": self.dut.ports_info[port_id]["port"].get_sriov_vfs_pci(),
            }
            pf_intf = self.dut.ports_info[port_id]["intf"]
            # Set vf mac
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (pf_intf, self.vfs_mac[port_id]), "#"
            )
            self.dut.send_expect("ip link set %s vf 0 trust on" % pf_intf, "#")
            self.dut.send_expect("ip link set %s vf 0 spoofchk off" % pf_intf, "#")
            # Bind vf to dpdk
            try:
                for port in sriov_vfs_port:
                    port.bind_driver(driver=vf_driver)
            except Exception as e:
                self.vf_destroy()
                raise Exception(e)

    def vf_destroy(self):
        """
        Destroy the setup VFs
        """
        if not self.vf_port_info:
            return
        for port_id, _ in self.vf_port_info.items():
            self.dut.destroy_sriov_vfs_by_port(port_id)
            self.dut.ports_info[port_id]["port"].bind_driver(self.drivername)
        self.vf_port_info = None

    def checksum_enable(self, csum, csum_config):
        self.dut.send_expect("stop", "testpmd> ", 15)
        self.dut.send_expect("set fwd csum", "testpmd> ", 15)
        self.dut.send_expect("port stop all", "testpmd> ", 15)
        for port_id in self.dut_ports:
            self.dut.send_expect("csum set ip %s %d" % (csum, port_id), "testpmd> ", 15)
            if csum_config:
                self.dut.send_expect(
                    "csum set udp %s %d" % (csum, port_id), "testpmd> ", 15
                )
                self.dut.send_expect(
                    "csum set outer-ip %s %d" % (csum, port_id), "testpmd> ", 15
                )
                self.dut.send_expect(
                    "csum set outer-udp %s %d" % (csum, port_id), "testpmd> ", 15
                )
                self.dut.send_expect(
                    "csum set parse-tunnel on %d" % (port_id), "testpmd> ", 15
                )
        self.dut.send_expect("port start all", "testpmd> ", 15)
        if csum == "hw":
            self.dut.send_expect("set promisc all on", "testpmd> ", 15)

    def start_testpmd(self, core_list, pci_para, eal, csum, csum_config):
        self.pmdout.start_testpmd(core_list, eal, pci_para, socket=self.socket)
        if csum:
            self.checksum_enable(csum, csum_config)
        self.dut.send_expect("start", "testpmd> ", 15)

    def create_pcaps_file(self, frame_size, checksum, pkt_type):
        """
        Prepare traffic flow
        """
        if pkt_type == "vxlan":
            headers_size = sum(
                [
                    HEADER_SIZE[x]
                    for x in ["eth", "ip", "udp", "vxlan", "eth", "ip", "udp"]
                ]
            )
        else:
            headers_size = sum([HEADER_SIZE[x] for x in ["eth", "ip"]])
        payload_size = frame_size - headers_size
        pcaps = {}
        # Configure the correct or incorrect checksum.
        for _port in self.dut_ports:
            if 1 == len(self.dut_ports):
                if pkt_type == "vxlan":
                    if checksum == "invalid":
                        flow = [
                            'Ether(dst="%s")/IP(dst="192.18.1.%d",chksum=1)/UDP(chksum=1)/VXLAN(vni=0x1)/Ether()/IP(dst="192.18.%d.0,chksum=1)/UDP(chksum=1)/("X"*%d)'
                            % (self.vfs_mac[_port], _port, _port, payload_size)
                        ]
                    else:
                        flow = [
                            'Ether(dst="%s")/IP(dst="192.18.1.%d")/UDP()/VXLAN(vni=0x1)/Ether()/IP(dst="192.18.%d.0)/UDP()/("X"*%d)'
                            % (self.vfs_mac[_port], _port, _port, payload_size)
                        ]
                elif pkt_type == "ipv4":
                    if checksum == "invalid":
                        flow = [
                            'Ether(dst="%s")/IP(dst="192.18.1.%d",chksum=1)/("X"*%d)'
                            % (self.vfs_mac[_port], _port, payload_size)
                        ]
                    else:
                        flow = [
                            'Ether(dst="%s")/IP(dst="192.18.1.%d")/("X"*%d)'
                            % (self.vfs_mac[_port], _port, payload_size)
                        ]
                pcap = os.sep.join([self.output_path, "dst{0}.pcap".format(_port)])
                self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, ",".join(flow)))
                self.tester.scapy_execute()
                pcaps[_port] = []
                pcaps[_port].append(pcap)
            else:
                cnt = 0
                for i in range(len(self.dut_ports) ** 2)[_port * 2 : (_port + 1) * 2]:
                    if pkt_type == "vxlan":
                        if checksum == "invalid":
                            flow = [
                                'Ether(dst="%s")/IP(dst="192.18.%d.%d",chksum=1)/UDP(chksum=1)/VXLAN(vni=0x1)/Ether()/IP(dst="192.18.%d.0",chksum=1)/UDP(chksum=1)/("X"*%d)'
                                % (self.vfs_mac[_port], i, _port, i + 1, payload_size)
                            ]
                        else:
                            flow = [
                                'Ether(dst="%s")/IP(dst="192.18.%d.%d")/UDP()/VXLAN(vni=0x1)/Ether()/IP(dst="192.18.%d.0")/UDP()/("X"*%d)'
                                % (self.vfs_mac[_port], i, _port, i + 1, payload_size)
                            ]
                    elif pkt_type == "ipv4":
                        if checksum == "invalid":
                            flow = [
                                'Ether(dst="%s")/IP(dst="192.18.%d.%d",chksum=1)/("X"*%d)'
                                % (self.vfs_mac[_port], i, _port, payload_size)
                            ]
                        else:
                            flow = [
                                'Ether(dst="%s")/IP(dst="192.18.%d.%d")/("X"*%d)'
                                % (self.vfs_mac[_port], i, _port, payload_size)
                            ]
                    pcap = os.sep.join(
                        [self.output_path, "dst{0}_{1}.pcap".format(_port, cnt)]
                    )
                    self.tester.scapy_append(
                        'wrpcap("%s", [%s])' % (pcap, ",".join(flow))
                    )
                    self.tester.scapy_execute()
                    if _port not in pcaps:
                        pcaps[_port] = []
                    pcaps[_port].append(pcap)
                    cnt += 1
        return pcaps

    def prepare_stream(self, pcaps):
        """
        Create streams for ports, one port one stream
        """
        tgen_input = []
        port_num = len(self.dut_ports)
        if 1 == port_num:
            txIntf = self.tester.get_local_port(self.dut_ports[0])
            rxIntf = txIntf
            for pcap in pcaps[0]:
                tgen_input.append((txIntf, rxIntf, pcap))
        else:
            for rxPort in self.dut_ports:
                if rxPort % port_num == 0 or rxPort**2 == port_num:
                    txIntf = self.tester.get_local_port(self.dut_ports[rxPort + 1])
                    port_id = self.dut_ports[rxPort + 1]
                else:
                    txIntf = self.tester.get_local_port(self.dut_ports[rxPort - 1])
                    port_id = self.dut_ports[rxPort - 1]
                rxIntf = self.tester.get_local_port(self.dut_ports[rxPort])
                for pcap in pcaps[port_id]:
                    tgen_input.append((txIntf, rxIntf, pcap))
        return tgen_input

    def throughput(self, frame_size, checksum, pkt_type):
        pcaps = self.create_pcaps_file(frame_size, checksum, pkt_type)
        tgenInput = self.prepare_stream(pcaps)
        # Get traffic option
        duration = self.test_content.get("test_duration")
        traffic_stop_wait_time = self.test_content.get("traffic_stop_wait_time", 0)
        vm_config = self.set_fields()
        # Clear streams before add new streams
        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgenInput, 100, vm_config, self.tester.pktgen
        )
        # Set traffic option
        traffic_option = {
            "method": "throughput",
            "duration": duration,
        }
        # Run packet generator
        result = self.tester.pktgen.measure(streams, traffic_option)
        time.sleep(traffic_stop_wait_time)
        # Statistics result
        _, pps = result
        self.verify(pps > 0, "No traffic detected")
        pps /= 1000000
        self.logger.info(
            "Throughput of " + "framesize: {}, is: {} Mpps".format(frame_size, pps)
        )
        return pps

    def display_result(self, datas):
        # Display result table
        header_row = ["Fwd Core", "Frame Size", "Throughput", "Rate"]
        self.test_result["header"] = header_row
        self.result_table_create(header_row)
        self.test_result["data"] = []
        for data in datas:
            config, frame_size, pps = data
            linerate = self.wirespeed(self.nic, frame_size, len(self.dut_ports))
            percentage = pps * 100 / linerate
            data_row = [
                config,
                frame_size,
                "{:.3f} Mpps".format(pps),
                "{:.3f}%".format(percentage),
            ]
            self.result_table_add(data_row)
            self.test_result["data"].append(data_row)
        self.result_table_print()

    def perf_test(self, csum="", csum_config="", checksum="", pkt_type="ipv4"):
        """
        Performance Benchmarking test
        """
        pci_para = ""
        for port_id in self.dut_ports:
            pci_para += " -a " + self.vf_port_info[port_id]["vf_pci"][0]
        results = []

        for config, core_list, eal in self.test_content["configs"]:
            self.logger.info(
                ("Executing Test Using cores: {0} of config {1}, ").format(
                    core_list, config
                )
            )
            self.start_testpmd(core_list, pci_para, eal[0], csum, csum_config)
            for frame_size in self.test_content["frame_sizes"]:
                self.logger.info("Test running at framesize: {}".format(frame_size))
                result = self.throughput(frame_size, checksum, pkt_type)
                if result:
                    results.append([config, frame_size, result])
            self.dut.send_expect("stop", "testpmd> ", 15)
            self.dut.send_expect("quit", "# ", 15)
        self.display_result(results)

    def test_perf_disable_checksum_offload_ipv4(self):
        self.perf_test()
        self.perf_test(csum="sw", pkt_type="ipv4")
        self.perf_test(csum="sw", checksum="invalid", pkt_type="ipv4")

    def test_perf_disable_checksum_offload_vxlan(self):
        self.perf_test(csum="sw", pkt_type="vxlan")
        self.perf_test(csum="sw", checksum="invalid", pkt_type="vxlan")

    def test_perf_enable_checksum_offload_ipv4(self):
        self.perf_test(csum="hw", pkt_type="ipv4")
        self.perf_test(csum="hw", checksum="invalid", pkt_type="ipv4")

    def test_perf_enable_checksum_offload_vxlan(self):
        self.perf_test(csum="hw", csum_config="all", pkt_type="vxlan")
        self.perf_test(
            csum="hw", csum_config="all", checksum="invalid", pkt_type="vxlan"
        )

    def set_fields(self):
        """
        Set ip protocol field behavior
        """
        fields_config = {
            "ip": {
                "src": {"action": "random"},
            },
        }
        return fields_config

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.vf_destroy()
        self.dut.kill_all()

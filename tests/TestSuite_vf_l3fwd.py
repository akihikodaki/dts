# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import os
import string
import time

import framework.utils as utils
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestVfL3fwd(TestCase):

    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.requirt_ports_num = len(self.dut_ports)
        global valports
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]

        # Verify that enough ports are available
        self.verify(
            len(valports) == 2 or len(valports) == 4, "Port number must be 2 or 4."
        )
        # define vf's mac address
        self.vfs_mac = ["00:12:34:56:78:0%d" % (i + 1) for i in valports]
        # get socket and cores
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("1S/6C/1T", socket=self.socket)
        self.verify(self.cores is not None, "Requested 6 cores failed")

        # get test parameters: frames size, queues number
        self.perf_params = self.get_suite_cfg()["perf_params"]
        self.frame_sizes = self.perf_params["frame_size"]
        self.queue = self.perf_params["queue_number"][self.nic]

        self.l3fwd_methods = ["lpm"]
        self.l3fwd_test_results = {"header": [], "data": []}

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "pci-stub"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == "pci-stub":
            self.vf_assign_method = "pci-assign"
        else:
            self.vf_assign_method = "vfio-pci"
            self.dut.send_expect("modprobe vfio-pci", "#")

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        self.setup_vf_env_flag = 0

    def setup_vf_env(self, host_driver="default", vf_driver="vfio-pci"):
        """
        require enough PF ports,using kernel or dpdk driver, create 1 VF from each PF.
        """
        if host_driver != "default" and host_driver != "igb_uio":
            self.logger.error("only support kernel driver and igb_uio!")
        self.used_dut_port = [port for port in self.dut_ports]
        self.sriov_vfs_port = []
        for i in valports:
            if host_driver == "default":
                h_driver = self.dut.ports_info[i]["port"].default_driver
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dut_port[i], 1, driver=h_driver
                )
            else:
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dut_port[i], 1, driver=host_driver
                )
            sriov_vfs_port = self.dut.ports_info[self.used_dut_port[i]]["vfs_port"]
            self.sriov_vfs_port.append(sriov_vfs_port)
        # bind vf to vf driver
        try:
            for i in valports:
                for port in self.sriov_vfs_port[i]:
                    port.bind_driver(vf_driver)
            time.sleep(1)
            # set vf mac address.
            if host_driver == "default":
                for i in valports:
                    pf_intf = self.dut.ports_info[i]["port"].get_interface_name()
                    self.dut.send_expect(
                        "ip link set %s vf 0 mac %s" % (pf_intf, self.vfs_mac[i]), "#"
                    )
            else:
                self.host_testpmd = PmdOutput(self.dut)
                eal_param = "--socket-mem=1024,1024 --file-prefix=pf"
                for i in valports:
                    eal_param += " -a %s" % self.dut.ports_info[i]["pci"]
                core_config = self.cores[: len(valports)]
                self.host_testpmd.start_testpmd(core_config, "", eal_param=eal_param)
                for i in valports:
                    self.host_testpmd.execute_cmd(
                        "set vf mac addr %d 0 %s" % (i, self.vfs_mac[i])
                    )
                time.sleep(1)
            self.setup_vf_env_flag = 1
        except Exception as e:
            self.destroy_vf_env()
            raise Exception(e)

    def destroy_vf_env(self):
        """
        destroy the setup VFs
        """
        if getattr(self, "host_testpmd", None):
            self.host_testpmd.execute_cmd("quit", "# ")
            self.host_testpmd = None
        for i in valports:
            if "vfs_port" in self.dut.ports_info[self.used_dut_port[i]].keys():
                self.dut.destroy_sriov_vfs_by_port(self.used_dut_port[i])
                port = self.dut.ports_info[self.used_dut_port[i]]["port"]
                self.used_dut_port[i] = None
        self.setup_vf_env_flag = 0

    def flows(self):
        """
        Return a list of packets that implements the flows described in l3fwd.
        """
        return [
            'IP(src="1.2.3.4",dst="192.18.1.0")',
            'IP(src="1.2.3.4",dst="192.18.1.1")',
            'IP(src="1.2.3.4",dst="192.18.0.0")',
            'IP(src="1.2.3.4",dst="192.18.0.1")',
            'IP(src="1.2.3.4",dst="192.18.3.0")',
            'IP(src="1.2.3.4",dst="192.18.3.1")',
            'IP(src="1.2.3.4",dst="192.18.2.0")',
            'IP(src="1.2.3.4",dst="192.18.2.1")',
        ]

    def create_pacap_file(self, frame_size):
        """
        Prepare traffic flow
        """
        dmac = self.vfs_mac
        smac = ["02:00:00:00:00:0%d" % i for i in valports]
        payload_size = frame_size - HEADER_SIZE["ip"] - HEADER_SIZE["eth"]
        pcaps = {}
        for _port in valports:
            index = valports[_port]
            cnt = 0
            for layer in self.flows()[_port * 2 : (_port + 1) * 2]:
                flow = [
                    'Ether(dst="%s", src="%s")/%s/("X"*%d)'
                    % (dmac[index], smac[index], layer, payload_size)
                ]
                pcap = os.sep.join(
                    [self.output_path, "dst{0}_{1}.pcap".format(index, cnt)]
                )
                self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, ",".join(flow)))
                self.tester.scapy_execute()
                if index not in pcaps:
                    pcaps[index] = []
                pcaps[index].append(pcap)
                cnt += 1
        return pcaps

    def prepare_stream(self, pcaps):
        """
        create streams for ports,one port one stream
        """
        tgen_input = []
        for rxPort in valports:
            if rxPort % len(valports) == 0 or len(valports) % rxPort == 2:
                txIntf = self.tester.get_local_port(valports[rxPort + 1])
                port_id = valports[rxPort + 1]
            else:
                txIntf = self.tester.get_local_port(valports[rxPort - 1])
                port_id = valports[rxPort - 1]
            rxIntf = self.tester.get_local_port(valports[rxPort])
            for pcap in pcaps[port_id]:
                tgen_input.append((txIntf, rxIntf, pcap))
        return tgen_input

    def perf_test(self, cmdline):
        """
        vf l3fwd performance test
        """
        l3fwd_session = self.dut.new_session()
        header_row = ["Frame", "mode", "Mpps", "%linerate"]
        self.l3fwd_test_results["header"] = header_row
        self.result_table_create(header_row)
        self.l3fwd_test_results["data"] = []
        for frame_size in self.frame_sizes:
            pcaps = self.create_pacap_file(frame_size)
            for mode in self.l3fwd_methods:
                info = "Executing l3fwd using %s mode, %d ports, %d frame size.\n" % (
                    mode,
                    len(valports),
                    frame_size,
                )
                self.logger.info(info)
                if frame_size > 1518:
                    cmdline = cmdline + " --max-pkt-len %d" % frame_size
                l3fwd_session.send_expect(cmdline, "L3FWD:", 120)
                # send the traffic and Measure test
                tgenInput = self.prepare_stream(pcaps)

                vm_config = self.set_fields()
                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(
                    tgenInput, 100, vm_config, self.tester.pktgen
                )
                # set traffic option
                traffic_opt = {"delay": 30}
                # _, pps = self.tester.traffic_generator_throughput(tgenInput, rate_percent=100, delay=30)
                _, pps = self.tester.pktgen.measure_throughput(
                    stream_ids=streams, options=traffic_opt
                )
                self.verify(pps > 0, "No traffic detected")
                pps /= 1000000.0
                linerate = self.wirespeed(self.nic, frame_size, len(valports))
                percentage = pps * 100 / linerate
                # Stop l3fwd
                l3fwd_session.send_expect("^C", "#")
                time.sleep(5)
                data_row = [frame_size, mode, str(pps), str(percentage)]
                self.result_table_add(data_row)
                self.l3fwd_test_results["data"].append(data_row)

        self.dut.close_session(l3fwd_session)
        self.result_table_print()

    def measure_vf_performance(self, host_driver="default", vf_driver="vfio-pci"):
        """
        start l3fwd and run the perf test
        """
        self.setup_vf_env(host_driver, vf_driver)
        eal_param = ""
        for i in valports:
            eal_param += " -a " + self.sriov_vfs_port[i][0].pci
        port_mask = utils.create_mask(self.dut_ports)

        # for IIntel® Ethernet 700 Series: XL710, XXV710, use 2c/2q per VF port for performance test ,
        # for IIntel® Ethernet 700 Series: X710, 82599/500 Series, use 1c/1q per VF port for performance test
        core_list = self.cores[-len(valports) * self.queue :]
        core_mask = utils.create_mask(core_list)
        self.logger.info("Executing Test Using cores: %s" % core_list)
        queue_config = ""
        m = 0
        for i in valports:
            for j in range(self.queue):
                queue_config += "({0}, {1}, {2}),".format(i, j, core_list[m])
                m += 1
        app_name = self.dut.apps_name["l3fwd"]
        cmdline = (
            app_name
            + "-c {0} -n 4 {1} -- -p {2} --config '{3}' --parse-ptype".format(
                core_mask, eal_param, port_mask, queue_config
            )
        )
        self.perf_test(cmdline)

    def get_kernel_pf_vf_driver(self):
        if self.vf_driver == "igb_uio" or self.vf_driver == "vfio-pci":
            vf_driver = self.vf_driver
        elif self.drivername == "igb_uio" or self.drivername == "vfio-pci":
            vf_driver = self.drivername
        else:
            vf_driver = "vfio-pci"
        return vf_driver

    def test_perf_kernel_pf_dpdk_vf_perf_host_only(self):
        self.set_rxtx_descriptor_2048_and_rebuild_l3fwd()
        self.measure_vf_performance(
            host_driver="default", vf_driver=self.get_kernel_pf_vf_driver()
        )

    def test_perf_dpdk_pf_dpdk_vf_perf_host_only(self):
        for idx in self.dut_ports:
            self.verify(
                self.dut.ports_info[idx]["port"].default_driver != "ice",
                "Intel® Ethernet 800 Series do not support generate vfs from igb_uio",
            )

        self.set_rxtx_descriptor_2048_and_rebuild_l3fwd()
        if self.drivername != "igb_uio":
            self.logger.warning(
                "Use igb_uio as host driver for testing instead of %s" % self.drivername
            )

        self.dut.setup_modules_linux(self.target, "igb_uio", "")
        self.measure_vf_performance(host_driver="igb_uio", vf_driver="igb_uio")

    def test_perf_kernel_pf_dpdk_iavf_perf_host_only(self):
        """
        Need to change dpdk code to test Intel® Ethernet 700 Series iavf.
        Intel® Ethernet 800 Series iavf testing is same as Intel® Ethernet 700 Series VF,
        so use dpdk_pf_dpdk_vf_perf_host_only to test Intel® Ethernet 800 Series iavf
        """
        for idx in self.dut_ports:
            self.verify(
                self.dut.ports_info[idx]["port"].default_driver == "i40e",
                "The case is only designed for Intel® Ethernet 700 Series",
            )

        self.set_rxtx_descriptor_2048_and_rebuild_l3fwd()
        self.measure_vf_performance(
            host_driver="default", vf_driver=self.get_kernel_pf_vf_driver()
        )

    def set_rxtx_descriptor_2048_and_rebuild_l3fwd(self):
        """
        Set RX/TX descriptor to 2048 and rebuild l3fwd
        """
        self.logger.info(
            "Configure RX/TX descriptor to 2048, and re-build ./examples/l3fwd"
        )
        self.dut.send_expect(
            "sed -i -e 's/define RTE_TEST_RX_DESC_DEFAULT.*$/"
            + "define RTE_TEST_RX_DESC_DEFAULT 2048/' ./examples/l3fwd/l3fwd.h",
            "#",
            20,
        )
        self.dut.send_expect(
            "sed -i -e 's/define RTE_TEST_TX_DESC_DEFAULT.*$/"
            + "define RTE_TEST_TX_DESC_DEFAULT 2048/' ./examples/l3fwd/l3fwd.h",
            "#",
            20,
        )
        out = self.dut.build_dpdk_apps("./examples/l3fwd")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_fields(self):
        """
        set ip protocol field behavior
        """
        fields_config = {
            "ip": {
                "src": {"action": "random"},
            },
        }
        return fields_config

    def tear_down(self):
        self.destroy_vf_env()

    def tear_down_all(self):
        self.dut.bind_interfaces_linux(self.drivername)

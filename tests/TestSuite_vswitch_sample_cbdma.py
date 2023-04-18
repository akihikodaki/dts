# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2021 Intel Corporation
#

"""
DPDK Test suite.
"""

import os
import random
import re
import string
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.virt_common import VM
from tests.virtio_common import basic_common as BC
from tests.virtio_common import cbdma_common as CC


class TestVswitchSampleCBDMA(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.build_vhost_app()
        self.tester_tx_port_num = 1
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("all", socket=self.ports_socket)
        self.vhost_core_list = self.cores[0:2]
        self.vhost_core_range = "%s-%s" % (
            self.vhost_core_list[0],
            self.vhost_core_list[-1],
        )
        self.vuser0_core_list = self.cores[2:4]
        self.vuser1_core_list = self.cores[4:6]
        self.mem_channels = self.dut.get_memory_channels()
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.txItf = self.tester.get_interface(txport)
        self.virtio_dst_mac0 = "00:11:22:33:44:10"
        self.virtio_dst_mac1 = "00:11:22:33:44:11"
        self.vm_dst_mac0 = "52:54:00:00:00:01"
        self.vm_dst_mac1 = "52:54:00:00:00:02"
        self.vm_num = 2
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.virtio_user1_pmd = PmdOutput(self.dut, self.virtio_user1)
        self.random_string = string.ascii_letters + string.digits
        self.virtio_ip0 = "1.1.1.2"
        self.virtio_ip1 = "1.1.1.3"
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"]
        self.BC = BC(self)
        self.CC = CC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.table_header = ["Frame Size(Byte)", "Mode", "Throughput(Mpps)"]
        self.result_table_create(self.table_header)
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -I dpdk-vhost", "#", 20)
        self.dut.send_expect("killall -I dpdk-testpmd", "#", 20)
        self.dut.send_expect("killall -I qemu-system-x86_64", "#", 20)
        self.vm_dut = []
        self.vm = []

    def build_vhost_app(self):
        out = self.dut.build_dpdk_apps("./examples/vhost")
        self.verify("Error" not in out, "compilation vhost error")

    def start_vhost_app(
        self, cbdma_num, socket_num, dmas_info, cbdmas, client_mode=False
    ):
        """
        launch the vhost app on vhost side
        """
        self.app_path = self.dut.apps_name["vhost"]
        socket_file_param = ""
        for item in range(socket_num):
            socket_file_param += "--socket-file ./vhost-net{} ".format(item)
        allow_pci = [self.dut.ports_info[0]["pci"]]
        for item in range(cbdma_num):
            allow_pci.append(cbdmas[item])
        allow_option = ""
        for item in allow_pci:
            allow_option += " -a {}".format(item)
        params = (
            " -l {} -n {} {} -- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 "
            + socket_file_param
            + "--dmas [{}] --total-num-mbufs 600000"
        ).format(
            self.vhost_core_range,
            self.mem_channels,
            allow_option,
            dmas_info,
        )
        if client_mode:
            params = params + " --client"
        self.command_line = self.app_path + params
        self.vhost_user.send_command(self.command_line)
        time.sleep(3)

    def start_virtio_testpmd_with_vhost_net0(self, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net0
        """
        if self.BC.check_2M_hugepage_size():
            eal_param += " --single-file-segments"
        self.virtio_user0_pmd.start_testpmd(
            cores=self.vuser0_core_list,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user0",
            fixed_prefix=True,
        )

    def start_virtio_testpmd_with_vhost_net1(self, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net1
        """
        if self.BC.check_2M_hugepage_size():
            eal_param += " --single-file-segments"
        self.virtio_user1_pmd.start_testpmd(
            cores=self.vuser1_core_list,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user1",
            fixed_prefix=True,
        )

    def start_vms(
        self,
        mrg_rxbuf=True,
        packed=False,
        server_mode=False,
        set_target=True,
        bind_dev=True,
    ):
        """
        start two VM, each VM has one virtio device
        """
        mrg_rxbuf = "on" if mrg_rxbuf else "off"
        for i in range(self.vm_num):
            vm_dut = None
            if not packed:
                modern = "true" if i == 0 else "false"
                setting_format = "disable-modern=%s,mrg_rxbuf=%s,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
            else:
                modern = "false"
                setting_format = "disable-modern=%s,mrg_rxbuf=%s,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
            setting_args = setting_format % (modern, mrg_rxbuf)
            vm_info = VM(self.dut, "vm%d" % i, "vhost_sample")
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            if server_mode:
                vm_params["opt_path"] = "./vhost-net%d" % i + ",server"
            else:
                vm_params["opt_path"] = "./vhost-net%d" % i
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            vm_params["opt_settings"] = setting_args
            vm_info.set_vm_device(**vm_params)
            time.sleep(3)
            try:
                vm_dut = vm_info.start(set_target=set_target, bind_dev=bind_dev)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print((utils.RED("Failure for %s" % str(e))))
                raise e
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def start_vm_testpmd(self, pmd_session):
        """
        launch the testpmd in vm
        """
        self.vm_cores = [1, 2]
        param = "--rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024"
        pmd_session.start_testpmd(cores=self.vm_cores, param=param)

    def repeat_bind_driver(self, dut, repeat_times=50):
        i = 0
        while i < repeat_times:
            dut.unbind_interfaces_linux()
            dut.bind_interfaces_linux(driver="virtio-pci")
            dut.bind_interfaces_linux(driver="vfio-pci")
            i += 1

    def send_vlan_packet(self, dts_mac, pkt_size=64, pkt_count=1):
        """
        Send a vlan packet with vlan id 1000
        """
        pkt = Packet(pkt_type="VLAN_UDP", pkt_len=pkt_size)
        pkt.config_layer("ether", {"dst": dts_mac})
        pkt.config_layer("vlan", {"vlan": 1000})
        pkt.send_pkt(self.tester, tx_port=self.txItf, count=pkt_count)

    def verify_receive_packet(self, pmd_session, expected_pkt_count):
        out = pmd_session.execute_cmd("show port stats all")
        rx_num = re.compile("RX-packets: (.*?)\s+?").findall(out, re.S)
        self.verify(
            (int(rx_num[0]) >= int(expected_pkt_count)),
            "Can't receive enough packets from tester",
        )

    def config_stream(self, frame_size, dst_mac_list):
        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        for dst_mac in dst_mac_list:
            payload_size = frame_size - self.headers_size
            pkt = Packet(pkt_type="VLAN_UDP", pkt_len=payload_size)
            pkt.config_layer("ether", {"dst": dst_mac})
            pkt.config_layer("vlan", {"vlan": 1000})
            pcap = os.path.join(
                self.out_path, "vswitch_sample_cbdma_%s_%s.pcap" % (dst_mac, frame_size)
            )
            pkt.save_pcapfile(self.tester, pcap)
            tgen_input.append((rx_port, tx_port, pcap))
        return tgen_input

    def perf_test(self, frame_sizes, dst_mac_list):
        test_result = {}
        for frame_size in frame_sizes:
            self.logger.info(
                "Test running at parameters: " + "framesize: {}".format(frame_size)
            )
            tgenInput = self.config_stream(frame_size, dst_mac_list)
            # clear streams before add new streams
            self.tester.pktgen.clear_streams()
            # run packet generator
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgenInput, 100, None, self.tester.pktgen
            )
            # set traffic option
            traffic_opt = {"duration": 5}
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=traffic_opt
            )
            throughput = pps / 1000000.0
            test_result[frame_size] = throughput
        return test_result

    def pvp_test_with_cbdma(self):
        frame_sizes = [64, 128, 256, 512, 1024, 1280, 1518]
        dst_mac_list = [self.virtio_dst_mac0]
        perf_result = self.perf_test(frame_sizes, dst_mac_list)
        return perf_result

    def let_vswitch_know_mac(self, virtio_pmd, relaunch=False):
        if not relaunch:
            virtio_pmd.execute_cmd("set fwd mac")
            virtio_pmd.execute_cmd("start tx_first")
        else:
            virtio_pmd.execute_cmd("stop")
            virtio_pmd.execute_cmd("start tx_first")

    def test_perf_pvp_perfromance_check_with_cbdma_channel_using_vhost_async_driver(
        self,
    ):
        """
        Test Case 1: PVP performance check with CBDMA channel using vhost async driver
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd0@%s" % (cbdmas[0], cbdmas[1])
        self.start_vhost_app(
            cbdma_num=2,
            socket_num=1,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )

        # packed ring path
        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,server=1"
        virtio0_param = "--rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1"
        self.start_virtio_testpmd_with_vhost_net0(
            eal_param=virtio0_eal_param, param=virtio0_param
        )
        self.let_vswitch_know_mac(virtio_pmd=self.virtio_user0_pmd, relaunch=False)
        packed_ring_result = self.pvp_test_with_cbdma()

        # split ring path
        self.virtio_user0_pmd.execute_cmd("quit", "# ")
        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=0,in_order=1,vectorized=1,server=1"
        virtio0_param = "--rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1"
        self.start_virtio_testpmd_with_vhost_net0(
            eal_param=virtio0_eal_param, param=virtio0_param
        )
        self.let_vswitch_know_mac(virtio_pmd=self.virtio_user0_pmd)
        split_ring_reult = self.pvp_test_with_cbdma()

        for key in packed_ring_result.keys():
            perf_result.append([key, "packed_ring", packed_ring_result[key]])

        for key in split_ring_reult.keys():
            perf_result.append([key, "split_ring", split_ring_reult[key]])

        for table_row in perf_result:
            self.result_table_add(table_row)

        self.result_table_print()

    def config_stream_imix(self, frame_sizes, dst_mac_list):
        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        for dst_mac in dst_mac_list:
            for frame_size in frame_sizes:
                payload_size = frame_size - self.headers_size
                pkt = Packet()
                pkt.assign_layers(["ether", "ipv4", "raw"])
                pkt.config_layers(
                    [
                        ("ether", {"dst": "%s" % dst_mac}),
                        ("ipv4", {"src": "1.1.1.1"}),
                        ("raw", {"payload": ["01"] * int("%d" % payload_size)}),
                    ]
                )
                pcap = os.path.join(
                    self.out_path,
                    "vswitch_sample_cbdma_%s_%s.pcap" % (dst_mac, frame_size),
                )
                pkt.save_pcapfile(self.tester, pcap)
                tgen_input.append((rx_port, tx_port, pcap))
        return tgen_input

    def perf_test_imix(self, frame_sizes, dst_mac_list):
        test_result = {}
        tgenInput = self.config_stream_imix(frame_sizes, dst_mac_list)
        fields_config = {
            "ip": {
                "src": {"action": "random"},
            },
        }
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # run packet generator
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgenInput, 100, fields_config, self.tester.pktgen
        )
        # set traffic option
        traffic_opt = {"delay": 5, "duration": 5}
        _, pps = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=traffic_opt
        )
        throughput = pps / 1000000.0
        test_result["imix"] = throughput
        return test_result

    def pvp_test_with_multi_cbdma(self):
        frame_sizes = [64, 128, 256, 512, 1024, 1280, 1518]
        dst_mac_list = [self.virtio_dst_mac0, self.virtio_dst_mac1]
        perf_result = self.perf_test_imix(frame_sizes, dst_mac_list)
        return perf_result

    def test_perf_pvp_test_with_2_vms_using_vhost_async_driver(self):
        """
        Test Case 2: PVP test with two VMs using vhost async driver
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1"
        virtio0_param = "--rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1"
        self.start_virtio_testpmd_with_vhost_net0(
            eal_param=virtio0_eal_param, param=virtio0_param
        )

        virtio1_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=./vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1"
        virtio1_param = "--rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1"
        self.start_virtio_testpmd_with_vhost_net1(
            eal_param=virtio1_eal_param, param=virtio1_param
        )
        self.let_vswitch_know_mac(virtio_pmd=self.virtio_user0_pmd, relaunch=False)
        self.let_vswitch_know_mac(virtio_pmd=self.virtio_user1_pmd, relaunch=False)

        before_relunch = self.pvp_test_with_multi_cbdma()

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas_info = "txd0@%s,rxd1@%s" % (cbdmas[0], cbdmas[1])
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        self.let_vswitch_know_mac(virtio_pmd=self.virtio_user0_pmd, relaunch=True)
        self.let_vswitch_know_mac(virtio_pmd=self.virtio_user1_pmd, relaunch=True)
        after_relunch = self.pvp_test_with_multi_cbdma()

        for key in before_relunch.keys():
            perf_result.append(["imix", "Before Re-launch vhost", before_relunch[key]])
        for key in after_relunch.keys():
            perf_result.append(["imix", "After Re-launch vhost", after_relunch[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        self.verify(
            (
                abs(before_relunch["imix"] - after_relunch["imix"])
                / before_relunch["imix"]
            )
            < 0.5,
            "perf data have drop after re-launch vhost",
        )

    def get_receive_throughput(self, pmd_session, count=10):
        i = 0
        while i < count:
            pmd_session.execute_cmd("show port stats all")
            i += 1
        else:
            out = pmd_session.execute_cmd("show port stats all")
            pmd_session.execute_cmd("stop")
            rx_throughput = re.compile("Rx-pps: \s+(.*?)\s+?").findall(out, re.S)
        return float(rx_throughput[0]) / 1000000.0

    def set_testpmd0_param(self, pmd_session, eth_peer_mac):
        pmd_session.execute_cmd("set fwd mac")
        pmd_session.execute_cmd("start tx_first")
        pmd_session.execute_cmd("stop")
        pmd_session.execute_cmd("set eth-peer 0 %s" % eth_peer_mac)
        pmd_session.execute_cmd("start")

    def set_testpmd1_param(self, pmd_session, eth_peer_mac):
        pmd_session.execute_cmd("set fwd mac")
        pmd_session.execute_cmd("set eth-peer 0 %s" % eth_peer_mac)

    def send_pkts_from_testpmd1(self, pmd_session, pkt_len):
        if pkt_len in [64, 2000]:
            pmd_session.execute_cmd("set txpkts %s" % pkt_len)
        elif pkt_len == 8000:
            pmd_session.execute_cmd("set txpkts 2000,2000,2000,2000")
        elif pkt_len == "imix":
            pmd_session.execute_cmd("set txpkts 64,256,2000,64,256,2000")
        pmd_session.execute_cmd("start tx_first")

    def vm2vm_check_with_two_cbdma(self):
        frame_sizes = [64, 2000, 8000, "imix"]
        self.set_testpmd0_param(self.virtio_user0_pmd, self.virtio_dst_mac1)
        self.set_testpmd1_param(self.virtio_user1_pmd, self.virtio_dst_mac0)

        rx_throughput = {}
        for frame_size in frame_sizes:
            self.send_pkts_from_testpmd1(
                pmd_session=self.virtio_user1_pmd, pkt_len=frame_size
            )
            rx_pps = self.get_receive_throughput(pmd_session=self.virtio_user1_pmd)
            rx_throughput[frame_size] = rx_pps
        return rx_throughput

    def test_vm2vm_virtio_user_forwarding_test_using_vhost_async_driver(self):
        """
        Test Case 3: VM2VM virtio-user forwarding test using vhost async driver
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,packed_vq=1"
        virtio0_param = "--rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1"
        self.start_virtio_testpmd_with_vhost_net0(
            eal_param=virtio0_eal_param, param=virtio0_param
        )

        virtio1_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:11,path=./vhost-net1,queues=1,server=1,mrg_rxbuf=1,in_order=1,vectorized=1"
        virtio1_param = "--rxq=1 --txq=1 --txd=1024 --rxd=1024 --nb-cores=1"
        self.start_virtio_testpmd_with_vhost_net1(
            eal_param=virtio1_eal_param, param=virtio1_param
        )
        before_relunch_result = self.vm2vm_check_with_two_cbdma()

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas_info = "txd0@%s,rxd1@%s" % (cbdmas[0], cbdmas[1])
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        self.virtio_user0_pmd.execute_cmd("stop")
        after_relunch_result = self.vm2vm_check_with_two_cbdma()

        for key in before_relunch_result.keys():
            perf_result.append(
                [key, "Before Re-launch vhost", before_relunch_result[key]]
            )
        for key in after_relunch_result.keys():
            perf_result.append(
                [key, "After Re-launch vhost ", after_relunch_result[key]]
            )
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def vm2vm_check_with_two_vhost_device(self):
        rx_throughput = {}
        self.frame_sizes = [64, 2000, 8000, "imix"]
        for frame_size in self.frame_sizes:
            self.send_pkts_from_testpmd1(pmd_session=self.vm1_pmd, pkt_len=frame_size)
            rx_pps = self.get_receive_throughput(pmd_session=self.vm1_pmd)
            rx_throughput[frame_size] = rx_pps
        return rx_throughput

    def start_vms_testpmd_and_test(
        self, mrg_rxbuf=True, need_start_vm=True, packed=False
    ):
        if need_start_vm:
            self.start_vms(
                mrg_rxbuf=mrg_rxbuf,
                packed=packed,
                server_mode=True,
                set_target=True,
                bind_dev=True,
            )
            self.vm0_pmd = PmdOutput(self.vm_dut[0])
            self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(self.vm0_pmd)
        self.start_vm_testpmd(self.vm1_pmd)
        self.set_testpmd0_param(self.vm0_pmd, self.vm_dst_mac1)
        self.set_testpmd1_param(self.vm1_pmd, self.vm_dst_mac0)
        perf_result = self.vm2vm_check_with_two_vhost_device()
        self.vm0_pmd.quit()
        self.vm1_pmd.quit()
        return perf_result

    def test_vm2vm_virtio_pmd_split_ring_test_with_cbdma_channels_register_and_unregister_stable_check(
        self,
    ):
        """
        Test Case 4: VM2VM virtio-pmd split ring test with cbdma channels register/unregister stable check
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        before_rebind = self.start_vms_testpmd_and_test(
            mrg_rxbuf=True, need_start_vm=True, packed=False
        )

        # repeat bind 50 time from virtio-pci to vfio-pci
        self.repeat_bind_driver(dut=self.vm_dut[0], repeat_times=50)
        self.repeat_bind_driver(dut=self.vm_dut[1], repeat_times=50)

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas_info = "txd0@%s,rxd1@%s" % (cbdmas[0], cbdmas[3])
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        after_rebind = self.start_vms_testpmd_and_test(
            mrg_rxbuf=True, need_start_vm=False, packed=False
        )

        for key in before_rebind.keys():
            perf_result.append([key, "Before rebind driver", before_rebind[key]])

        for key in after_rebind.keys():
            perf_result.append([key, "After rebind driver", after_rebind[key]])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        for i in perf_result:
            self.verify(i[2] > 0, "%s Frame Size(Byte) is less than 0 Mpps" % i[0])

    def start_iperf_and_scp_test_in_vms(
        self, mrg_rxbuf=False, need_start_vm=True, packed=False, server_mode=False
    ):
        if need_start_vm:
            self.start_vms(
                mrg_rxbuf=mrg_rxbuf,
                packed=packed,
                server_mode=server_mode,
                set_target=True,
                bind_dev=False,
            )
            self.vm0_pmd = PmdOutput(self.vm_dut[0])
            self.vm1_pmd = PmdOutput(self.vm_dut[1])
            self.BC.config_2_vms_ip()
        self.BC.check_scp_file_between_2_vms(file_size=1)
        self.BC.run_iperf_test_between_2_vms()
        iperfdata = self.BC.check_iperf_result_between_2_vms()
        return iperfdata

    def test_vm2vm_virtio_pmd_packed_ring_test_with_cbdma_channels_register_and_unregister_stable_check(
        self,
    ):
        """
        Test Case 5: VM2VM virtio-pmd packed ring test with cbdma channels register/unregister stable check
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        before_rebind = self.start_vms_testpmd_and_test(
            mrg_rxbuf=True, need_start_vm=True, packed=True
        )

        # repeat bind 50 time from virtio-pci to vfio-pci
        self.repeat_bind_driver(dut=self.vm_dut[0], repeat_times=50)
        self.repeat_bind_driver(dut=self.vm_dut[1], repeat_times=50)

        after_rebind = self.start_vms_testpmd_and_test(
            mrg_rxbuf=True, need_start_vm=False, packed=True
        )

        for key in before_rebind.keys():
            perf_result.append([key, "Before rebind driver", before_rebind[key]])

        for key in after_rebind.keys():
            perf_result.append([key, "After rebind driver", after_rebind[key]])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        for i in perf_result:
            self.verify(i[2] > 0, "%s Frame Size(Byte) is less than 0 Mpps" % i[0])

    def test_vm2vm_virtio_net_split_ring_test_with_4_cbdma_channels_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 6: VM2VM virtio-net split ring test with 4 cbdma channels and iperf stable check
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            mrg_rxbuf=False, need_start_vm=True, packed=False, server_mode=True
        )
        perf_result.append(["split ring", "Before relaunch test", before_relaunch])

        self.vhost_user.send_expect("^C", "# ", 20)
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )

        for _ in range(5):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["split ring", "After  rerun test", rerun_result])

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas_info = "txd0@%s,rxd1@%s" % (cbdmas[0], cbdmas[1])
        self.start_vhost_app(
            cbdma_num=2,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )

        after_relaunch = self.start_iperf_and_scp_test_in_vms(
            mrg_rxbuf=False, need_start_vm=False, packed=False, server_mode=True
        )

        perf_result.append(["split ring", "After relaunch test", after_relaunch])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_vm2vm_virtio_net_packed_ring_test_with_4_cbdma_channels_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 7: VM2VM virtio-net packed ring test with 4 cbdma channels and iperf stable check
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        self.start_vhost_app(
            cbdma_num=4,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=True,
        )
        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            mrg_rxbuf=False, need_start_vm=True, packed=True, server_mode=True
        )

        perf_result.append(["packed ring", "Before rerun test", before_relaunch])

        for _ in range(5):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "After  rerun test", rerun_result])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_vm2vm_virtio_net_packed_ring_test_with_2_cbdma_channels_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 8: VM2VM virtio-net packed ring test with 2 cbdma channels and iperf stable check
        """
        perf_result = []
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas_info = "txd0@%s,rxd1@%s" % (cbdmas[0], cbdmas[1])
        self.start_vhost_app(
            cbdma_num=2,
            socket_num=2,
            dmas_info=dmas_info,
            cbdmas=cbdmas,
            client_mode=False,
        )
        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            mrg_rxbuf=False, need_start_vm=True, packed=True, server_mode=False
        )
        perf_result.append(["packed ring", "Before rerun test", before_relaunch])

        for _ in range(5):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "After  rerun test", rerun_result])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def close_all_session(self):
        if getattr(self, "vhost_user", None):
            self.dut.close_session(self.vhost_user)
        if getattr(self, "virtio-user0", None):
            self.dut.close_session(self.virtio_user0)
        if getattr(self, "virtio-user1", None):
            self.dut.close_session(self.virtio_user1)

    def tear_down(self):
        """
        Run after each test case.
        """
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vhost_user.send_expect("^C", "# ", 20)
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
        self.close_all_session()

# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

import _thread
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.virt_common import VM

from .virtio_common import basic_common as BC
from .virtio_common import cbdma_common as CC


class TestVhostAsyncRobustCbdma(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.vm_num = 2
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list("all", self.ports_socket)
        self.vhost_user_core = self.core_list[0:5]
        self.virtio_user0_core = self.core_list[6:11]
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.virtio_mac = "00:11:22:33:44:10"
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["tcp"]
        self.CC = CC(self)
        self.BC = BC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.flag = None
        self.vm_dut = []
        self.vm = []
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.CC.bind_cbdma_to_kernel_driver()

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_vhost_user_testpmd(
        self,
        cores,
        param="",
        eal_param="",
        ports="",
        set_fwd_mode=True,
        exec_start=True,
    ):
        """
        launch the testpmd as virtio with vhost_user
        """
        self.vhost_user_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            ports=ports,
            prefix="vhost-user",
            fixed_prefix=True,
        )
        if set_fwd_mode:
            self.vhost_user_pmd.execute_cmd("set fwd mac")
        if exec_start:
            self.vhost_user_pmd.execute_cmd("start")

    def start_virtio_user0_testpmd(self, cores, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net0
        """
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        self.virtio_user0_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user0",
            fixed_prefix=True,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")

    def start_to_send_packets(self, duration):
        """
        Send imix packet with packet generator and verify
        """
        frame_sizes = [64, 128, 256, 512, 1024, 1518]
        tgenInput = []
        for frame_size in frame_sizes:
            payload_size = frame_size - self.headers_size
            port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {
                "ip": {
                    "src": {"action": "random"},
                },
            }
            pkt = Packet()
            pkt.assign_layers(["ether", "ipv4", "tcp", "raw"])
            pkt.config_layers(
                [
                    ("ether", {"dst": "%s" % self.virtio_mac}),
                    ("ipv4", {"src": "1.1.1.1"}),
                    ("raw", {"payload": ["01"] * int("%d" % payload_size)}),
                ]
            )
            pkt.save_pcapfile(
                self.tester,
                "%s/%s_%s.pcap" % (self.out_path, self.suite_name, frame_size),
            )
            tgenInput.append(
                (
                    port,
                    port,
                    "%s/%s_%s.pcap" % (self.out_path, self.suite_name, frame_size),
                )
            )

        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgenInput, 100, fields_config, self.tester.pktgen
        )
        traffic_opt = {"delay": 5, "duration": duration, "rate": 100}
        _, self.flag = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=traffic_opt
        )

    def calculate_avg_throughput(self, pmd, reg="Tx-pps"):
        """
        calculate the average throughput
        """
        results = 0.0
        pmd.execute_cmd("show port stats 0", "testpmd>", 60)
        time.sleep(5)
        pmd.execute_cmd("show port stats 0", "testpmd>", 60)
        for _ in range(10):
            out = pmd.execute_cmd("show port stats 0", "testpmd>", 60)
            time.sleep(5)
            lines = re.search("%s:\s*(\d*)" % reg, out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.logger.info("vhost-user testpmd port 0 Tx-pps: %s" % Mpps)
        self.verify(Mpps > 0, "port can not receive packets")
        return Mpps

    def check_packets_after_relaunch_virtio_user_testpmd(
        self, duration, cores, eal_param="", param=""
    ):
        # ixia send packets times equal to duration time
        start_time = time.time()
        _thread.start_new_thread(self.start_to_send_packets, (duration,))
        # wait the ixia begin to send packets
        time.sleep(10)
        if time.time() - start_time > duration:
            self.logger.error(
                "The ixia has stop to send packets, please change the delay time of ixia"
            )
            return False
        # get the throughput as the expected value before relaunch the virtio-user0 testpmd
        expected_throughput = self.calculate_avg_throughput(
            pmd=self.vhost_user_pmd, reg="Tx-pps"
        )
        # quit and relaunch virtio-user0 testpmd
        self.logger.info(
            "quit and relaunch virtio-user0 testpmd during the pktgen sending packets"
        )
        self.virtio_user0_pmd.quit()
        self.start_virtio_user0_testpmd(cores=cores, eal_param=eal_param, param=param)
        result_throughput = self.calculate_avg_throughput(
            pmd=self.vhost_user_pmd, reg="Tx-pps"
        )
        # delta value and accepted tolerance in percentage
        delta = result_throughput - expected_throughput
        gap = expected_throughput * -0.05
        delta = float(delta)
        gap = float(gap)
        self.logger.info("Accept tolerance are (Mpps) %f" % gap)
        self.logger.info("Throughput Difference are (Mpps) %f" % delta)
        self.verify(
            (result_throughput > expected_throughput + gap),
            "result_throughput: %s is less than the expected_throughput: %s"
            % (result_throughput, result_throughput),
        )
        # stop vhost-user port then quit and relaunch virtio-user0 testpmd
        self.logger.info(
            "stop vhost-user port then quit and relaunch virtio-user0 testpmd during the pktgen sending packets"
        )
        self.vhost_user_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.quit()
        self.start_virtio_user0_testpmd(cores=cores, eal_param=eal_param, param=param)
        self.vhost_user_pmd.execute_cmd("start")
        # delta value and accepted tolerance in percentage
        result_throughput = self.calculate_avg_throughput(
            pmd=self.vhost_user_pmd, reg="Tx-pps"
        )
        delta = result_throughput - expected_throughput
        gap = expected_throughput * -0.05
        delta = float(delta)
        gap = float(gap)
        self.logger.info("Accept tolerance are (Mpps) %f" % gap)
        self.logger.info("Throughput Difference are (Mpps) %f" % delta)
        self.verify(
            (result_throughput > expected_throughput + gap),
            "result_throughput: %s is less than the expected_throughput: %s"
            % (result_throughput, result_throughput),
        )
        # wait ixia thread exit
        self.logger.info("wait the thread of ixia to exit")
        while 1:
            if self.flag is not None:
                break
            time.sleep(5)
        return True

    def check_packets_after_relaunch_vhost_user_testpmd(
        self, duration, cores, eal_param="", param="", ports=""
    ):
        # ixia send packets times equal to duration time
        start_time = time.time()
        _thread.start_new_thread(self.start_to_send_packets, (duration,))
        # wait the ixia begin to send packets
        time.sleep(10)
        if time.time() - start_time > duration:
            self.logger.error(
                "The ixia has stop to send packets, please change the delay time of ixia"
            )
            return False
        # get the throughput as the expected value before relaunch the virtio-user0 testpmd
        expected_throughput = self.calculate_avg_throughput(
            pmd=self.vhost_user_pmd, reg="Tx-pps"
        )
        # quit and relaunch vhost-user testpmd
        self.logger.info(
            "quit and relaunch vhost-user testpmd during the pktgen sending packets"
        )
        self.vhost_user_pmd.quit()
        self.start_vhost_user_testpmd(
            cores=cores, eal_param=eal_param, param=param, ports=ports
        )

        result_throughput = self.calculate_avg_throughput(
            pmd=self.vhost_user_pmd, reg="Tx-pps"
        )
        # delta value and accepted tolerance in percentage
        delta = result_throughput - expected_throughput
        gap = expected_throughput * -0.05
        delta = float(delta)
        gap = float(gap)
        self.logger.info("Accept tolerance are (Mpps) %f" % gap)
        self.logger.info("Throughput Difference are (Mpps) %f" % delta)
        self.verify(
            (result_throughput > expected_throughput + gap),
            "result_throughput: %s is less than the expected_throughput: %s"
            % (result_throughput, result_throughput),
        )
        # wait ixia thread exit
        self.logger.info("wait the thread of ixia to exit")
        while 1:
            if self.flag is not None:
                break
            time.sleep(5)
        return True

    def start_vms(self):
        """
        start two VM, each VM has one virtio device
        """
        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, "vm%d" % i, "vhost_sample")
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i + ",server"
            vm_params["opt_queue"] = self.queues
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            if i == 0:
                vm_params[
                    "opt_settings"
                ] = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
            else:
                vm_params[
                    "opt_settings"
                ] = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
            vm_info.set_vm_device(**vm_params)
            try:
                vm_dut = vm_info.start(bind_dev=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print(utils.RED("Failure for %s" % str(e)))
            self.verify(vm_dut is not None, "start vm failed")
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def bind_dpdk_driver_in_2_vms(self):
        for i in range(self.vm_num):
            self.vm_dut[i].send_expect("modprobe vfio", "#")
            self.vm_dut[i].send_expect("modprobe vfio-pci", "#")
            self.vm_dut[i].send_expect(
                "./usertools/dpdk-devbind.py --force --bind=vfio-pci %s"
                % self.vm_dut[i].ports_info[0]["pci"],
                "#",
            )

    def quit_testpmd_in_2_vms(self):
        for i in range(self.vm_num):
            self.vm_dut[i].send_expect("quit", "#")

    def bind_kernel_driver_in_2_vms(self):
        for i in range(self.vm_num):
            self.vm_dut[i].send_expect(
                "./usertools/dpdk-devbind.py --force --bind=virtio-pci %s"
                % self.vm_dut[i].ports_info[0]["pci"],
                "#",
            )

    def start_testpmd_in_vm(self, pmd):
        """
        launch the testpmd in vm
        """
        self.vm_cores = [1, 2]
        param = "--tx-offloads=0x00 --enable-hw-vlan-strip --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        pmd.start_testpmd(cores=self.vm_cores, param=param)

    def send_packets_from_vhost(self):
        self.vhost_user_pmd.execute_cmd("set txpkts 1024")
        self.vhost_user_pmd.execute_cmd("start tx_first 32")

    def test_perf_pvp_virtio_user_quit(self):
        """
        Test Case 1: PVP virtio-user quit test
        """
        cdbmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s;rxq0@%s" % (cdbmas[0], cdbmas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,queues=1,dmas=[%s]' --iova=va" % dmas
        )
        vhost_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        ports = cdbmas
        ports.append(self.dut.ports_info[0]["pci"])
        self.start_vhost_user_testpmd(
            cores=self.vhost_user_core,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )

        virtio0_eal_param = f"--vdev=net_virtio_user0,mac={self.virtio_mac},path=./vhost-net0,mrg_rxbuf=1,in_order=1,queues=1"
        virtio0_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio_user0_core,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        res = self.check_packets_after_relaunch_virtio_user_testpmd(
            duration=180,
            cores=self.virtio_user0_core,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )
        self.verify(res is True, "Should increase the wait times of ixia")
        self.quit_all_testpmd()

    def test_perf_pvp_vhost_user_quit(self):
        """
        Test Case 2: PVP vhost-user quit test
        """
        cdbmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s;rxq0@%s" % (cdbmas[0], cdbmas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,queues=1,client=1,dmas=[%s]' --iova=va"
            % dmas
        )
        vhost_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        ports = cdbmas
        ports.append(self.dut.ports_info[0]["pci"])
        self.start_vhost_user_testpmd(
            cores=self.vhost_user_core,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )

        virtio0_eal_param = f"--vdev=net_virtio_user0,mac={self.virtio_mac},path=./vhost-net0,mrg_rxbuf=1,in_order=1,queues=1,server=1"
        virtio0_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio_user0_core,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        res = self.check_packets_after_relaunch_vhost_user_testpmd(
            duration=180,
            cores=self.vhost_user_core,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )
        self.verify(res is True, "Should increase the wait times of ixia")
        self.quit_all_testpmd()

    def test_perf_pvp_vhost_async_test_with_redundant_device_parameters(self):
        """
        Test Case 3: PVP vhost async test with redundant device parameters
        """
        cdbmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s;rxq0@%s" % (cdbmas[1], cdbmas[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,queues=1,client=1,dmas=[%s]' --iova=va"
            % dmas
        )
        vhost_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        ports = cdbmas
        ports.append(self.dut.ports_info[0]["pci"])
        self.start_vhost_user_testpmd(
            cores=self.vhost_user_core,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )

        virtio0_eal_param = f"--vdev=net_virtio_user0,mac={self.virtio_mac},path=./vhost-net0,mrg_rxbuf=1,in_order=1,queues=1,server=1"
        virtio0_param = "--nb-cores=1 --txq=1 --rxq=1 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio_user0_core,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.start_to_send_packets(duration=60)
        Mpps = self.flag / 1000000
        self.verify(Mpps > 0, "pktgen can't receive packets from vhost-user")
        self.quit_all_testpmd()

    def test_loopback_vhost_async_test_with_each_queue_using_2_dma_devices(self):
        """
        Test Case 4: Loopback vhost async test with each queue using 2 DMA devices
        """
        cdbmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=3, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s;txq0@%s;rxq0@%s;rxq0@%s" % (
            cdbmas[0],
            cdbmas[1],
            cdbmas[1],
            cdbmas[2],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,queues=2,client=1,dmas=[%s]' --iova=va"
            % dmas
        )
        vhost_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
        ports = cdbmas
        self.start_vhost_user_testpmd(
            cores=self.vhost_user_core,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            exec_start=False,
        )

        virtio0_eal_param = f"--vdev=net_virtio_user0,mac={self.virtio_mac},path=./vhost-net0,mrg_rxbuf=1,in_order=1,queues=2,server=1"
        virtio0_param = "--nb-cores=1 --txq=2 --rxq=2 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio_user0_core,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )
        self.send_packets_from_vhost()
        self.calculate_avg_throughput(pmd=self.vhost_user_pmd, reg="Tx-pps")
        self.quit_all_testpmd()

    def test_loopback_vhost_async_test_with_dmas_parameters_out_of_order(self):
        """
        Test Case 5: Loopback vhost async test with dmas parameters out of order
        """
        cdbmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "rxq3@%s;txq0@%s;rxq1@%s;txq2@%s" % (
            cdbmas[1],
            cdbmas[0],
            cdbmas[0],
            cdbmas[1],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,queues=4,client=1,dmas=[%s]' --iova=va"
            % dmas
        )
        vhost_param = "--nb-cores=1 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        ports = cdbmas
        self.start_vhost_user_testpmd(
            cores=self.vhost_user_core,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            exec_start=False,
        )

        virtio0_eal_param = f"--vdev=net_virtio_user0,mac={self.virtio_mac},path=./vhost-net0,mrg_rxbuf=1,in_order=1,queues=4,server=1"
        virtio0_param = "--nb-cores=1 --txq=4 --rxq=4 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio_user0_core,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )
        self.send_packets_from_vhost()
        self.calculate_avg_throughput(pmd=self.vhost_user_pmd, reg="Tx-pps")
        self.quit_all_testpmd()

    def test_vm2vm_split_and_packed_ring_mergeable_path_with_cbdma_enable_and_server_mode(
        self,
    ):
        """
        Test Case 6: VM2VM split and packed ring mergeable path with cbdma enable and server mode
        """
        cdbmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=16, driver_name="vfio-pci", socket=-1
        )
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cdbmas[0],
                cdbmas[1],
                cdbmas[2],
                cdbmas[3],
                cdbmas[4],
                cdbmas[1],
                cdbmas[2],
                cdbmas[3],
                cdbmas[4],
                cdbmas[5],
                cdbmas[6],
                cdbmas[7],
            )
        )
        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cdbmas[8],
                cdbmas[9],
                cdbmas[11],
                cdbmas[12],
                cdbmas[13],
                cdbmas[9],
                cdbmas[10],
                cdbmas[11],
                cdbmas[12],
                cdbmas[13],
                cdbmas[14],
                cdbmas[15],
            )
        )

        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=8,tso=1,dmas=[%s]' "
            % dmas1
            + "--vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % dmas2
        )
        vhost_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        ports = cdbmas
        self.start_vhost_user_testpmd(
            cores=self.vhost_user_core,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            set_fwd_mode=False,
            exec_start=True,
        )
        self.queues = 8
        self.start_vms()
        self.BC.config_2_vms_combined(combined=self.queues)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.bind_dpdk_driver_in_2_vms()
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.start_testpmd_in_vm(self.vm0_pmd)
        self.vm0_pmd.execute_cmd("set fwd mac")
        self.vm0_pmd.execute_cmd("start")

        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_testpmd_in_vm(self.vm1_pmd)
        self.vm1_pmd.execute_cmd("set fwd mac")
        self.vm1_pmd.execute_cmd("set txpkts 64,256,512")
        self.vm1_pmd.execute_cmd("start tx_first 32")
        self.calculate_avg_throughput(pmd=self.vm1_pmd, reg="Rx-pps")

        self.quit_testpmd_in_2_vms()
        self.bind_kernel_driver_in_2_vms()

        self.BC.config_2_vms_combined(combined=self.queues)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.bind_dpdk_driver_in_2_vms()
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.start_testpmd_in_vm(self.vm0_pmd)
        self.vm0_pmd.execute_cmd("set fwd mac")
        self.vm0_pmd.execute_cmd("start")
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_testpmd_in_vm(self.vm1_pmd)
        self.vm1_pmd.execute_cmd("set fwd mac")
        self.vm1_pmd.execute_cmd("set txpkts 64,256,512")
        self.vm1_pmd.execute_cmd("start tx_first 32")
        self.calculate_avg_throughput(pmd=self.vm1_pmd, reg="Rx-pps")

        self.quit_testpmd_in_2_vms()
        self.stop_all_vms()
        self.vhost_user_pmd.quit()

    def stop_all_vms(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()

    def quit_all_testpmd(self):
        self.virtio_user0_pmd.quit()
        self.vhost_user_pmd.quit()

    def close_all_session(self):
        """
        close all session of vhost an virtio
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user0)

    def tear_down(self):
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.CC.bind_cbdma_to_kernel_driver()

    def tear_down_all(self):
        self.close_all_session()

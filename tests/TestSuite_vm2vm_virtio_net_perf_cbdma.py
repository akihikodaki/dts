# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import random
import re
import string
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM
from tests.virtio_common import basic_common as BC
from tests.virtio_common import cbdma_common as CC


class TestVM2VMVirtioNetPerfCbdma(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.vm_num = 2
        self.virtio_ip1 = "1.1.1.1"
        self.virtio_ip2 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.virtio_mac2 = "52:54:00:00:00:02"
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.random_string = string.ascii_letters + string.digits
        socket_num = len(set([int(core["socket"]) for core in self.dut.cores]))
        self.socket_mem = ",".join(["2048"] * socket_num)
        self.vhost = self.dut.new_session(suite="vhost")
        self.pmdout_vhost_user = PmdOutput(self.dut, self.vhost)
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.BC = BC(self)
        self.CC = CC(self)

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_dut = []
        self.vm = []

    def start_vhost_testpmd(
        self, cores, param="", eal_param="", ports="", iova_mode=""
    ):
        if iova_mode:
            eal_param += " --iova=" + iova_mode
        self.pmdout_vhost_user.start_testpmd(
            cores=cores, param=param, eal_param=eal_param, ports=ports, prefix="vhost"
        )
        self.pmdout_vhost_user.execute_cmd("start")

    def start_vms(self, server_mode=False, vm_queue=1, vm_config="vhost_sample"):
        """
        start two VM, each VM has one virtio device
        """
        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, "vm%d" % i, vm_config)
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            if not server_mode:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            else:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i + ",server"
            vm_params["opt_queue"] = vm_queue
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            vm_params["opt_settings"] = self.vm_args
            vm_info.set_vm_device(**vm_params)
            try:
                vm_dut = vm_info.start(set_target=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print(utils.RED("Failure for %s" % str(e)))
            self.verify(vm_dut is not None, "start vm failed")
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def verify_xstats_info_on_vhost(self):
        """
        check both 2VMs can receive and send big packets to each other
        """
        self.vhost.send_expect("show port stats all", "testpmd> ", 20)
        out_tx = self.vhost.send_expect("show port xstats 0", "testpmd> ", 20)
        out_rx = self.vhost.send_expect("show port xstats 1", "testpmd> ", 20)

        tx_info = re.search("tx_q0_size_1519_max_packets:\s*(\d*)", out_tx)
        rx_info = re.search("rx_q0_size_1519_max_packets:\s*(\d*)", out_rx)

        self.verify(
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1518"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1518"
        )

    def test_vm2vm_virtio_net_split_ring_cbdma_enable_test_with_tcp_traffic(self):
        """
        Test Case 1: VM2VM virtio-net split ring CBDMA enable test with tcp traffic
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;rxq0@%s" % (cbdmas[0], cbdmas[0])
        dmas2 = "txq0@%s;rxq0@%s" % (cbdmas[1], cbdmas[1])
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1"

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_vm2vm_virtio_net_split_ring_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 2: VM2VM virtio-net split ring mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
                cbdmas[6],
                cbdmas[6],
                cbdmas[7],
                cbdmas[7],
            )
        )
        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
                cbdmas[6],
                cbdmas[6],
                cbdmas[7],
                cbdmas[7],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas[0:8],
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.BC.config_2_vms_ip()
        self.BC.config_2_vms_combined(combined=8)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
            )
        )
        dmas2 = (
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s"
            % (
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,client=1,legacy-ol-flags=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,client=1,legacy-ol-flags=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas[0:2],
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        if not self.BC.check_2M_hugepage_size():
            dmas1 = (
                "txq0@%s;"
                "txq1@%s;"
                "txq2@%s;"
                "txq3@%s;"
                "txq4@%s;"
                "txq5@%s;"
                "txq6@%s"
                % (
                    cbdmas[0],
                    cbdmas[1],
                    cbdmas[0],
                    cbdmas[1],
                    cbdmas[0],
                    cbdmas[1],
                    cbdmas[2],
                )
            )
            dmas2 = (
                "rxq0@%s;"
                "rxq1@%s;"
                "rxq2@%s;"
                "rxq3@%s;"
                "rxq4@%s;"
                "rxq5@%s;"
                "rxq6@%s"
                % (
                    cbdmas[2],
                    cbdmas[3],
                    cbdmas[2],
                    cbdmas[3],
                    cbdmas[2],
                    cbdmas[3],
                    cbdmas[4],
                )
            )
            eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,client=1,dmas=[%s]' "
                "--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,client=1,dmas=[%s]'"
                % (dmas1, dmas2)
            )
            param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
            self.pmdout_vhost_user.execute_cmd("quit", "#")
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                ports=cbdmas[0:8],
                eal_param=eal_param,
                param=param,
                iova_mode="pa",
            )
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=4 --rxq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
        )
        self.BC.config_2_vms_combined(combined=4)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.pmdout_vhost_user.execute_cmd("quit", "#")

        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
        )
        self.BC.config_2_vms_combined(combined=1)
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_vm2vm_virtio_net_split_ring_with_non_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 3: VM2VM virtio-net split ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
            )
        )
        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[%s],dma-ring-size=1024' "
            "--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8,dmas=[%s],dma-ring-size=1024'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.BC.config_2_vms_ip()
        self.BC.config_2_vms_combined(combined=8)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s"
            % (
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
            )
        )

        dmas2 = (
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[%s],dma-ring-size=128' "
            "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[%s],dma-ring-size=128'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms(file_size=10)
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.BC.config_2_vms_combined(combined=8)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
        )
        self.BC.config_2_vms_combined(combined=1)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_vm2vm_virtio_net_split_ring_mergeable_16_queues_cbdma_enable_test_with_Rx_Tx_csum_in_SW(
        self,
    ):
        """
        Test Case 4: VM2VM virtio-net split ring mergeable 16 queues CBDMA enable test with Rx/Tx csum in SW
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "txq8@%s;"
            "txq9@%s;"
            "txq10@%s;"
            "txq11@%s;"
            "txq12@%s;"
            "txq13@%s;"
            "txq14@%s;"
            "txq15@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s;"
            "rxq8@%s;"
            "rxq9@%s;"
            "rxq10@%s;"
            "rxq11@%s;"
            "rxq12@%s;"
            "rxq13@%s;"
            "rxq14@%s;"
            "rxq15@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
                cbdmas[6],
                cbdmas[6],
                cbdmas[7],
                cbdmas[7],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
                cbdmas[6],
                cbdmas[6],
                cbdmas[7],
                cbdmas[7],
            )
        )

        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "txq8@%s;"
            "txq9@%s;"
            "txq10@%s;"
            "txq11@%s;"
            "txq12@%s;"
            "txq13@%s;"
            "txq14@%s;"
            "txq15@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s;"
            "rxq8@%s;"
            "rxq9@%s;"
            "rxq10@%s;"
            "rxq11@%s;"
            "rxq12@%s;"
            "rxq13@%s;"
            "rxq14@%s;"
            "rxq15@%s"
            % (
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,tso=1,dmas=[%s]'"
        ) % (dmas1, dmas2)

        param = " --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.pmdout_vhost_user.execute_cmd("set fwd csum")
        self.pmdout_vhost_user.execute_cmd("csum mac-swap off 0")
        self.pmdout_vhost_user.execute_cmd("csum mac-swap off 1")
        self.pmdout_vhost_user.execute_cmd("stop")
        self.pmdout_vhost_user.execute_cmd("port stop all")
        self.pmdout_vhost_user.execute_cmd("port config 0 tx_offload tcp_cksum on")
        self.pmdout_vhost_user.execute_cmd("port config 1 tx_offload tcp_cksum on")
        self.pmdout_vhost_user.execute_cmd("port start all")
        self.pmdout_vhost_user.execute_cmd("start")

        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=16)
        self.BC.config_2_vms_ip()
        self.BC.config_2_vms_combined(combined=16)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_vm2vm_virtio_net_packed_ring_cbdma_enable_test_with_tcp_traffic(self):
        """
        Test Case 5: VM2VM virtio-net packed ring CBDMA enable test with tcp traffic
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;rxq0@%s" % (cbdmas[0], cbdmas[0])
        dmas2 = "txq0@%s;rxq0@%s" % (cbdmas[1], cbdmas[1])
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
        ) % (dmas1, dmas2)
        param = " --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_vm2vm_virtio_net_packed_ring_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 6: VM2VM virtio-net packed ring mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
                cbdmas[6],
                cbdmas[6],
                cbdmas[7],
                cbdmas[7],
            )
        )
        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
                cbdmas[6],
                cbdmas[6],
                cbdmas[7],
                cbdmas[7],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_ip()
        self.BC.config_2_vms_combined(combined=8)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms(file_size=10)
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_vm2vm_virtio_net_packed_ring_non_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 7: VM2VM virtio-net packed ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
            )
        )
        dmas2 = (
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s"
            % (
                cbdmas[8],
                cbdmas[8],
                cbdmas[9],
                cbdmas[9],
                cbdmas[10],
                cbdmas[10],
                cbdmas[11],
                cbdmas[11],
                cbdmas[12],
                cbdmas[12],
                cbdmas[13],
                cbdmas[13],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[%s],dma-ring-size=1024' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[%s],dma-ring-size=1024'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_ip()
        self.BC.config_2_vms_combined(combined=8)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms(file_size=10)
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_vm2vm_virtio_net_packed_ring_mergeable_16_queues_cbdma_enable_test_with_Rx_Tx_csum_in_SW(
        self,
    ):
        """
        Test Case 8: VM2VM virtio-net packed ring mergeable 16 queues CBDMA enabled test with Rx/Tx csum in SW
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "txq8@%s;"
            "txq9@%s;"
            "txq10@%s;"
            "txq11@%s;"
            "txq12@%s;"
            "txq13@%s;"
            "txq14@%s;"
            "txq15@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s;"
            "rxq8@%s;"
            "rxq9@%s;"
            "rxq10@%s;"
            "rxq11@%s;"
            "rxq12@%s;"
            "rxq13@%s;"
            "rxq14@%s;"
            "rxq15@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
                cbdmas[6],
                cbdmas[6],
                cbdmas[7],
                cbdmas[7],
                cbdmas[8],
                cbdmas[8],
                cbdmas[9],
                cbdmas[9],
                cbdmas[10],
                cbdmas[10],
                cbdmas[11],
                cbdmas[11],
                cbdmas[12],
                cbdmas[12],
                cbdmas[13],
                cbdmas[13],
                cbdmas[14],
                cbdmas[14],
                cbdmas[15],
                cbdmas[15],
            )
        )

        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "txq8@%s;"
            "txq9@%s;"
            "txq10@%s;"
            "txq11@%s;"
            "txq12@%s;"
            "txq13@%s;"
            "txq14@%s;"
            "txq15@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s;"
            "rxq8@%s;"
            "rxq9@%s;"
            "rxq10@%s;"
            "rxq11@%s;"
            "rxq12@%s;"
            "rxq13@%s;"
            "rxq14@%s;"
            "rxq15@%s"
            % (
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=16,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=16,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )

        self.pmdout_vhost_user.execute_cmd("set fwd csum")
        self.pmdout_vhost_user.execute_cmd("csum mac-swap off 0")
        self.pmdout_vhost_user.execute_cmd("csum mac-swap off 1")
        self.pmdout_vhost_user.execute_cmd("stop")
        self.pmdout_vhost_user.execute_cmd("port stop all")
        self.pmdout_vhost_user.execute_cmd("port config 0 tx_offload tcp_cksum on")
        self.pmdout_vhost_user.execute_cmd("port config 1 tx_offload tcp_cksum on")
        self.pmdout_vhost_user.execute_cmd("port start all")
        self.pmdout_vhost_user.execute_cmd("start")

        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=16)
        self.BC.config_2_vms_ip()
        self.BC.config_2_vms_combined(combined=16)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms(file_size=10)
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_vm2vm_virtio_net_packed_ring_cbdma_enable_test_dma_ring_size_with_tcp_traffic(
        self,
    ):
        """
        Test Case 9: VM2VM virtio-net packed ring CBDMA enable test dma-ring-size with tcp traffic
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;rxq0@%s" % (cbdmas[0], cbdmas[0])
        dmas2 = "txq0@%s;rxq0@%s" % (cbdmas[1], cbdmas[1])
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s],dma-ring-size=256' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s],dma-ring-size=256'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms(file_size=10)
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_vm2vm_virtio_net_packed_ring_8_queues_cbdma_enable_test_with_legacy_mode(
        self,
    ):
        """
        Test Case 10: VM2VM virtio-net packed ring 8 queues CBDMA enable test with legacy mode
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[4],
                cbdmas[4],
                cbdmas[5],
                cbdmas[5],
            )
        )
        dmas2 = (
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s"
            % (
                cbdmas[8],
                cbdmas[8],
                cbdmas[9],
                cbdmas[9],
                cbdmas[10],
                cbdmas[10],
                cbdmas[11],
                cbdmas[11],
                cbdmas[12],
                cbdmas[12],
                cbdmas[13],
                cbdmas[13],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=cbdmas,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms(file_size=10)
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms(file_size=10)
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.pmdout_vhost_user.quit()

    def tear_down(self):
        """
        run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
        self.dut.close_session(self.vhost)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM

from .virtio_common import basic_common as BC
from .virtio_common import dsa_common as DC


class TestVM2VMVirtioNetPerfDsa(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.vm_num = 2
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        socket_num = len(set([int(core["socket"]) for core in self.dut.cores]))
        self.socket_mem = ",".join(["2048"] * socket_num)
        self.vhost_user = self.dut.new_session(suite="vhost")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.BC = BC(self)
        self.DC = DC(self)

    def set_up(self):
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.vm_dut = []
        self.vm = []

    def start_vhost_testpmd(
        self,
        cores,
        eal_param="",
        param="",
        no_pci=False,
        ports="",
        port_options="",
        iova_mode="va",
    ):
        if iova_mode:
            eal_param += " --iova=" + iova_mode
        if not no_pci and port_options != "":
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=eal_param,
                param=param,
                port_options=port_options,
                ports=ports,
                prefix="vhost",
                fixed_prefix=True,
            )
        elif not no_pci and port_options == "":
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=eal_param,
                param=param,
                ports=ports,
                prefix="vhost",
                fixed_prefix=True,
            )
        else:
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=eal_param,
                param=param,
                no_pci=no_pci,
                prefix="vhost",
                fixed_prefix=True,
            )
        self.vhost_user_pmd.execute_cmd("start")

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
            if vm_queue > 1:
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
        self.vhost_user.send_expect("show port stats all", "testpmd> ", 20)
        out_tx = self.vhost_user.send_expect("show port xstats 0", "testpmd> ", 20)
        out_rx = self.vhost_user.send_expect("show port xstats 1", "testpmd> ", 20)

        tx_info = re.search("tx_q0_size_1519_max_packets:\s*(\d*)", out_tx)
        rx_info = re.search("rx_q0_size_1519_max_packets:\s*(\d*)", out_rx)

        self.verify(
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1519"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1519"
        )

    def test_split_tso_with_dpdk_driver(self):
        """
        Test Case 1: VM2VM vhost-user/virtio-net split ring test TSO with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q0" % (dsas[0], dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_split_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 2: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q1;"
            "txq3@%s-q1;"
            "txq4@%s-q2;"
            "txq5@%s-q2;"
            "txq6@%s-q3;"
            "txq7@%s-q3;"
            "rxq0@%s-q0;"
            "rxq1@%s-q0;"
            "rxq2@%s-q1;"
            "rxq3@%s-q1;"
            "rxq4@%s-q2;"
            "rxq5@%s-q2;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        port_options = {dsas[0]: "max_queues=4"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q2;"
            "rxq2@%s-q3;"
            "rxq3@%s-q4;"
            "rxq4@%s-q5;"
            "rxq5@%s-q5;"
            "rxq6@%s-q5;"
            "rxq7@%s-q5"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        dmas2 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q2;"
            "rxq2@%s-q3;"
            "rxq3@%s-q4;"
            "rxq4@%s-q5;"
            "rxq5@%s-q5;"
            "rxq6@%s-q5;"
            "rxq7@%s-q5"
            % (
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=8",
            dsas[1]: "max_queues=8",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        if not self.BC.check_2M_hugepage_size:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=dsas,
                port_options=port_options,
                iova_mode="pa",
            )
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=4)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=1)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_split_non_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 3: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q1;"
            "txq3@%s-q1;"
            "txq4@%s-q2;"
            "txq5@%s-q2;"
            "txq6@%s-q3;"
            "txq7@%s-q3;"
            "rxq0@%s-q0;"
            "rxq1@%s-q0;"
            "rxq2@%s-q1;"
            "rxq3@%s-q1;"
            "rxq4@%s-q2;"
            "rxq5@%s-q2;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        port_options = {dsas[0]: "max_queues=8"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=4)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_packed_tso_with_dpdk_driver(self):
        """
        Test Case 4: VM2VM vhost-user/virtio-net packed ring test TSO with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_packed_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 5: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q1;"
            "txq3@%s-q1;"
            "txq4@%s-q2;"
            "txq5@%s-q2;"
            "txq6@%s-q3;"
            "txq7@%s-q3;"
            "rxq0@%s-q0;"
            "rxq1@%s-q0;"
            "rxq2@%s-q1;"
            "rxq3@%s-q1;"
            "rxq4@%s-q2;"
            "rxq5@%s-q2;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        port_options = {dsas[0]: "max_queues=4"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_packed_non_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 6: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q3;"
            "txq4@%s-q4;"
            "txq5@%s-q5;"
            "rxq2@%s-q6;"
            "rxq3@%s-q6;"
            "rxq4@%s-q7;"
            "rxq5@%s-q7;"
            "rxq6@%s-q7;"
            "rxq7@%s-q7"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        dmas2 = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q3;"
            "txq4@%s-q4;"
            "txq5@%s-q5;"
            "rxq2@%s-q6;"
            "rxq3@%s-q6;"
            "rxq4@%s-q7;"
            "rxq5@%s-q7;"
            "rxq6@%s-q7;"
            "rxq7@%s-q7"
            % (
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
            )
        )
        port_options = {
            dsas[0]: "max_queues=8",
            dsas[1]: "max_queues=8",
        }
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=off,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_packed_dma_ring_size_with_tcp_and_dpdk_driver(self):
        """
        Test Case 7: VM2VM vhost-user/virtio-net packed ring test dma-ring-size with tcp traffic and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s-q0;rxq0@%s-q0" % (dsas[0], dsas[0])
        dmas2 = "txq0@%s-q1;rxq0@%s-q1" % (dsas[0], dsas[0])
        port_options = {dsas[0]: "max_queues=2"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s],dma-ring-size=64' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s],dma-ring-size=64'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_packed_mergeable_8_queues_with_legacy_mode_and_dpdk_driver(self):
        """
        Test Case 8: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with legacy mode with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "txq6@%s-q1;"
            "txq7@%s-q1;"
            "rxq0@%s-q0;"
            "rxq1@%s-q0;"
            "rxq2@%s-q0;"
            "rxq3@%s-q0;"
            "rxq4@%s-q1;"
            "rxq5@%s-q1;"
            "rxq6@%s-q1;"
            "rxq7@%s-q1"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        port_options = {dsas[0]: "max_queues=4"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_split_tso_with_kernel_driver(self):
        """
        Test Case 9: VM2VM vhost-user/virtio-net split ring test TSO with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=1, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[0])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_split_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(self):
        """
        Test Case 10: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
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
        ) % (
            wqs[0],
            wqs[1],
            wqs[2],
            wqs[3],
            wqs[4],
            wqs[5],
            wqs[6],
            wqs[7],
            wqs[0],
            wqs[1],
            wqs[2],
            wqs[3],
            wqs[4],
            wqs[5],
            wqs[6],
            wqs[7],
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
        ) % (
            wqs[8],
            wqs[9],
            wqs[10],
            wqs[11],
            wqs[12],
            wqs[13],
            wqs[14],
            wqs[15],
            wqs[8],
            wqs[9],
            wqs[10],
            wqs[11],
            wqs[12],
            wqs[13],
            wqs[14],
            wqs[15],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
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
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[1],
                wqs[1],
                wqs[2],
                wqs[2],
                wqs[2],
                wqs[2],
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
                wqs[3],
                wqs[3],
                wqs[3],
                wqs[3],
                wqs[4],
                wqs[4],
                wqs[4],
                wqs[4],
                wqs[5],
                wqs[5],
                wqs[5],
                wqs[5],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=4)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_split_non_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(
        self,
    ):
        """
        Test Case 11: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
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
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[1],
                wqs[1],
                wqs[2],
                wqs[2],
                wqs[2],
                wqs[2],
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
                wqs[3],
                wqs[3],
                wqs[3],
                wqs[3],
                wqs[4],
                wqs[4],
                wqs[4],
                wqs[4],
                wqs[5],
                wqs[5],
                wqs[5],
                wqs[5],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=off,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,legacy-ol-flags=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,legacy-ol-flags=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_packed_tso_with_kernel_driver(self):
        """
        Test Case 12: VM2VM vhost-user/virtio-net packed ring test TSO with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=1, dsa_idxs=[0])
        dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[0])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_packed_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(self):
        """
        Test Case 13: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
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
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[6],
                wqs[7],
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
                wqs[8],
                wqs[9],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vm_args = "mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_packed_non_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(
        self,
    ):
        """
        Test Case 14: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=4, dsa_idxs=[0, 1])
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
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[2],
                wqs[2],
                wqs[3],
                wqs[3],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[2],
                wqs[2],
                wqs[3],
                wqs[3],
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
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[2],
                wqs[2],
                wqs[3],
                wqs[3],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[2],
                wqs[2],
                wqs[3],
                wqs[3],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=8,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.BC.config_2_vms_combined(combined=8)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def test_split_non_mergeable_16_queues_with_rx_tx_csum_in_sw(self):
        """
        Test Case 15: VM2VM vhost-user/virtio-net split ring non-mergeable 16 queues test with Rx/Tx csum in SW
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2,
            driver_name="vfio-pci",
            dsa_idxs=[2, 3],
            socket=self.ports_socket,
        )
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q0;"
            "txq5@%s-q0;"
            "txq6@%s-q0;"
            "txq7@%s-q0;"
            "txq8@%s-q0;"
            "txq9@%s-q0;"
            "txq10@%s-q0;"
            "txq11@%s-q0;"
            "txq12@%s-q0;"
            "txq13@%s-q0;"
            "txq14@%s-q0;"
            "txq15@%s-q0;"
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
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
            )
        )
        dmas2 = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q3;"
            "txq4@%s-q4;"
            "txq5@%s-q5;"
            "txq6@%s-q6;"
            "txq7@%s-q7;"
            "txq8@%s-q0;"
            "txq9@%s-q1;"
            "txq10@%s-q2;"
            "txq11@%s-q3;"
            "txq12@%s-q4;"
            "txq13@%s-q5;"
            "txq14@%s-q6;"
            "txq15@%s-q7;"
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
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[6],
                wqs[7],
                wqs[8],
                wqs[9],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=16,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=16,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
        )
        self.vhost_user_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("set fwd csum")
        self.vhost_user_pmd.execute_cmd("csum mac-swap off 0")
        self.vhost_user_pmd.execute_cmd("csum mac-swap off 1")
        self.vhost_user_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("port stop all")
        self.vhost_user_pmd.execute_cmd("port config 0 tx_offload tcp_cksum on")
        self.vhost_user_pmd.execute_cmd("port config 1 tx_offload tcp_cksum on")
        self.vhost_user_pmd.execute_cmd("port start all")
        self.vhost_user_pmd.execute_cmd("start")
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=16)
        self.BC.config_2_vms_combined(combined=16)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q2;"
            "txq5@%s-q3;"
            "rxq2@%s-q4;"
            "rxq3@%s-q5;"
            "rxq4@%s-q6;"
            "rxq5@%s-q6;"
            "rxq6@%s-q6;"
            "rxq7@%s-q6"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        dmas2 = (
            "txq12@%s;"
            "txq13@%s;"
            "txq14@%s;"
            "txq15@%s;"
            "rxq12@%s;"
            "rxq13@%s;"
            "rxq14@%s;"
            "rxq15@%s"
            % (
                wqs[8],
                wqs[8],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=16,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=16,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
        )
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=16,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=16,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.BC.config_2_vms_combined(combined=1)
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

    def test_packed_mergeable_16_queues_with_rx_tx_csum_in_sw(self):
        """
        Test Case 16: VM2VM vhost-user/virtio-net packed ring mergeable 16 queues test with Rx/Tx csum in SW
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2,
            driver_name="vfio-pci",
            dsa_idxs=[2, 3],
            socket=self.ports_socket,
        )
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q0;"
            "txq5@%s-q0;"
            "txq6@%s-q0;"
            "txq7@%s-q0;"
            "txq8@%s-q0;"
            "txq9@%s-q0;"
            "txq10@%s-q0;"
            "txq11@%s-q0;"
            "txq12@%s-q0;"
            "txq13@%s-q0;"
            "txq14@%s-q0;"
            "txq15@%s-q0;"
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
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
            )
        )
        dmas2 = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q3;"
            "txq4@%s-q4;"
            "txq5@%s-q5;"
            "txq6@%s-q6;"
            "txq7@%s-q7;"
            "txq8@%s-q0;"
            "txq9@%s-q1;"
            "txq10@%s-q2;"
            "txq11@%s-q3;"
            "txq12@%s-q4;"
            "txq13@%s-q5;"
            "txq14@%s-q6;"
            "txq15@%s-q7;"
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
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[6],
                wqs[7],
                wqs[8],
                wqs[9],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=16,tso=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=16,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=16 --txq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
        )
        self.vhost_user_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("set fwd csum")
        self.vhost_user_pmd.execute_cmd("csum mac-swap off 0")
        self.vhost_user_pmd.execute_cmd("csum mac-swap off 1")
        self.vhost_user_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("port stop all")
        self.vhost_user_pmd.execute_cmd("port config 0 tx_offload tcp_cksum on")
        self.vhost_user_pmd.execute_cmd("port config 1 tx_offload tcp_cksum on")
        self.vhost_user_pmd.execute_cmd("port start all")
        self.vhost_user_pmd.execute_cmd("start")
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=off,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=16)
        self.BC.config_2_vms_combined(combined=16)
        self.BC.config_2_vms_ip()
        self.BC.check_ping_between_2_vms()
        self.BC.check_scp_file_between_2_vms()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()

        for _ in range(5):
            self.BC.check_ping_between_2_vms()
            self.BC.check_scp_file_between_2_vms()
            self.BC.run_iperf_test_between_2_vms()
            self.BC.check_iperf_result_between_2_vms()

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vhost_user_pmd.quit()

    def tear_down(self):
        self.stop_all_apps()
        self.dut.kill_all()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def tear_down_all(self):
        self.dut.close_session(self.vhost_user)

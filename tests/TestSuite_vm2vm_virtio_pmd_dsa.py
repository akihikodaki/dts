# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM

from .virtio_common import dsa_common as DC


class TestVM2VMVirtioPmdDsa(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:5]
        self.memory_channel = self.dut.get_memory_channels()
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.DC = DC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("killall -s INT perf", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.vm_num = 2
        self.vm_dut = []
        self.vm = []

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_vhost_testpmd(
        self,
        cores,
        eal_param="",
        param="",
        no_pci=False,
        ports="",
        port_options="",
    ):
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

    def start_vms(
        self,
        vm_queue,
        mergeable=True,
        packed=False,
        server_mode=True,
        restart_vm1=False,
    ):
        """
        start two VM, each VM has one virtio device
        """
        vm_params = {}
        vm_params["opt_queue"] = vm_queue
        if restart_vm1:
            self.vm_num = 1
        for i in range(self.vm_num):
            if restart_vm1:
                i = i + 1
            vm_info = VM(self.dut, "vm%d" % i, "vhost_sample")
            vm_params["driver"] = "vhost-user"
            if not server_mode:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            else:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i + ",server"
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            if mergeable:
                mrg_rxbuf = "on"
            else:
                mrg_rxbuf = "off"
            if packed:
                vm_params[
                    "opt_settings"
                ] = "disable-modern=false,mrg_rxbuf={},mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on".format(
                    mrg_rxbuf
                )
            else:
                vm_params[
                    "opt_settings"
                ] = "disable-modern=false,mrg_rxbuf={},mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on".format(
                    mrg_rxbuf
                )
            vm_info.set_vm_device(**vm_params)
            time.sleep(3)
            try:
                vm_dut = vm_info.start()
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print((utils.RED("Failure for %s" % str(e))))
                raise e
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def start_vm_testpmd(self, vm_pmd, queues, mergeable=True):
        if mergeable:
            param = "--enable-hw-vlan-strip --txq={} --rxq={} --txd=1024 --rxd=1024 --max-pkt-len=9600 --tx-offloads=0x00 --rx-offloads=0x00002000".format(
                queues, queues
            )
        else:
            param = "--enable-hw-vlan-strip --txq={} --rxq={} --txd=1024 --rxd=1024 --tx-offloads=0x00".format(
                queues, queues
            )
        vm_pmd.start_testpmd(cores="default", param=param)
        vm_pmd.execute_cmd("set fwd mac")

    def send_big_imix_packets_from_vm1(self):
        self.vm1_pmd.execute_cmd("set txpkts 64,256,512,1024,2000,64,256,512,1024,2000")
        self.vm1_pmd.execute_cmd("start tx_first 32")
        self.vm1_pmd.execute_cmd("show port stats all")

    def send_small_imix_packets_from_vm1(self):
        self.vm1_pmd.execute_cmd("set txpkts 64,256,512")
        self.vm1_pmd.execute_cmd("start tx_first 32")
        self.vm1_pmd.execute_cmd("show port stats all")

    def send_64b_packets_from_vm1(self):
        self.vm1_pmd.execute_cmd("stop")
        self.vm1_pmd.execute_cmd("start tx_first 32")
        self.vm1_pmd.execute_cmd("show port stats all")

    def check_packets_looped_in_2vms(self, vm_pmd):
        results = 0.0
        for _ in range(10):
            out = vm_pmd.execute_cmd("show port stats 0")
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.logger.info(Mpps)
        self.verify(Mpps > 0, "virtio-pmd can not looped packets")

    def check_packets_of_each_queue(self, vm_pmd, queues):
        vm_pmd.execute_cmd("show port stats all")
        out = vm_pmd.execute_cmd("stop")
        self.logger.info(out)
        for queue in range(queues):
            reg = "Queue= %d" % queue
            index = out.find(reg)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(
                rx_packets > 0 and tx_packets > 0,
                "The queue {} rx-packets or tx-packets is 0 about ".format(queue)
                + "rx-packets: {}, tx-packets: {}".format(rx_packets, tx_packets),
            )

    def dynamic_change_queue_size(self, dut_pmd, queues):
        dut_pmd.execute_cmd("stop")
        dut_pmd.execute_cmd("port stop all")
        dut_pmd.execute_cmd("port config all rxq {}".format(queues))
        dut_pmd.execute_cmd("port config all txq {}".format(queues))
        dut_pmd.execute_cmd("port start all")
        dut_pmd.execute_cmd("start")

    def get_and_verify_func_name_of_perf_top(self, func_name_list):
        time.sleep(10)
        self.dut.send_expect("rm -fr perf_top.log", "# ", 120)
        self.dut.send_expect("perf top > perf_top.log", "", 120)
        time.sleep(30)
        self.dut.send_expect("^C", "#")
        out = self.dut.send_expect("cat perf_top.log", "# ", 120)
        self.logger.info(out)
        for func_name in func_name_list:
            self.verify(
                func_name in out,
                "the func_name {} is not in the perf top output".format(func_name),
            )

    def test_vm2vm_virtio_pmd_split_ring_mergeable_path_dynamic_queue_size_with_dsa_dpdk_driver_and_server_mode(
        self,
    ):
        """
        Test Case 1: VM2VM virtio-pmd split ring mergeable path dynamic queue size with dsa dpdk driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q3;"
            "rxq0@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q3"
            % (dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0])
        )
        port_options = {dsas[0]: "max_queues=4"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.start_vms(vm_queue=8, mergeable=True, packed=False, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=True)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_big_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=8)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

    def test_vm2vm_virtio_pmd_split_ring_non_mergeable_path_dynamic_queue_size_with_dsa_dpdk_driver_and_server_mode(
        self,
    ):
        """
        Test Case 2: VM2VM virtio-pmd split ring non-mergeable path dynamic queue size with dsa dpdk driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q1;"
            "txq3@%s-q1;"
            "rxq0@%s-q2;"
            "rxq1@%s-q2;"
            "rxq2@%s-q3;"
            "rxq3@%s-q3"
            % (dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0])
        )
        port_options = {dsas[0]: "max_queues=4"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.start_vms(vm_queue=8, mergeable=False, packed=False, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=False)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=False)
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=4)
        self.vm0_pmd.execute_cmd("start")
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

    def test_vm2vm_virtio_pmd_packed_ring_mergeable_path_dynamic_queue_size_with_dsa_dpdk_driver_and_server_mode(
        self,
    ):
        """
        Test Case 3: VM2VM virtio-pmd packed ring mergeable path dynamic queue size with dsa dpdk driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q3;"
            "rxq0@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q3"
            % (dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0])
        )
        port_options = {dsas[0]: "max_queues=4"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.start_vms(vm_queue=8, mergeable=True, packed=True, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=True)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_big_imix_packets_from_vm1()
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.logger.info("Quit and relaunch VM2 with split ring")
        self.vm1_pmd.execute_cmd("quit", "#")
        self.vm[1].stop()
        self.vm_dut.remove(self.vm_dut[1])
        self.vm.remove(self.vm[1])
        self.start_vms(
            vm_queue=8, mergeable=True, packed=False, restart_vm1=True, server_mode=True
        )
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_big_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=8)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

    def test_vm2vm_virtio_pmd_packed_ring_non_mergeable_path_dynamic_queue_size_with_dsa_dpdk_driver_and_server_mode(
        self,
    ):
        """
        Test Case 4: VM2VM virtio-pmd packed ring non-mergeable path dynamic queue size with dsa dpdk driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q2;"
            "txq3@%s-q3;"
            "rxq0@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q3"
            % (dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0], dsas[0])
        )
        port_options = {dsas[0]: "max_queues=4"}
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.start_vms(vm_queue=8, mergeable=False, packed=True, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=False)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=False)
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=4)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

    def test_vm2vm_virtio_pmd_split_ring_mergeable_path_dynamic_queue_size_with_dsa_kernel_driver_and_server_mode(
        self,
    ):
        """
        Test Case 5: VM2VM virtio-pmd split ring mergeable path dynamic queue size with dsa kernel driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s" % (wqs[0], wqs[0], wqs[0], wqs[0], wqs[1], wqs[1], wqs[1], wqs[1])
        )

        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s" % (wqs[1], wqs[1], wqs[1], wqs[1], wqs[0], wqs[0], wqs[0], wqs[0])
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.start_vms(vm_queue=8, mergeable=True, packed=False, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=True)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_big_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=8)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

    def test_vm2vm_virtio_pmd_split_ring_non_mergeable_path_dynamic_queue_size_with_dsa_kernel_driver_and_server_mode(
        self,
    ):
        """
        Test Case 6: VM2VM virtio-pmd split ring non-mergeable path dynamic queue size with dsa kernel driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
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
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.start_vms(vm_queue=8, mergeable=False, packed=False, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=False)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=False)
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=4)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

    def test_vm2vm_virtio_pmd_packed_ring_mergeable_path_dynamic_queue_size_with_dsa_kernel_driver_and_server_mode(
        self,
    ):
        """
        Test Case 7: VM2VM virtio-pmd packed ring mergeable path dynamic queue size with dsa kernel driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s" % (wqs[0], wqs[1], wqs[2], wqs[3], wqs[0], wqs[1], wqs[2], wqs[3])
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas, dmas)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.start_vms(vm_queue=8, mergeable=True, packed=True, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=True)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_big_imix_packets_from_vm1()
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.logger.info("Quit and relaunch VM2 with split ring")
        self.vm1_pmd.execute_cmd("quit", "#")
        self.vm[1].stop()
        self.vm_dut.remove(self.vm_dut[1])
        self.vm.remove(self.vm[1])
        self.start_vms(
            vm_queue=8, mergeable=True, packed=False, restart_vm1=True, server_mode=True
        )
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=8)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

    def test_vm2vm_virtio_pmd_packed_ring_non_mergeable_path_dynamic_queue_size_with_dsa_kernel_driver_and_server_mode(
        self,
    ):
        """
        Test Case 8: VM2VM virtio-pmd packed ring non-mergeable path dynamic queue size with dsa kernel driver and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
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
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
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
                wqs[2],
                wqs[2],
                wqs[2],
                wqs[2],
                wqs[3],
                wqs[3],
                wqs[10],
                wqs[10],
                wqs[11],
                wqs[11],
                wqs[11],
                wqs[11],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.start_vms(vm_queue=8, mergeable=False, packed=True, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=False)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=False)
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=4)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm0_pmd)
        self.check_packets_looped_in_2vms(vm_pmd=self.vm1_pmd)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vhost_user_pmd.quit()

    def tear_down(self):
        self.stop_all_apps()
        self.dut.kill_all()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    def tear_down_all(self):
        self.dut.close_session(self.vhost_user)

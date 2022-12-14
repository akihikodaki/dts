# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM


class TestVM2VMVirtioPmdCBDMA(TestCase):
    def set_up_all(self):
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

    def set_up(self):
        """
        run before each test case.
        """
        self.table_header = [
            "FrameSize(B)",
            "Mode",
            "Throughput(Mpps)",
            "Queue Number",
            "Path",
        ]
        self.result_table_create(self.table_header)
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("killall -s INT perf", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_num = 2
        self.vm_dut = []
        self.vm = []

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num, allow_diff_socket=False):
        """
        get all cbdma ports
        """
        self.all_cbdma_list = []
        self.cbdma_list = []
        self.cbdma_str = ""
        out = self.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "# ", 30
        )
        device_info = out.split("\n")
        for device in device_info:
            pci_info = re.search("\s*(0000:\S*:\d*.\d*)", device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if allow_diff_socket:
                    self.all_cbdma_list.append(pci_info.group(1))
                else:
                    if self.ports_socket == cur_socket:
                        self.all_cbdma_list.append(pci_info.group(1))
        self.verify(
            len(self.all_cbdma_list) >= cbdma_num, "There no enough cbdma device"
        )
        self.cbdma_list = self.all_cbdma_list[0:cbdma_num]
        self.cbdma_str = " ".join(self.cbdma_list)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (self.drivername, self.cbdma_str),
            "# ",
            60,
        )

    def start_vhost_testpmd(self, cores, ports, prefix, eal_param, param):
        """
        launch the testpmd with different parameters
        """
        self.vhost_user_pmd.start_testpmd(
            cores=cores, ports=ports, prefix=prefix, eal_param=eal_param, param=param
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    def start_vms(
        self,
        vm_queue,
        mergeable=True,
        packed=False,
        server_mode=True,
        restart_vm1=False,
        vm_config="vhost_sample",
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
            vm_info = VM(self.dut, "vm%d" % i, vm_config)
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
        self.dut.send_expect("rm -fr perf_top.log", "# ", 120)
        self.dut.send_expect("perf top > perf_top.log", "", 120)
        time.sleep(10)
        self.dut.send_expect("^C", "#")
        out = self.dut.send_expect("cat perf_top.log", "# ", 120)
        self.logger.info(out)
        for func_name in func_name_list:
            self.verify(
                func_name in out,
                "the func_name {} is not in the perf top output".format(func_name),
            )

    def test_vm2vm_virtio_pmd_split_ring_mergeable_path_dynamic_queue_size_with_cbdma_enable_and_server_mode(
        self,
    ):
        """
        Test Case 1: VM2VM virtio-pmd split ring mergeable path dynamic queue size with cbdma enable and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s"
            % (
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            prefix="vhost",
            eal_param=eal_param,
            param=param,
        )
        self.start_vms(vm_queue=8, mergeable=True, packed=False, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=True)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_big_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=8)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

        for _ in range(3):
            self.logger.info("Quit and relaunch vhost side testpmd")
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
                    self.cbdma_list[0],
                    self.cbdma_list[1],
                    self.cbdma_list[2],
                    self.cbdma_list[3],
                    self.cbdma_list[4],
                    self.cbdma_list[1],
                    self.cbdma_list[2],
                    self.cbdma_list[3],
                    self.cbdma_list[4],
                    self.cbdma_list[5],
                    self.cbdma_list[6],
                    self.cbdma_list[7],
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
                    self.cbdma_list[8],
                    self.cbdma_list[9],
                    self.cbdma_list[10],
                    self.cbdma_list[11],
                    self.cbdma_list[12],
                    self.cbdma_list[9],
                    self.cbdma_list[10],
                    self.cbdma_list[11],
                    self.cbdma_list[12],
                    self.cbdma_list[13],
                    self.cbdma_list[14],
                    self.cbdma_list[15],
                )
            )
            eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]' "
                "--vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,dmas=[%s]'"
                % (dmas1, dmas2)
            )
            param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                ports=self.cbdma_list,
                prefix="vhost",
                eal_param=eal_param,
                param=param,
            )
            self.vm0_pmd.execute_cmd("start")
            self.send_64b_packets_from_vm1()
            self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
            self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

    def test_vm2vm_virtio_pmd_split_ring_non_mergeable_path_dynamic_queue_size_with_cbdma_enable_and_server_mode(
        self,
    ):
        """
        Test Case 2: VM2VM virtio-pmd split ring non-mergeable path dynamic queue size with cbdma enable and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            prefix="vhost",
            eal_param=eal_param,
            param=param,
        )
        self.start_vms(vm_queue=8, mergeable=False, packed=False, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=False)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=False)
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(dut_pmd=self.vm0_pmd, queues=4)
        self.dynamic_change_queue_size(dut_pmd=self.vm1_pmd, queues=4)
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

    def test_vm2vm_virtio_pmd_packed_ring_mergeable_path_dynamic_queue_size_with_cbdma_enable_and_server_mode(
        self,
    ):
        """
        Test Case 3: VM2VM virtio-pmd packed ring mergeable path dynamic queue size with cbdma enable and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        dmas2 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            prefix="vhost",
            eal_param=eal_param,
            param=param,
        )
        self.start_vms(vm_queue=8, mergeable=True, packed=True, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=8, mergeable=True)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8, mergeable=True)
        self.send_big_imix_packets_from_vm1()
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
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=8)
        self.send_big_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(dut_pmd=self.vhost_user_pmd, queues=8)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

    def test_vm2vm_virtio_pmd_packed_ring_non_mergeable_path_dynamic_queue_size_with_cbdma_enable_and_server_mode(
        self,
    ):
        """
        Test Case 4: VM2VM virtio-pmd packed ring non-mergeable path dynamic queue size with cbdma enable and server mode
        """
        self.check_path = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
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
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[7],
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
                self.cbdma_list[8],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[13],
                self.cbdma_list[14],
                self.cbdma_list[15],
            )
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            prefix="vhost",
            eal_param=eal_param,
            param=param,
        )
        self.start_vms(vm_queue=8, mergeable=False, packed=True, server_mode=True)
        self.vm0_pmd = PmdOutput(self.vm_dut[0])
        self.vm1_pmd = PmdOutput(self.vm_dut[1])
        self.start_vm_testpmd(vm_pmd=self.vm0_pmd, queues=4, mergeable=False)
        self.vm0_pmd.execute_cmd("start")
        self.start_vm_testpmd(vm_pmd=self.vm1_pmd, queues=4, mergeable=False)
        self.send_small_imix_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=4)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=4)

        self.dynamic_change_queue_size(self.vm0_pmd, queues=8)
        self.dynamic_change_queue_size(self.vm1_pmd, queues=8)
        self.vm0_pmd.execute_cmd("start")
        self.send_64b_packets_from_vm1()
        self.get_and_verify_func_name_of_perf_top(self.check_path)
        self.check_packets_of_each_queue(vm_pmd=self.vm0_pmd, queues=8)
        self.check_packets_of_each_queue(vm_pmd=self.vm1_pmd, queues=8)

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm_dut[i].send_expect("quit", "#", 20)
            self.vm[i].stop()
        self.vhost_user.send_expect("quit", "#", 30)

    def bind_cbdma_device_to_kernel(self):
        self.dut.send_expect("modprobe ioatdma", "# ")
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % self.cbdma_str, "# ", 30
        )
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=ioatdma  %s" % self.cbdma_str,
            "# ",
            60,
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)

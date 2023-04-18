# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import _thread
import re
import time

from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM
from tests.virtio_common import basic_common as BC
from tests.virtio_common import cbdma_common as CC


class TestVirtioIdxInterruptCbdma(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.queues = 1
        self.nb_cores = 1
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list("all", socket=self.ports_socket)
        self.vhost_core_list = self.core_list[0:17]
        self.cores_num = len(
            [n for n in self.dut.cores if int(n["socket"]) == self.ports_socket]
        )
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.pf_pci = self.dut.ports_info[0]["pci"]
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_pmd = PmdOutput(self.dut, self.vhost_user)
        self.CC = CC(self)
        self.BC = BC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.flag = None
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    def get_core_mask(self):
        self.core_config = "1S/%dC/1T" % (self.nb_cores + 1)
        self.verify(
            self.cores_num >= (self.nb_cores + 1),
            "There has not enough cores to test this case %s" % self.running_case,
        )
        self.core_list = self.dut.get_core_list(self.core_config)

    def start_vms(self, packed=False, mode=False, set_target=False, bind_dev=False):
        """
        start qemus
        """
        self.vm = VM(self.dut, "vm0", "vhost_sample")
        vm_params = {}
        vm_params["driver"] = "vhost-user"
        if mode:
            vm_params["opt_path"] = "%s/vhost-net,%s" % (self.base_dir, mode)
        else:
            vm_params["opt_path"] = "%s/vhost-net" % self.base_dir
        vm_params["opt_mac"] = "00:11:22:33:44:55"
        opt_args = (
            "mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on"
        )
        if self.queues > 1:
            vm_params["opt_queue"] = self.queues
            opt_args = opt_args + ",mq=on,vectors=%d" % (2 * self.queues + 2)
        if packed:
            opt_args = opt_args + ",packed=on"
        vm_params["opt_settings"] = opt_args
        self.vm.set_vm_device(**vm_params)
        try:
            self.vm_dut = self.vm.start(set_target=set_target, bind_dev=bind_dev)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def config_virito_net_in_vm(self):
        """
        config ip for virtio net
        set net for multi queues enable
        """
        self.vm_intf = self.vm_dut.ports_info[0]["intf"]
        self.vm_dut.send_expect("ifconfig %s down" % self.vm_intf, "#")
        out = self.vm_dut.send_expect("ifconfig", "#")
        self.verify(self.vm_intf not in out, "the virtio-pci down failed")
        self.vm_dut.send_expect("ifconfig %s up" % self.vm_intf, "#")
        if self.queues > 1:
            self.vm_dut.send_expect(
                "ethtool -L %s combined %d" % (self.vm_intf, self.queues), "#", 20
            )

    def start_to_send_packets(self, delay):
        """
        start send packets
        """
        tgen_input = []
        port = self.tester.get_local_port(self.dut_ports[0])
        self.tester.scapy_append(
            'a=[Ether(dst="%s")/IP(src="0.240.74.101",proto=255)/UDP()/("X"*18)]'
            % (self.dst_mac)
        )
        self.tester.scapy_append('wrpcap("%s/interrupt.pcap", a)' % self.out_path)
        self.tester.scapy_execute()
        tgen_input.append((port, port, "%s/interrupt.pcap" % self.out_path))
        self.tester.pktgen.clear_streams()
        fields_config = {
            "ip": {
                "dst": {"action": "random"},
            },
        }
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, 1, fields_config, self.tester.pktgen
        )
        traffic_opt = {"delay": 5, "duration": delay, "rate": 1}
        _, self.flag = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=traffic_opt
        )

    def check_packets_after_reload_virtio_device(self, reload_times):
        """
        start to send packets and check virtio net has receive packets
        """
        # ixia send packets times equal to reload_times * wait_times
        start_time = time.time()
        _thread.start_new_thread(self.start_to_send_packets, (reload_times * 20,))
        # wait the ixia begin to send packets
        time.sleep(10)
        self.vm_pci = self.vm_dut.ports_info[0]["pci"]
        # reload virtio device to check the virtio-net can receive packets
        for i in range(reload_times + 1):
            if time.time() - start_time > reload_times * 30:
                self.logger.error(
                    "The ixia has stop to send packets, please change the delay time of ixia"
                )
                self.logger.info("The virtio device has reload %d times" % i)
                return False
            self.logger.info("The virtio net device reload %d times" % i)
            self.vm_dut.send_expect(
                "tcpdump -n -vv -i %s" % self.vm_intf, "tcpdump", 30
            )
            time.sleep(5)
            out = self.vm_dut.get_session_output(timeout=3)
            self.vm_dut.send_expect("^c", "#", 30)
            self.verify(
                "ip-proto-255" in out,
                "The virtio device can not receive packets after reload %d times" % i,
            )
            time.sleep(2)
            # reload virtio device
            self.vm_dut.restore_interfaces()
            time.sleep(3)
            self.vm_dut.send_expect("ifconfig %s down" % self.vm_intf, "#")
            self.vm_dut.send_expect("ifconfig %s up" % self.vm_intf, "#")
        # wait ixia thread exit
        self.logger.info("wait the thread of ixia to exit")
        while 1:
            if self.flag is not None:
                break
            time.sleep(5)
        return True

    def check_each_queue_has_packets_info_on_vhost(self):
        """
        check each queue has receive packets on vhost side
        """
        out = self.vhost_pmd.execute_cmd("stop")
        print(out)
        for queue_index in range(0, self.queues):
            queue = re.search("Port= 0/Queue=\s*%d" % queue_index, out)
            queue = queue.group()
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(
                rx_packets > 0 and tx_packets > 0,
                "The queue %d rx-packets or tx-packets is 0 about " % queue_index
                + "rx-packets:%d, tx-packets:%d" % (rx_packets, tx_packets),
            )
        self.vhost_pmd.execute_cmd("clear port stats all")

    def stop_all_apps(self):
        """
        close all vms
        """
        self.vm.stop()
        self.vhost_pmd.quit()

    def test_perf_split_ring_virito_pci_driver_reload_test_with_cbdma_enable(self):
        """
        Test Case1: Split ring virtio-pci driver reload test with CBDMA enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        vhost_eal_param = "--vdev 'net_vhost,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        ports = cbdmas
        ports.append(self.dut.ports_info[0]["pci"])
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("start")
        self.queues = 1
        self.start_vms(packed=False)
        self.config_virito_net_in_vm()
        res = self.check_packets_after_reload_virtio_device(reload_times=10)
        self.verify(res is True, "Should increase the wait times of ixia")
        self.stop_all_apps()

    def test_perf_split_ring_16_queues_virtio_net_event_idx_interrupt_mode_test_with_cbdma_enable(
        self,
    ):
        """
        Test Case2: Split ring 16 queues virtio-net event idx interrupt mode test with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
            )
        )
        vhost_param = "--nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16"
        vhost_eal_param = (
            "--vdev 'net_vhost,iface=vhost-net,queues=16,client=1,dmas=[%s]'" % dmas
        )
        ports = cbdmas
        ports.append(self.dut.ports_info[0]["pci"])
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("start")
        self.queues = 16
        self.start_vms(packed=False, mode="server")
        self.config_virito_net_in_vm()
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.vhost_pmd.execute_cmd("start")
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.stop_all_apps()

    def test_perf_packed_ring_virito_pci_driver_reload_test_with_cbdma_enable(self):
        """
        Test Case3: Packed ring virtio-pci driver reload test with CBDMA enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
        )
        vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024"
        vhost_eal_param = "--vdev 'net_vhost,iface=vhost-net,queues=1,dmas=[%s]'" % dmas
        ports = cbdmas
        ports.append(self.dut.ports_info[0]["pci"])
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("start")
        self.queues = 1
        self.start_vms(packed=True)
        self.config_virito_net_in_vm()
        res = self.check_packets_after_reload_virtio_device(reload_times=10)
        self.verify(res is True, "Should increase the wait times of ixia")
        self.stop_all_apps()

    def test_perf_packed_ring_16_queues_virtio_net_event_idx_interrupt_mode_test_with_cbdma_enable(
        self,
    ):
        """
        Test Case4: Packed ring 16 queues virtio-net event idx interrupt mode test with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
            )
        )
        vhost_param = "--nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16"
        vhost_eal_param = (
            "--vdev 'net_vhost,iface=vhost-net,queues=16,client=1,dmas=[%s]'" % dmas
        )
        ports = cbdmas
        ports.append(self.dut.ports_info[0]["pci"])
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=vhost_eal_param,
            param=vhost_param,
        )
        self.vhost_pmd.execute_cmd("start")
        self.queues = 16
        self.start_vms(packed=True, mode="server")
        self.config_virito_net_in_vm()
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.vhost_pmd.execute_cmd("start")
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.stop_all_apps()

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
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
        self.dut.close_session(self.vhost_user)

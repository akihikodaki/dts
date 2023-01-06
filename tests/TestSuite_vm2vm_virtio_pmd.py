# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM


class TestVM2VMVirtioPMD(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.vm_num = 2
        self.dump_pcap = "/root/pdump-rx.pcap"
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.virtio_user1_pmd = PmdOutput(self.dut, self.virtio_user1)
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_user_core = self.cores_list[0:2]
        self.virtio_user0_core = self.cores_list[2:4]
        self.virtio_user1_core = self.cores_list[4:6]
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.testpmd_path = self.dut.apps_name["test-pmd"]
        self.pdump_path = self.dut.apps_name["pdump"]
        self.testpmd_name = self.testpmd_path.split("/")[-1]

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
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_dut = []
        self.vm = []

    def start_vhost_testpmd(self):
        """
        launch the testpmd on vhost-user side
        """
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1'"
        )
        param = "--nb-cores=1 --txd=1024 --rxd=1024"
        self.vhost_user_pmd.start_testpmd(
            cores=self.vhost_user_core,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="vhost-user",
            fixed_prefix=True,
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_virtio_testpmd_with_vhost_net1(self, path_mode, extern_param):
        """
        launch the testpmd as virtio with vhost_net1
        """
        eal_param = (
            "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=vhost-net1,queues=1,%s "
            % path_mode
        )
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        param = "--nb-cores=1 --txd=1024 --rxd=1024 %s" % extern_param
        self.virtio_user1_pmd.start_testpmd(
            cores=self.virtio_user1_core,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user1",
            fixed_prefix=True,
        )
        self.virtio_user1_pmd.execute_cmd("set fwd rxonly")
        self.virtio_user1_pmd.execute_cmd("start")

    def start_virtio_testpmd_with_vhost_net0(self, path_mode, extern_param):
        """
        launch the testpmd as virtio with vhost_net0
        """
        eal_param = (
            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,queues=1,%s "
            % path_mode
        )
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        param = "--nb-cores=1 --txd=1024 --rxd=1024 %s" % extern_param
        self.virtio_user0_pmd.start_testpmd(
            cores=self.virtio_user0_core,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user0",
            fixed_prefix=True,
        )
        self.virtio_user0_pmd.execute_cmd("set txpkts 2000,2000,2000,2000")
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("start tx_first 10")

    def start_vm_testpmd(
        self, vm_client, path_mode, extern_param="", virtio_net_pci=""
    ):
        """
        launch the testpmd in vm
        """
        # deal with ports
        w_pci_list = []
        w_pci_list.append("-a %s,%s" % (virtio_net_pci, "vectorized=1"))
        w_pci_str = " ".join(w_pci_list)
        if path_mode == "mergeable":
            command = (
                self.testpmd_path
                + " -c 0x3 -n 4 "
                + "--file-prefix=virtio -- -i --tx-offloads=0x00 --rx-offloads=0x00002000 "
                + "--enable-hw-vlan-strip "
            )
            command = command + "--txd=1024 --rxd=1024 %s"
            vm_client.send_expect(command % extern_param, "testpmd> ", 20)
        elif path_mode == "normal":
            command = (
                self.testpmd_path
                + " -c 0x3 -n 4 "
                + "--file-prefix=virtio -- -i --tx-offloads=0x00 "
                + "--enable-hw-vlan-strip "
            )
            command = command + "--txd=1024 --rxd=1024 %s"
            vm_client.send_expect(command % extern_param, "testpmd> ", 20)
        elif path_mode == "vector_rx":
            command = (
                self.testpmd_path + " -c 0x3 -n 4 " + "--file-prefix=virtio %s -- -i "
            )
            command = command + "--txd=1024 --rxd=1024 %s"
            vm_client.send_expect(command % (w_pci_str, extern_param), "testpmd> ", 20)

    def launch_pdump_to_capture_pkt(self, client_dut, dump_port):
        """
        launch pdump in VM
        """
        self.pdump_session = client_dut.new_session(suite="pdump")
        if hasattr(client_dut, "vm_name"):
            command_line = (
                self.pdump_path
                + " "
                + "-v --file-prefix=virtio -- "
                + "--pdump  '%s,queue=*,rx-dev=%s,mbuf-size=8000'"
            )
            self.pdump_session.send_expect(
                command_line % (dump_port, self.dump_pcap), "Port"
            )
        else:
            command_line = (
                self.pdump_path
                + " "
                + "-v --file-prefix=virtio_%s -- "
                + "--pdump  '%s,queue=*,rx-dev=%s,mbuf-size=8000'"
            )
            self.pdump_session.send_expect(
                command_line % (self.dut.prefix_subfix, dump_port, self.dump_pcap),
                "Port",
            )

    def start_vms(
        self,
        setting_args="",
        server_mode=False,
        opt_queue=1,
    ):
        vm_params = {}

        if opt_queue > 1:
            vm_params["opt_queue"] = opt_queue

        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, "vm%d" % i, "vhost_sample")

            vm_params["driver"] = "vhost-user"
            if not server_mode:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            else:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i + ",server"
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            vm_params["opt_settings"] = setting_args
            vm_info.set_vm_device(**vm_params)
            time.sleep(3)
            try:
                vm_dut = vm_info.start(set_target=True, bind_dev=True)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print((utils.RED("Failure for %s" % str(e))))
                raise e
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def calculate_avg_throughput(self):
        results = 0.0
        self.vhost_user.send_expect("show port stats 1", "testpmd> ", 60)
        for i in range(10):
            out = self.vhost_user.send_expect("show port stats 1", "testpmd> ", 60)
            time.sleep(1)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.verify(Mpps > 4.5, "%s can not receive packets" % self.running_case)
        return Mpps

    def update_table_info(self, case_info, frame_size, Mpps, path):
        results_row = [frame_size]
        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(1)
        results_row.append(path)
        self.result_table_add(results_row)

    def send_and_verify(self, mode, path):
        """
        start to send packets and verify it
        """
        # start to send packets
        self.vm_dut[0].send_expect("set fwd rxonly", "testpmd> ")
        self.vm_dut[0].send_expect("start", "testpmd> ")
        self.vm_dut[1].send_expect("set fwd txonly", "testpmd> ")
        self.vm_dut[1].send_expect("set txpkts 64", "testpmd> ")
        self.vm_dut[1].send_expect("start tx_first 32", "testpmd> ")
        Mpps = self.calculate_avg_throughput()
        self.update_table_info(mode, 64, Mpps, path)
        self.result_table_print()

    def check_packet_payload_valid(self, client_dut):
        """
        check the payload is valid
        """
        # stop pdump
        self.pdump_session.send_expect("^c", "# ", 60)
        # quit testpmd
        client_dut.send_expect("quit", "#", 60)
        time.sleep(2)
        client_dut.session.copy_file_from(
            src="%s" % self.dump_pcap, dst="%s" % self.dump_pcap
        )
        pkt = Packet()
        pkts = pkt.read_pcapfile(self.dump_pcap)
        self.verify(len(pkts) == 10, "The vm0 do not capture all the packets")
        data = str(pkts[0]["Raw"])
        for i in range(1, 10):
            value = str(pkts[i]["Raw"])
            self.verify(
                data == value, "the payload in receive packets has been changed"
            )

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm_dut[i].send_expect("quit", "#", 20)
            self.vm[i].stop()
        self.vhost_user.send_expect("quit", "#", 30)
        if self.virtio_user1:
            self.virtio_user1.send_expect("quit", "# ", 30)
            self.dut.close_session(self.virtio_user1)
            self.virtio_user1 = None
        if self.virtio_user0:
            self.virtio_user0.send_expect("quit", "# ", 30)
            self.dut.close_session(self.virtio_user0)
            self.virtio_user0 = None

    def test_vm2vm_vhost_user_virtio95_pmd_with_vector_rx_path(self):
        """
        Test Case 1: VM2VM vhost-user/virtio0.95-pmd with vector_rx path
        """
        path_mode = "vector_rx"
        setting_args = "disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        self.start_vm_testpmd(
            self.vm_dut[0],
            path_mode,
            virtio_net_pci=self.vm_dut[0].ports_info[0]["pci"],
        )
        self.start_vm_testpmd(
            self.vm_dut[1],
            path_mode,
            virtio_net_pci=self.vm_dut[1].ports_info[0]["pci"],
        )
        self.send_and_verify(mode="virtio 0.95 vector_rx", path=path_mode)

    def test_vm2vm_vhost_user_virtio95_pmd_with_normal_path(self):
        """
        Test Case 2: VM2VM vhost-user/virtio0.95-pmd with normal path
        """
        setting_args = "disable-modern=true,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        path_mode = "normal"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 0.95 normal path", path=path_mode)

    def test_vm2vm_vhost_user_virtio10_pmd_with_vector_rx_path(self):
        """
        Test Case 3: VM2VM vhost-user/virtio1.0-pmd with vector_rx path
        """
        path_mode = "vector_rx"
        setting_args = "disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        self.start_vm_testpmd(
            self.vm_dut[0],
            path_mode,
            virtio_net_pci=self.vm_dut[0].ports_info[0]["pci"],
        )
        self.start_vm_testpmd(
            self.vm_dut[1],
            path_mode,
            virtio_net_pci=self.vm_dut[1].ports_info[0]["pci"],
        )
        self.send_and_verify(mode="virtio 1.0 vector_rx", path=path_mode)

    def test_vm2vm_vhost_user_virito10_pmd_with_normal_path(self):
        """
        Test Case 4: VM2VM vhost-user/virtio1.0-pmd with normal path
        """
        path_mode = "normal"
        setting_args = "disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 1.0 normal path", path=path_mode)

    def test_vm2vm_vhost_user_virtio95_pmd_with_mergeable_path_with_payload_valid_check(
        self,
    ):
        """
        Test Case 5: VM2VM vhost-user/virtio0.95-pmd mergeable path with payload valid check
        """
        path_mode = "mergeable"
        setting_args = "disable-modern=true,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        extern_param = "--max-pkt-len=9600"
        dump_port = "port=0"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        # start testpmd and pdump in VM0
        self.start_vm_testpmd(self.vm_dut[0], path_mode, extern_param)
        self.vm_dut[0].send_expect("set fwd rxonly", "testpmd> ", 30)
        self.vm_dut[0].send_expect("start", "testpmd> ", 30)
        self.launch_pdump_to_capture_pkt(self.vm_dut[0], dump_port)
        # start testpmd in VM1 and start to send packet
        self.start_vm_testpmd(self.vm_dut[1], path_mode, extern_param)
        self.vm_dut[1].send_expect("set txpkts 2000,2000,2000,2000", "testpmd> ", 30)
        self.vm_dut[1].send_expect("set burst 1", "testpmd> ", 30)
        self.vm_dut[1].send_expect("start tx_first 10", "testpmd> ", 30)
        # check the packet in vm0
        self.check_packet_payload_valid(self.vm_dut[0])

    def test_vm2vm_vhost_user_virtio10_pmd_with_mergeable_path_with_payload_valid_check(
        self,
    ):
        """
        Test Case 6: VM2VM vhost-user/virtio1.0-pmd mergeable path with payload valid check
        """
        path_mode = "mergeable"
        setting_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        extern_param = "--max-pkt-len=9600"
        dump_port = "port=0"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        # start testpmd and pdump in VM0
        self.start_vm_testpmd(self.vm_dut[0], path_mode, extern_param)
        self.vm_dut[0].send_expect("set fwd rxonly", "testpmd> ", 30)
        self.vm_dut[0].send_expect("start", "testpmd> ", 30)
        self.launch_pdump_to_capture_pkt(self.vm_dut[0], dump_port)
        # start testpmd in VM1 and start to send packet
        self.start_vm_testpmd(self.vm_dut[1], path_mode, extern_param)
        self.vm_dut[1].send_expect("set txpkts 2000,2000,2000,2000", "testpmd> ", 30)
        self.vm_dut[1].send_expect("set burst 1", "testpmd> ", 30)
        self.vm_dut[1].send_expect("start tx_first 10", "testpmd> ", 30)
        # check the packet in vm0
        self.check_packet_payload_valid(self.vm_dut[0])

    def test_vm2vm_vhost_user_virtio11_pmd_with_mergeable_path_with_payload_valid_check(
        self,
    ):
        """
        Test Case 7: VM2VM vhost-user/virtio1.1-pmd mergeable path with payload valid check
        """
        path_mode = "mergeable"
        setting_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        extern_param = "--max-pkt-len=9600"
        dump_port = "port=0"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        # start testpmd and pdump in VM0
        self.start_vm_testpmd(self.vm_dut[0], path_mode, extern_param)
        self.vm_dut[0].send_expect("set fwd rxonly", "testpmd> ", 30)
        self.vm_dut[0].send_expect("start", "testpmd> ", 30)
        self.launch_pdump_to_capture_pkt(self.vm_dut[0], dump_port)
        # start testpmd in VM1 and start to send packet
        self.start_vm_testpmd(self.vm_dut[1], path_mode, extern_param)
        self.vm_dut[1].send_expect("set txpkts 2000,2000,2000,2000", "testpmd> ", 30)
        self.vm_dut[1].send_expect("set burst 1", "testpmd> ", 30)
        self.vm_dut[1].send_expect("start tx_first 10", "testpmd> ", 30)
        # check the packet in vm0
        self.check_packet_payload_valid(self.vm_dut[0])

    def test_vm2vm_vhost_user_virito11_pmd_with_normal_path(self):
        """
        Test Case 8: VM2VM vhost-user/virtio1.1-pmd with normal path
        """
        path_mode = "normal"
        setting_args = "disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vhost_testpmd()
        self.start_vms(setting_args=setting_args)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 1.1 normal path", path=path_mode)

    def check_port_stats_result(self, vm_dut, queue_num=0):
        out = vm_dut.send_expect("show port stats all", "testpmd> ", 30)
        rx_packets = re.findall(r"RX-packets: (\w+)", out)
        tx_packets = re.findall(r"TX-packets: (\w+)", out)
        self.verify(int(rx_packets[0]) > 1, "RX packets no correctly")
        self.verify(int(tx_packets[0]) > 1, "TX packets no correctly")
        self.check_packets_of_each_queue(vm_dut, queue_num)

    def check_packets_of_each_queue(self, vm_dut, queue_num):
        """
        check each queue has receive packets
        """
        out = vm_dut.send_expect("stop", "testpmd> ", 60)
        for queue_index in range(queue_num):
            queue = "Queue= %d" % queue_index
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
        vm_dut.send_expect("clear port stats all", "testpmd> ", 30)
        vm_dut.send_expect("start", "testpmd> ", 30)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)

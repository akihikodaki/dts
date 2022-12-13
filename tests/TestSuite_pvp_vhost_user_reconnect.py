# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.

Vhost reconnect two VM test suite.
Becase this suite will use the reconnet feature, the VM will start as
server mode, so the qemu version should greater than 2.7
"""
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.test_case import TestCase
from framework.virt_common import VM


class TestPVPVhostUserReconnect(TestCase):
    def set_up_all(self):

        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")

        # Get the port's socket
        self.pf = self.dut_ports[0]
        netdev = self.dut.ports_info[self.pf]["port"]
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.socket = netdev.get_nic_socket()
        self.cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        # set diff arg about mem_socket base on socket number
        if len(set([int(core["socket"]) for core in self.dut.cores])) == 1:
            self.socket_mem = "1024"
        else:
            self.socket_mem = "1024,1024"

        self.reconnect_times = 5
        self.vm_num = 1
        self.frame_sizes = [64, 1518]
        self.virtio_ip = ["1.1.1.2", "1.1.1.3"]
        self.virtio_mac = ["52:54:00:00:00:01", "52:54:00:00:00:02"]
        self.src1 = "192.168.4.1"
        self.dst1 = "192.168.3.1"
        self.checked_vm = False

        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]

    def set_up(self):
        """
        run before each test case.
        clear the execution ENV
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
        self.dut.send_expect("rm -rf ./vhost-net*", "# ")
        self.vhost_user = self.dut.new_session(suite="vhost-user")

    def launch_testpmd_as_vhost_user(self):
        """
        launch the testpmd as vhost user
        """
        vdev_info = ""
        for i in range(self.vm_num):
            vdev_info += "--vdev 'net_vhost%d,iface=vhost-net%d,client=1,queues=1' " % (
                i,
                i,
            )
        testcmd = self.dut.base_dir + "/%s" % self.path
        eal_params = self.dut.create_eal_parameters(
            cores=self.cores, prefix="vhost", ports=[self.pci_info]
        )
        para = " -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024"
        self.vhostapp_testcmd = testcmd + eal_params + vdev_info + para
        self.vhost_user.send_expect(self.vhostapp_testcmd, "testpmd> ", 40)
        self.vhost_user.send_expect("set fwd mac", "testpmd> ", 40)
        self.vhost_user.send_expect("start", "testpmd> ", 40)

    def launch_testpmd_as_vhost_user_with_no_pci(self):
        """
        launch the testpmd as vhost user
        """
        vdev_info = ""
        for i in range(self.vm_num):
            vdev_info += "--vdev 'net_vhost%d,iface=vhost-net%d,client=1,queues=1' " % (
                i,
                i,
            )
        testcmd = self.dut.base_dir + "/%s" % self.path
        eal_params = self.dut.create_eal_parameters(
            cores=self.cores, no_pci=True, prefix="vhost"
        )
        para = " -- -i --nb-cores=1 --txd=1024 --rxd=1024"
        self.vhostapp_testcmd = testcmd + eal_params + vdev_info + para
        self.vhost_user.send_expect(self.vhostapp_testcmd, "testpmd> ", 40)
        self.vhost_user.send_expect("start", "testpmd> ", 40)

    def check_link_status_after_testpmd_start(self, dut_info):
        """
        check the link status is up after testpmd start
        """
        loop = 1
        while loop <= 5:
            out = dut_info.send_expect("show port info all", "testpmd> ", 120)
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if "down" not in port_status:
                break
            time.sleep(3)
            loop = loop + 1

        self.verify("down" not in port_status, "port can not up after restart")

    def check_qemu_version(self, vm_config):
        """
        in this suite, the qemu version should greater 2.7
        """
        if self.checked_vm:
            return

        self.vm_qemu_version = vm_config.qemu_emulator
        params_number = len(vm_config.params)
        for i in range(params_number):
            if list(vm_config.params[i].keys())[0] == "qemu":
                self.vm_qemu_version = vm_config.params[i]["qemu"][0]["path"]

        out = self.dut.send_expect("%s --version" % self.vm_qemu_version, "#")
        result = re.search("QEMU\s*emulator\s*version\s*(\d*.\d*)", out)
        self.verify(
            result is not None,
            "the qemu path may be not right: %s" % self.vm_qemu_version,
        )
        version = result.group(1)
        index = version.find(".")
        self.verify(
            int(version[:index]) > 2
            or (int(version[:index]) == 2 and int(version[index + 1 :]) >= 7),
            "This qemu version should greater than 2.7 "
            + "in this suite, please config it in vhost_sample.cfg file",
        )
        self.checked_vm = True

    def start_vms(self, packed=False, bind_dev=True):
        """
        start two VM
        """
        self.vm_dut = []
        self.vm = []
        setting_args = "mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024"
        if packed is True:
            setting_args = "%s,packed=on" % setting_args
        for i in range(self.vm_num):
            vm_info = VM(self.dut, "vm%d" % i, "vhost_sample")
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            vm_params["opt_path"] = "./vhost-net%d" % (i)
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            vm_params["opt_server"] = "server"
            vm_params["opt_settings"] = setting_args
            vm_info.set_vm_device(**vm_params)
            self.check_qemu_version(vm_info)

            try:
                vm_dut = None
                vm_dut = vm_info.start(bind_dev=bind_dev)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print(utils.RED("Failure for %s" % str(e)))
            self.verify(vm_dut is not None, "start vm failed")
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def vm_testpmd_start(self):
        """
        start testpmd in vm
        """
        vm_testpmd = (
            self.path
            + " -c 0x3 -n 4 "
            + "-- -i --port-topology=chained --txd=1024 --rxd=1024 "
        )
        for i in range(len(self.vm_dut)):
            self.vm_dut[i].send_expect(vm_testpmd, "testpmd> ", 20)
            self.vm_dut[i].send_expect("set fwd mac", "testpmd> ")
            self.vm_dut[i].send_expect("start", "testpmd> ")

        self.check_link_status_after_testpmd_start(self.vhost_user)

    def stop_all_apps(self):
        """
        quit the testpmd in vm and stop all apps
        """
        for i in range(len(self.vm_dut)):
            self.vm_dut[i].send_expect("stop", "testpmd> ", 20)
            self.vm_dut[i].send_expect("quit", "# ", 20)
            self.vm[i].stop()
        self.vhost_user.send_expect("quit", "# ", 20)

    def config_vm_intf(self):
        """
        restore vm interfaces and config intf arp
        """
        for i in range(len(self.vm_dut)):
            vm_intf = self.vm_dut[i].ports_info[0]["intf"]
            self.vm_dut[i].send_expect(
                "ifconfig %s %s" % (vm_intf, self.virtio_ip[i]), "#", 10
            )
            self.vm_dut[i].send_expect("ifconfig %s up" % vm_intf, "#", 10)

        self.vm_dut[0].send_expect(
            "arp -s %s %s" % (self.virtio_ip[1], self.virtio_mac[1]), "#", 10
        )
        self.vm_dut[1].send_expect(
            "arp -s %s %s" % (self.virtio_ip[0], self.virtio_mac[0]), "#", 10
        )

    def start_iperf(self):
        """
        start iperf
        """
        self.vm_dut[0].send_expect(
            "iperf -s -p 12345 -i 1 > iperf_server.log &", "", 10
        )
        self.vm_dut[1].send_expect(
            "iperf -c %s -p 12345 -i 1 -t 10 > iperf_client.log &" % self.virtio_ip[0],
            "",
            60,
        )
        time.sleep(15)

    def iperf_result_verify(self, cycle, tinfo):
        """
        verify the Iperf test result
        """
        # copy iperf_client file from vm1
        self.vm_dut[1].session.copy_file_from("%s/iperf_client.log" % self.dut.base_dir)
        fp = open("./iperf_client.log")
        fmsg = fp.read()
        fp.close()
        iperfdata = re.compile("\S*\s*[M|G]bits/sec").findall(fmsg)
        self.verify(len(iperfdata) != 0, "The iperf data between to vms is 0")
        if cycle == 0:
            cinfo = "Before reconnet"
        else:
            cinfo = tinfo
        self.result_table_add(["vm2vm iperf", iperfdata[-1], cinfo])
        data_li = iperfdata[-1].strip().split()
        if self.nic in ["I40E_40G-QSFP_A"]:
            self.verify(data_li[1] == "Gbits/sec", "data unit not correct")
        return float(data_li[0])

    def send_and_verify(self, cycle=0, tinfo=""):
        frame_data = dict().fromkeys(self.frame_sizes, 0)
        for frame_size in self.frame_sizes:
            pkt = Packet(pkt_type="UDP", pkt_len=frame_size)
            pkt.config_layers(
                [
                    ("ether", {"dst": "%s" % self.dst_mac}),
                    ("ipv4", {"dst": "%s" % self.dst1, "src": "%s" % self.src1}),
                ]
            )
            pkt.save_pcapfile(self.tester, "%s/reconnect.pcap" % self.out_path)

            tgenInput = []
            port = self.tester.get_local_port(self.pf)
            tgenInput.append((port, port, "%s/reconnect.pcap" % self.out_path))

            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgenInput, 100, None, self.tester.pktgen
            )
            traffic_opt = {
                "delay": 30,
            }
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=traffic_opt
            )
            Mpps = pps / 1000000.0
            if self.running_case in [
                "test_perf_packed_ring_reconnet_two_vms",
                "test_perf_split_ring_reconnet_two_vms",
            ]:
                check_speed = 2 if frame_size == 64 else 0.5
            else:
                check_speed = 5 if frame_size == 64 else 1
            self.verify(
                Mpps > check_speed,
                "can not receive packets of frame size %d" % (frame_size),
            )
            pct = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))
            frame_data[frame_size] = Mpps
            if cycle == 0:
                data_row = [
                    tinfo,
                    frame_size,
                    str(Mpps),
                    str(pct),
                    "Before relaunch",
                    "1",
                ]
            elif cycle == 1:
                data_row = [
                    tinfo,
                    frame_size,
                    str(Mpps),
                    str(pct),
                    "After relaunch",
                    "1",
                ]
            self.result_table_add(data_row)
        return frame_data

    def check_reconnect_perf(self):
        if isinstance(self.before_data, dict):
            for i in self.frame_sizes:
                self.verify(
                    (self.before_data[i] - self.reconnect_data[i])
                    < self.before_data[i] * 0.15,
                    "verify reconnect speed failed",
                )
        else:
            self.verify(
                (self.before_data - self.reconnect_data) < self.before_data * 0.15,
                "verify reconnect speed failed",
            )

    def test_perf_split_ring_reconnet_one_vm(self):
        """
        test reconnect stability test of one vm
        """
        self.header_row = [
            "Mode",
            "FrameSize(B)",
            "Throughput(Mpps)",
            "LineRate(%)",
            "Cycle",
            "Queue Number",
        ]
        self.result_table_create(self.header_row)
        vm_cycle = 0
        self.vm_num = 1
        self.launch_testpmd_as_vhost_user()
        self.start_vms()
        self.vm_testpmd_start()
        self.before_data = self.send_and_verify(vm_cycle, "reconnet one vm")

        vm_cycle = 1
        # reconnet from vhost
        self.logger.info("now reconnect from vhost")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
            self.launch_testpmd_as_vhost_user()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from vhost")
            self.check_reconnect_perf()

        # reconnet from qemu
        self.logger.info("now reconnect from vm")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
            self.start_vms()
            self.vm_testpmd_start()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from VM")
            self.check_reconnect_perf()
        self.result_table_print()

    def test_perf_split_ring_reconnet_two_vms(self):
        """
        test reconnect stability test of two vms
        """
        self.header_row = [
            "Mode",
            "FrameSize(B)",
            "Throughput(Mpps)",
            "LineRate(%)",
            "Cycle",
            "Queue Number",
        ]
        self.result_table_create(self.header_row)
        vm_cycle = 0
        self.vm_num = 2
        self.launch_testpmd_as_vhost_user()
        self.start_vms()
        self.vm_testpmd_start()
        self.before_data = self.send_and_verify(vm_cycle, "reconnet two vm")

        vm_cycle = 1
        # reconnet from vhost
        self.logger.info("now reconnect from vhost")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
            self.launch_testpmd_as_vhost_user()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from vhost")
            self.check_reconnect_perf()

        # reconnet from qemu
        self.logger.info("now reconnect from vm")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
            self.start_vms()
            self.vm_testpmd_start()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from VM")
            self.check_reconnect_perf()
        self.result_table_print()

    def test_perf_split_ring_vm2vm_virtio_net_reconnet_two_vms(self):
        """
        test the iperf traffice can resume after reconnet
        """
        self.header_row = ["Mode", "[M|G]bits/sec", "Cycle"]
        self.result_table_create(self.header_row)
        self.vm_num = 2
        vm_cycle = 0
        self.launch_testpmd_as_vhost_user_with_no_pci()
        self.start_vms(bind_dev=False)
        self.config_vm_intf()
        self.start_iperf()
        self.before_data = self.iperf_result_verify(vm_cycle, "before reconnet")

        vm_cycle = 1
        # reconnet from vhost
        self.logger.info("now reconnect from vhost")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
            self.launch_testpmd_as_vhost_user_with_no_pci()
            self.start_iperf()
            self.reconnect_data = self.iperf_result_verify(
                vm_cycle, "reconnet from vhost"
            )
            self.check_reconnect_perf()

        # reconnet from VM
        self.logger.info("now reconnect from vm")
        vm_tmp = list()
        for i in range(self.reconnect_times):
            self.vm_dut[0].send_expect("rm iperf_server.log", "# ", 10)
            self.vm_dut[1].send_expect("rm iperf_client.log", "# ", 10)
            self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
            self.start_vms(bind_dev=False)
            self.config_vm_intf()
            self.start_iperf()
            self.reconnect_data = self.iperf_result_verify(vm_cycle, "reconnet from vm")
            self.check_reconnect_perf()
        self.result_table_print()

    def test_perf_packed_ring_reconnet_one_vm(self):
        """
        test reconnect stability test of one vm
        """
        self.header_row = [
            "Mode",
            "FrameSize(B)",
            "Throughput(Mpps)",
            "LineRate(%)",
            "Cycle",
            "Queue Number",
        ]
        self.result_table_create(self.header_row)
        vm_cycle = 0
        self.vm_num = 1
        self.launch_testpmd_as_vhost_user()
        self.start_vms(packed=True)
        self.vm_testpmd_start()
        self.before_data = self.send_and_verify(vm_cycle, "reconnet one vm")

        vm_cycle = 1
        # reconnet from vhost
        self.logger.info("now reconnect from vhost")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
            self.launch_testpmd_as_vhost_user()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from vhost")
            self.check_reconnect_perf()

        # reconnet from qemu
        self.logger.info("now reconnect from vm")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
            self.start_vms(packed=True)
            self.vm_testpmd_start()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from VM")
            self.check_reconnect_perf()
        self.result_table_print()

    def test_perf_packed_ring_reconnet_two_vms(self):
        """
        test reconnect stability test of two vms
        """
        self.header_row = [
            "Mode",
            "FrameSize(B)",
            "Throughput(Mpps)",
            "LineRate(%)",
            "Cycle",
            "Queue Number",
        ]
        self.result_table_create(self.header_row)
        vm_cycle = 0
        self.vm_num = 2
        self.launch_testpmd_as_vhost_user()
        self.start_vms(packed=True)
        self.vm_testpmd_start()
        self.before_data = self.send_and_verify(vm_cycle, "reconnet two vm")

        vm_cycle = 1
        # reconnet from vhost
        self.logger.info("now reconnect from vhost")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
            self.launch_testpmd_as_vhost_user()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from vhost")
            self.check_reconnect_perf()
        # reconnet from qemu
        self.logger.info("now reconnect from vm")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
            self.start_vms(packed=True)
            self.vm_testpmd_start()
            self.reconnect_data = self.send_and_verify(vm_cycle, "reconnet from VM")
            self.check_reconnect_perf()
        self.result_table_print()

    def test_perf_packed_ring_virtio_net_reconnet_two_vms(self):
        """
        test the iperf traffice can resume after reconnet
        """
        self.header_row = ["Mode", "[M|G]bits/sec", "Cycle"]
        self.result_table_create(self.header_row)
        self.vm_num = 2
        vm_cycle = 0
        self.launch_testpmd_as_vhost_user_with_no_pci()
        self.start_vms(packed=True, bind_dev=False)
        self.config_vm_intf()
        self.start_iperf()
        self.before_data = self.iperf_result_verify(vm_cycle, "before reconnet")

        vm_cycle = 1
        # reconnet from vhost
        self.logger.info("now reconnect from vhost")
        for i in range(self.reconnect_times):
            self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
            self.launch_testpmd_as_vhost_user_with_no_pci()
            self.start_iperf()
            self.reconnect_data = self.iperf_result_verify(
                vm_cycle, "reconnet from vhost"
            )
            self.check_reconnect_perf()

        # reconnet from VM
        self.logger.info("now reconnect from vm")
        for i in range(self.reconnect_times):
            self.vm_dut[0].send_expect("rm iperf_server.log", "# ", 10)
            self.vm_dut[1].send_expect("rm iperf_client.log", "# ", 10)
            self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
            self.start_vms(packed=True, bind_dev=False)
            self.config_vm_intf()
            self.start_iperf()
            self.reconnect_data = self.iperf_result_verify(vm_cycle, "reconnet from vm")
            self.check_reconnect_perf()
        self.result_table_print()

    def tear_down(self):
        #
        # Run after each test case.
        #
        try:
            self.stop_all_apps()
        except Exception as e:
            self.logger.warning(e)
        finally:
            self.dut.kill_all()
            self.dut.send_expect("killall -s INT qemu-system-x86_64", "# ")
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        pass

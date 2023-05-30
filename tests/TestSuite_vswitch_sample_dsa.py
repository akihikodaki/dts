# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

"""
DPDK Test suite.
"""

import random
import re
import string
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM

from .virtio_common import dsa_common as DC


class TestVswitchSampleDsa(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        out = self.dut.build_dpdk_apps("./examples/vhost")
        self.verify("Error" not in out, "compilation vhost error")
        self.vhost_path = self.dut.apps_name["vhost"]
        self.tester_tx_port_num = 1
        self.dut_ports = self.dut.get_ports()
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
        self.virtio_dst_mac0 = "00:11:22:33:44:10"
        self.virtio_dst_mac1 = "00:11:22:33:44:11"
        self.vm_dst_mac0 = "52:54:00:00:00:01"
        self.vm_dst_mac1 = "52:54:00:00:00:02"
        self.vm_num = 2
        # create an instance to set stream field setting
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.virtio_user1_pmd = PmdOutput(self.dut, self.virtio_user1)
        self.random_string = string.ascii_letters + string.digits
        self.virtio_ip0 = "1.1.1.2"
        self.virtio_ip1 = "1.1.1.3"
        self.rerun_times = 5
        self.DC = DC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.table_header = ["Frame Size(Byte)", "Mode", "Throughput(Mpps)"]
        self.result_table_create(self.table_header)
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -I dpdk-vhost", "#", 20)
        self.dut.send_expect("killall -I qemu-system-x86_64", "#", 20)
        self.vm_dut = []
        self.vm = []

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def launch_vhost_app(
        self, eal_params, vdev_num, dmas, mergeable=True, tso=False, client_mode=True
    ):
        """
        launch the vhost app on vhost side
        """
        vdev_param = ""
        for i in range(vdev_num):
            vdev_param += "--socket-file ./vhost-net{} ".format(i)
        mergeable_param = "--mergeable 1" if mergeable else ""
        tso_param = "--tso 1" if tso else ""
        client_param = "--client" if client_mode else ""
        cmd = (
            "%s %s -- -p 0x1 %s %s --vm2vm 1  --stats 1 \
        %s --dmas [%s] \
        %s --total-num-mbufs 600000"
            % (
                self.vhost_path,
                eal_params,
                tso_param,
                mergeable_param,
                vdev_param,
                dmas,
                client_param,
            )
        )
        self.vhost_user.send_command(cmd)
        time.sleep(3)

    def start_virtio_testpmd_with_vhost_net0(self, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net0
        """
        if self.check_2M_env:
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
        if self.check_2M_env:
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
        moderns=["true", "true"],
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
        packed = ",packed=on" if packed else ""
        for i in range(self.vm_num):
            vm_dut = None
            setting_format = "disable-modern=%s,mrg_rxbuf=%s,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on%s"
            setting_args = setting_format % (moderns[i], mrg_rxbuf, packed)
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

    def let_vswitch_know_mac(self, virtio_pmd, relaunch=False):
        if not relaunch:
            virtio_pmd.execute_cmd("set fwd mac")
            virtio_pmd.execute_cmd("start tx_first")
        else:
            virtio_pmd.execute_cmd("stop")
            virtio_pmd.execute_cmd("start tx_first")

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

    def vm2vm_check_with_two_dsa(self):
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

    def test_vm2vm_virtio_user_forwarding_test_using_dsa_dpdk_driver(self):
        """
        Test Case 1: VM2VM virtio-user forwarding test when vhost async operation using DSA dpdk driver
        """
        perf_result = []
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        ports = dsas
        ports.append(self.dut.ports_info[0]["pci"])
        port_options = {dsas[0]: "max_queues=4"}
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports, port_options=port_options
        )
        dmas = "txd0@%s-q0,rxd0@%s-q1,txd1@%s-q2,rxd1@%s-q3" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
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
        before_relunch_result = self.vm2vm_check_with_two_dsa()

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas = "txd0@%s-q0,rxd1@%s-q1" % (dsas[0], dsas[0])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )
        self.virtio_user0_pmd.execute_cmd("stop")
        after_relunch_result = self.vm2vm_check_with_two_dsa()

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
        self, moderns=["true", "true"], mrg_rxbuf=True, need_start_vm=True, packed=False
    ):
        if need_start_vm:
            self.start_vms(
                moderns=moderns,
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

    def test_vm2vm_virtio_pmd_split_ring_test_with_dsa_dpdk_driver_register_and_unregister_stable_check(
        self,
    ):
        """
        Test Case 2: VM2VM virtio-pmd split ring test with DSA dpdk driver register/unregister stable check
        """
        perf_result = []
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        ports = dsas
        ports.append(self.dut.ports_info[0]["pci"])
        port_options = {dsas[0]: "max_queues=4"}
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports, port_options=port_options
        )
        dmas = "txd0@%s-q0,rxd0@%s-q1,txd1@%s-q2,rxd1@%s-q3" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_rebind = self.start_vms_testpmd_and_test(
            moderns=["true", "false"], mrg_rxbuf=True, need_start_vm=True, packed=False
        )

        # repeat bind 50 time from virtio-pci to vfio-pci
        self.repeat_bind_driver(dut=self.vm_dut[0], repeat_times=50)
        self.repeat_bind_driver(dut=self.vm_dut[1], repeat_times=50)

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas = "txd0@%s-q0,rxd1@%s-q3" % (dsas[0], dsas[0])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        after_rebind = self.start_vms_testpmd_and_test(need_start_vm=False)

        for key in before_rebind.keys():
            perf_result.append([key, "Before rebind driver", before_rebind[key]])

        for key in after_rebind.keys():
            perf_result.append([key, "After rebind driver", after_rebind[key]])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        for i in perf_result:
            self.verify(i[2] > 0, "%s Frame Size(Byte) is less than 0 Mpps" % i[0])

    def test_vm2vm_virtio_pmd_packed_ring_test_with_dsa_dpdk_driver_register_and_unregister_stable_check(
        self,
    ):
        """
        Test Case 3: VM2VM virtio-pmd packed ring test with DSA dpdk driver register/unregister stable check
        """
        perf_result = []
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        ports = dsas
        ports.append(self.dut.ports_info[0]["pci"])
        port_options = {dsas[0]: "max_queues=4"}
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports, port_options=port_options
        )
        dmas = "txd0@%s-q0,rxd0@%s-q1,txd1@%s-q2,rxd1@%s-q3" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_rebind = self.start_vms_testpmd_and_test(
            moderns=["false", "false"], mrg_rxbuf=True, need_start_vm=True, packed=True
        )

        # repeat bind 50 time from virtio-pci to vfio-pci
        self.repeat_bind_driver(dut=self.vm_dut[0], repeat_times=50)
        self.repeat_bind_driver(dut=self.vm_dut[1], repeat_times=50)

        after_rebind = self.start_vms_testpmd_and_test(need_start_vm=False)

        for key in before_rebind.keys():
            perf_result.append([key, "Before rebind driver", before_rebind[key]])

        for key in after_rebind.keys():
            perf_result.append([key, "After rebind driver", after_rebind[key]])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        for i in perf_result:
            self.verify(i[2] > 0, "%s Frame Size(Byte) is less than 0 Mpps" % i[0])

    def config_vm_env(self):
        """
        set virtio device IP and run arp protocal
        """
        vm0_intf = self.vm_dut[0].ports_info[0]["intf"]
        vm1_intf = self.vm_dut[1].ports_info[0]["intf"]
        self.vm_dut[0].send_expect(
            "ifconfig %s %s" % (vm0_intf, self.virtio_ip0), "#", 10
        )
        self.vm_dut[1].send_expect(
            "ifconfig %s %s" % (vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm_dut[0].send_expect(
            "arp -s %s %s" % (self.virtio_ip1, self.vm_dst_mac1), "#", 10
        )
        self.vm_dut[1].send_expect(
            "arp -s %s %s" % (self.virtio_ip0, self.vm_dst_mac0), "#", 10
        )

    def start_iperf_test(self):
        """
        run perf command between to vms
        """
        iperf_server = "iperf -f g -s -i 1"
        iperf_client = "iperf -f g -c 1.1.1.2 -i 1 -t 60"
        self.vm_dut[0].send_expect("%s > iperf_server.log &" % iperf_server, "", 10)
        self.vm_dut[1].send_expect("%s > iperf_client.log &" % iperf_client, "", 60)
        time.sleep(90)

    def get_iperf_result(self):
        """
        get the iperf test result
        """
        self.vm_dut[0].send_expect("pkill iperf", "# ")
        self.vm_dut[1].session.copy_file_from("%s/iperf_client.log" % self.dut.base_dir)
        fp = open("./iperf_client.log")
        fmsg = fp.read()
        fp.close()
        # remove the server report info from msg
        index = fmsg.find("Server Report")
        if index != -1:
            fmsg = fmsg[:index]
        iperfdata = re.compile("\S*\s*[M|G]bits/sec").findall(fmsg)
        # the last data of iperf is the ave data from 0-30 sec
        self.verify(len(iperfdata) != 0, "The iperf data between to vms is 0")
        self.logger.info("The iperf data between vms is %s" % iperfdata[-1])
        self.verify(
            (iperfdata[-1].split()[1]) == "Gbits/sec"
            and float(iperfdata[-1].split()[0]) >= 1,
            "the throughput must be above 1Gbits/sec",
        )
        # rm the iperf log file in vm
        self.vm_dut[0].send_expect("rm iperf_server.log", "#", 10)
        self.vm_dut[1].send_expect("rm iperf_client.log", "#", 10)
        return float(iperfdata[-1].split()[0])

    def check_scp_file_valid_between_vms(self, file_size=1024):
        """
        scp file form VM1 to VM2, check the data is valid
        """
        # default file_size=1024K
        data = ""
        for _ in range(file_size * 1024):
            data += random.choice(self.random_string)
        self.vm_dut[0].send_expect('echo "%s" > /tmp/payload' % data, "# ")
        # scp this file to vm1
        out = self.vm_dut[1].send_command(
            "scp root@%s:/tmp/payload /root" % self.virtio_ip0, timeout=5
        )
        if "Are you sure you want to continue connecting" in out:
            self.vm_dut[1].send_command("yes", timeout=3)
        self.vm_dut[1].send_command(self.vm[0].password, timeout=3)
        # get the file info in vm1, and check it valid
        md5_send = self.vm_dut[0].send_expect("md5sum /tmp/payload", "# ")
        md5_revd = self.vm_dut[1].send_expect("md5sum /root/payload", "# ")
        md5_send = md5_send[: md5_send.find(" ")]
        md5_revd = md5_revd[: md5_revd.find(" ")]
        self.verify(
            md5_send == md5_revd, "the received file is different with send file"
        )

    def start_iperf_and_scp_test_in_vms(
        self,
        moderns=["true", "true"],
        mrg_rxbuf=False,
        need_start_vm=True,
        packed=False,
        server_mode=False,
    ):
        if need_start_vm:
            self.start_vms(
                moderns=moderns,
                mrg_rxbuf=mrg_rxbuf,
                server_mode=server_mode,
                set_target=True,
                bind_dev=False,
            )
            self.vm0_pmd = PmdOutput(self.vm_dut[0])
            self.vm1_pmd = PmdOutput(self.vm_dut[1])
            self.config_vm_env()
        self.check_scp_file_valid_between_vms()
        self.start_iperf_test()
        iperfdata = self.get_iperf_result()
        return iperfdata

    def test_vm2vm_virtio_net_split_ring_test_with_dsa_dpdk_driver_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 4: VM2VM virtio-net split ring test with DSA dpdk driver and iperf stable check
        """
        perf_result = []
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        ports = dsas
        ports.append(self.dut.ports_info[0]["pci"])
        port_options = {dsas[0]: "max_queues=2"}
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports, port_options=port_options
        )
        dmas = "txd0@%s-q0,rxd0@%s-q1,txd1@%s-q0,rxd1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["true", "false"],
            mrg_rxbuf=False,
            need_start_vm=True,
            packed=False,
            server_mode=True,
        )
        perf_result.append(["split ring", "Before relaunch test", before_relaunch])

        self.vhost_user.send_expect("^C", "# ", 20)
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["split ring", "Before relaunch test", rerun_result])

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas = "txd0@%s-q0,rxd1@%s-q1" % (dsas[0], dsas[0])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        after_relaunch = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)

        perf_result.append(["split ring", "After relaunch test", after_relaunch])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_vm2vm_virtio_net_packed_ring_test_with_dsa_dpdk_driver_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 5: VM2VM virtio-net packed ring test with DSA dpdk driver and iperf stable check
        """
        perf_result = []
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        ports = dsas
        ports.append(self.dut.ports_info[0]["pci"])
        port_options = {dsas[0]: "max_queues=2"}
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports, port_options=port_options
        )
        dmas = "txd0@%s-q0,rxd0@%s-q1,txd1@%s-q0,rxd1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=False,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )
        perf_result.append(["packed ring", "Before relaunch test", before_relaunch])

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "Before relaunch test", rerun_result])

        self.stop_vms()
        after_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=True,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )

        perf_result.append(["packed ring", "After relaunch test", after_relaunch])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_vm2vm_virtio_net_packed_ring_test_with_2_dsa_wq_with_dpdk_driver_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 6: VM2VM virtio-net packed ring test with 2 DSA WQ with dpdk driver and iperf stable check
        """
        perf_result = []
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        ports = dsas
        ports.append(self.dut.ports_info[0]["pci"])
        port_options = {dsas[0]: "max_queues=2"}
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports, port_options=port_options
        )
        dmas = "txd0@%s-q0,rxd1@%s-q1" % (dsas[0], dsas[0])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=False,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )
        perf_result.append(["packed ring", "Before relaunch test", before_relaunch])

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "Before relaunch test", rerun_result])

        self.stop_vms()
        after_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=True,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )
        perf_result.append(["packed ring", "After relaunch test", after_relaunch])

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "After relaunch test", rerun_result])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_vm2vm_virtio_user_forwarding_test_using_dsa_kernel_driver(self):
        """
        Test Case 7: VM2VM virtio-user forwarding test when vhost async operation using DSA kernel driver
        """
        perf_result = []
        wqs = self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports
        )
        dmas = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (wqs[0], wqs[1], wqs[2], wqs[3])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
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
        before_relunch_result = self.vm2vm_check_with_two_dsa()

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas = "txd0@wq0.0,rxd1@wq0.1"
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )
        self.virtio_user0_pmd.execute_cmd("stop")
        after_relunch_result = self.vm2vm_check_with_two_dsa()

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

    def test_vm2vm_virtio_pmd_split_ring_test_with_dsa_kernle_driver_register_and_unregister_stable_check(
        self,
    ):
        """
        Test Case 8: VM2VM virtio-pmd split ring test with DSA kernel driver register/unregister stable check
        """
        perf_result = []
        wqs = self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports
        )
        dmas = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (wqs[0], wqs[1], wqs[2], wqs[3])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_rebind = self.start_vms_testpmd_and_test(
            moderns=["false", "true"], mrg_rxbuf=True, need_start_vm=True, packed=False
        )

        # repeat bind 50 time from virtio-pci to vfio-pci
        self.repeat_bind_driver(dut=self.vm_dut[0], repeat_times=50)
        self.repeat_bind_driver(dut=self.vm_dut[1], repeat_times=50)

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas = "txd0@%s,rxd1@%s" % (wqs[0], wqs[3])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        after_rebind = self.start_vms_testpmd_and_test(need_start_vm=False)

        for key in before_rebind.keys():
            perf_result.append([key, "Before rebind driver", before_rebind[key]])

        for key in after_rebind.keys():
            perf_result.append([key, "After rebind driver", after_rebind[key]])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        for i in perf_result:
            self.verify(i[2] > 0, "%s Frame Size(Byte) is less than 0 Mpps" % i[0])

    def test_vm2vm_virtio_pmd_packed_ring_test_with_dsa_kernel_driver_register_and_unregister_stable_check(
        self,
    ):
        """
        Test Case 9: VM2VM virtio-pmd packed ring test with DSA kernel driver register/unregister stable check
        """
        perf_result = []
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0, 1])
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports
        )
        dmas = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (wqs[0], wqs[1], wqs[2], wqs[3])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_rebind = self.start_vms_testpmd_and_test(
            moderns=["false", "false"], mrg_rxbuf=True, need_start_vm=True, packed=True
        )

        # repeat bind 50 time from virtio-pci to vfio-pci
        self.repeat_bind_driver(dut=self.vm_dut[0], repeat_times=50)
        self.repeat_bind_driver(dut=self.vm_dut[1], repeat_times=50)

        after_rebind = self.start_vms_testpmd_and_test(need_start_vm=False)

        for key in before_rebind.keys():
            perf_result.append([key, "Before rebind driver", before_rebind[key]])

        for key in after_rebind.keys():
            perf_result.append([key, "After rebind driver", after_rebind[key]])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        for i in perf_result:
            self.verify(i[2] > 0, "%s Frame Size(Byte) is less than 0 Mpps" % i[0])

    def test_vm2vm_virtio_net_split_ring_test_with_dsa_kernel_driver_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 10: VM2VM virtio-net split ring test with DSA kernel driver and iperf stable check
        """
        perf_result = []
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0, 1])
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports
        )
        dmas = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (wqs[0], wqs[1], wqs[2], wqs[3])
        self.launch_vhost_app(
            eal_params=eal_params,
            vdev_num=2,
            dmas=dmas,
            mergeable=False,
            tso=True,
            client_mode=True,
        )

        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["true", "false"],
            mrg_rxbuf=False,
            need_start_vm=True,
            packed=False,
            server_mode=True,
        )
        perf_result.append(["split ring", "Before relaunch test", before_relaunch])

        self.vhost_user.send_expect("^C", "# ", 20)
        self.launch_vhost_app(
            eal_params=eal_params,
            vdev_num=2,
            dmas=dmas,
            mergeable=False,
            tso=True,
            client_mode=True,
        )

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["split ring", "Before relaunch test", rerun_result])

        self.vhost_user.send_expect("^C", "# ", 20)
        dmas = "txd0@%s,rxd1@%s" % (wqs[0], wqs[1])
        self.launch_vhost_app(
            eal_params=eal_params,
            vdev_num=2,
            dmas=dmas,
            mergeable=False,
            tso=True,
            client_mode=True,
        )

        after_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["true", "false"],
            mrg_rxbuf=False,
            need_start_vm=False,
            packed=False,
            server_mode=True,
        )

        perf_result.append(["split ring", "After relaunch test", after_relaunch])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_vm2vm_virtio_net_packed_ring_test_with_dsa_kernel_driver_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 11: VM2VM virtio-net packed ring test with DSA kenrel driver and iperf stable check
        """
        perf_result = []
        wqs = self.DC.create_wq(wq_num=2, dsa_index=[0, 1])
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports
        )
        dmas = "txd0@%s,rxd0@%s,txd1@%s,rxd1@%s" % (wqs[0], wqs[1], wqs[2], wqs[3])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, tso=True, client_mode=True
        )

        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=False,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )
        perf_result.append(["packed ring", "Before relaunch test", before_relaunch])

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "Before relaunch test", rerun_result])

        self.stop_vms()
        after_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=True,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )

        perf_result.append(["packed ring", "After relaunch test", after_relaunch])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def test_vm2vm_virtio_net_packed_ring_test_with_2_dsa_wq_with_kernel_driver_and_iperf_stable_check(
        self,
    ):
        """
        Test Case 12: VM2VM virtio-net packed ring test with 2 DSA WQ with kernel driver and iperf stable check
        """
        perf_result = []
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        ports = [self.dut.ports_info[0]["pci"]]
        eal_params = self.dut.create_eal_parameters(
            cores=self.vhost_core_list, ports=ports
        )
        dmas = "txd0@%s,rxd1@%s" % (wqs[0], wqs[1])
        self.launch_vhost_app(
            eal_params=eal_params, vdev_num=2, dmas=dmas, client_mode=True
        )

        before_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=False,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )
        perf_result.append(["packed ring", "Before relaunch test", before_relaunch])

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "Before relaunch test", rerun_result])

        self.stop_vms()
        after_relaunch = self.start_iperf_and_scp_test_in_vms(
            moderns=["false", "false"],
            mrg_rxbuf=True,
            need_start_vm=True,
            packed=True,
            server_mode=True,
        )
        perf_result.append(["packed ring", "After relaunch test", after_relaunch])

        for _ in range(self.rerun_times):
            rerun_result = self.start_iperf_and_scp_test_in_vms(need_start_vm=False)
            perf_result.append(["packed ring", "After relaunch test", rerun_result])

        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def stop_vms(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vm_dut = []
        self.vm = []

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
        self.stop_vms()
        self.vhost_user.send_expect("^C", "# ", 20)
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_all_session()

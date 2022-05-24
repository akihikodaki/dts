# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.

vm2vm split ring and packed ring with tx offload (TSO and UFO) with non-mergeable path.
vm2vm split ring and packed ring with UFO about virtio-net device capability with non-mergeable path.
vm2vm split ring and packed ring vhost-user/virtio-net check the payload of large packet is valid with
mergeable and non-mergeable dequeue zero copy.
please use qemu version greater 4.1.94 which support packed feathur to test this suite.
"""
import random
import re
import string
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM


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

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_dut = []
        self.vm = []

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num, allow_diff_socket=False):
        """
        get and bind cbdma ports into DPDK driver
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

    @staticmethod
    def generate_dms_param(queues):
        das_list = []
        for i in range(queues):
            das_list.append("txq{}".format(i))
        das_param = "[{}]".format(";".join(das_list))
        return das_param

    @staticmethod
    def generate_lcore_dma_param(cbdma_list, core_list):
        group_num = int(len(cbdma_list) / len(core_list))
        lcore_dma_list = []
        if len(cbdma_list) == 1:
            for core in core_list:
                lcore_dma_list.append("lcore{}@{}".format(core, cbdma_list[0]))
        elif len(core_list) == 1:
            for cbdma in cbdma_list:
                lcore_dma_list.append("lcore{}@{}".format(core_list[0], cbdma))
        else:
            for cbdma in cbdma_list:
                core_list_index = int(cbdma_list.index(cbdma) / group_num)
                lcore_dma_list.append(
                    "lcore{}@{}".format(core_list[core_list_index], cbdma)
                )
        lcore_dma_param = "[{}]".format(",".join(lcore_dma_list))
        return lcore_dma_param

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

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

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

    def config_vm_ip(self):
        """
        set virtio device IP and run arp protocal
        """
        vm1_intf = self.vm_dut[0].ports_info[0]["intf"]
        vm2_intf = self.vm_dut[1].ports_info[0]["intf"]
        self.vm_dut[0].send_expect(
            "ifconfig %s %s" % (vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm_dut[1].send_expect(
            "ifconfig %s %s" % (vm2_intf, self.virtio_ip2), "#", 10
        )
        self.vm_dut[0].send_expect(
            "arp -s %s %s" % (self.virtio_ip2, self.virtio_mac2), "#", 10
        )
        self.vm_dut[1].send_expect(
            "arp -s %s %s" % (self.virtio_ip1, self.virtio_mac1), "#", 10
        )

    def config_vm_combined(self, combined=1):
        """
        set virtio device combined
        """
        vm1_intf = self.vm_dut[0].ports_info[0]["intf"]
        vm2_intf = self.vm_dut[1].ports_info[0]["intf"]
        self.vm_dut[0].send_expect(
            "ethtool -L %s combined %d" % (vm1_intf, combined), "#", 10
        )
        self.vm_dut[1].send_expect(
            "ethtool -L %s combined %d" % (vm2_intf, combined), "#", 10
        )

    def check_ping_between_vms(self):
        ping_out = self.vm_dut[0].send_expect(
            "ping {} -c 4".format(self.virtio_ip2), "#", 20
        )
        self.logger.info(ping_out)

    def start_iperf(self):
        """
        run perf command between to vms
        """
        self.vhost.send_expect("clear port xstats all", "testpmd> ", 10)

        server = "iperf -s -i 1"
        client = "iperf -c {} -i 1 -t 60".format(self.virtio_ip1)
        self.vm_dut[0].send_expect("{} > iperf_server.log &".format(server), "", 10)
        self.vm_dut[1].send_expect("{} > iperf_client.log &".format(client), "", 10)
        time.sleep(60)

    def get_perf_result(self):
        """
        get the iperf test result
        """
        self.table_header = ["Mode", "[M|G]bits/sec"]
        self.result_table_create(self.table_header)
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

        # put the result to table
        results_row = ["vm2vm", iperfdata[-1]]
        self.result_table_add(results_row)

        # print iperf resut
        self.result_table_print()
        # rm the iperf log file in vm
        self.vm_dut[0].send_expect("rm iperf_server.log", "#", 10)
        self.vm_dut[1].send_expect("rm iperf_client.log", "#", 10)

    def verify_xstats_info_on_vhost(self):
        """
        check both 2VMs can receive and send big packets to each other
        """
        self.vhost.send_expect("show port stats all", "testpmd> ", 20)
        out_tx = self.vhost.send_expect("show port xstats 0", "testpmd> ", 20)
        out_rx = self.vhost.send_expect("show port xstats 1", "testpmd> ", 20)

        tx_info = re.search("tx_size_1523_to_max_packets:\s*(\d*)", out_tx)
        rx_info = re.search("rx_size_1523_to_max_packets:\s*(\d*)", out_rx)

        self.verify(
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1522"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1522"
        )

    def offload_capbility_check(self, vm_client):
        """
        check UFO and TSO offload status on for the Virtio-net driver in VM
        """
        vm_intf = vm_client.ports_info[0]["intf"]
        vm_client.send_expect("ethtool -k %s > offload.log" % vm_intf, "#", 10)
        fmsg = vm_client.send_expect("cat ./offload.log", "#")
        udp_info = re.search("udp-fragmentation-offload:\s*(\S*)", fmsg)
        tcp_info = re.search("tx-tcp-segmentation:\s*(\S*)", fmsg)
        tcp_enc_info = re.search("tx-tcp-ecn-segmentation:\s*(\S*)", fmsg)
        tcp6_info = re.search("tx-tcp6-segmentation:\s*(\S*)", fmsg)

        self.verify(
            udp_info is not None and udp_info.group(1) == "on",
            "the udp-fragmentation-offload in vm not right",
        )
        self.verify(
            tcp_info is not None and tcp_info.group(1) == "on",
            "tx-tcp-segmentation in vm not right",
        )
        self.verify(
            tcp_enc_info is not None and tcp_enc_info.group(1) == "on",
            "tx-tcp-ecn-segmentation in vm not right",
        )
        self.verify(
            tcp6_info is not None and tcp6_info.group(1) == "on",
            "tx-tcp6-segmentation in vm not right",
        )

    def check_scp_file_valid_between_vms(self, file_size=1024):
        """
        scp file form VM1 to VM2, check the data is valid
        """
        # default file_size=1024K
        data = ""
        for char in range(file_size * 1024):
            data += random.choice(self.random_string)
        self.vm_dut[0].send_expect('echo "%s" > /tmp/payload' % data, "# ")
        # scp this file to vm1
        out = self.vm_dut[1].send_command(
            "scp root@%s:/tmp/payload /root" % self.virtio_ip1, timeout=5
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

    def test_vm2vm_split_ring_iperf_with_tso_and_cbdma_enable(self):
        """
        Test Case 1: VM2VM split ring vhost-user/virtio-net CBDMA enable test with tcp traffic
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        dmas = self.generate_dms_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:3]
        )
        eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        param = (
            " --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_vm2vm_split_ring_with_mergeable_path_8queue_check_large_packet_and_cbdma_enable(
        self,
    ):
        """
        Test Case 2: VM2VM split ring vhost-user/virtio-net mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
        dmas = self.generate_dms_param(8)
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        cbdma1 = self.cbdma_list[0]
        cbdma2 = self.cbdma_list[1]
        cbdma3 = self.cbdma_list[2]
        cbdma4 = self.cbdma_list[3]
        cbdma5 = self.cbdma_list[4]
        cbdma6 = self.cbdma_list[5]
        cbdma7 = self.cbdma_list[6]
        cbdma8 = self.cbdma_list[7]
        cbdma9 = self.cbdma_list[8]
        cbdma10 = self.cbdma_list[9]
        cbdma11 = self.cbdma_list[10]
        cbdma12 = self.cbdma_list[11]
        cbdma13 = self.cbdma_list[12]
        cbdma14 = self.cbdma_list[13]
        cbdma15 = self.cbdma_list[14]
        cbdma16 = self.cbdma_list[15]
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma2},lcore{core1}@{cbdma3},"
            f"lcore{core1}@{cbdma4},lcore{core1}@{cbdma5},lcore{core1}@{cbdma6},"
            f"lcore{core2}@{cbdma7},lcore{core2}@{cbdma8},"
            f"lcore{core3}@{cbdma9},lcore{core3}@{cbdma10},lcore{core3}@{cbdma11},lcore{core3}@{cbdma12},"
            f"lcore{core3}@{cbdma13},lcore{core3}@{cbdma14},lcore{core3}@{cbdma15},"
            f"lcore{core4}@{cbdma16}]"
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas={}'".format(
                dmas
            )
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas={}'".format(
                dmas
            )
        )
        param = (
            " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        self.logger.info("Quit and relaunch vhost w/ diff CBDMA channels")
        self.pmdout_vhost_user.execute_cmd("quit", "#")
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma2},"
            f"lcore{core1}@{cbdma3},lcore{core1}@{cbdma4},"
            f"lcore{core2}@{cbdma1},lcore{core2}@{cbdma3},lcore{core2}@{cbdma5},"
            f"lcore{core2}@{cbdma6},lcore{core2}@{cbdma7},lcore{core2}@{cbdma8},"
            f"lcore{core3}@{cbdma2},lcore{core3}@{cbdma4},lcore{core3}@{cbdma9},"
            f"lcore{core3}@{cbdma10},lcore{core3}@{cbdma11},lcore{core3}@{cbdma12},"
            f"lcore{core3}@{cbdma13},lcore{core3}@{cbdma14},lcore{core3}@{cbdma15},"
            f"lcore{core4}@{cbdma16}]"
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]'"
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6;txq7]'"
        )
        param = (
            " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost w/ iova=pa")
            eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]'"
                + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]'"
            )
            param = (
                " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
                + " --lcore-dma={}".format(lcore_dma)
            )
            self.pmdout_vhost_user.execute_cmd("quit", "#")
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                ports=self.cbdma_list,
                eal_param=eal_param,
                param=param,
                iova_mode="pa",
            )
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

        self.logger.info("Quit and relaunch vhost w/o CBDMA channels")
        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4'"
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=4 --rxq=4"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
        )
        self.config_vm_combined(combined=4)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        self.logger.info("Quit and relaunch vhost w/o CBDMA channels with 1 queue")
        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4'"
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
        )
        self.config_vm_combined(combined=1)
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_vm2vm_split_ring_with_non_mergeable_path_8queue_check_large_packet_and_cbdma_enable(
        self,
    ):
        """
        Test Case 3: VM2VM split ring vhost-user/virtio-net non-mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
        dmas = self.generate_dms_param(8)
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        cbdma1 = self.cbdma_list[0]
        cbdma2 = self.cbdma_list[1]
        cbdma3 = self.cbdma_list[2]
        cbdma4 = self.cbdma_list[3]
        cbdma5 = self.cbdma_list[4]
        cbdma6 = self.cbdma_list[5]
        cbdma7 = self.cbdma_list[6]
        cbdma8 = self.cbdma_list[7]
        cbdma9 = self.cbdma_list[8]
        cbdma10 = self.cbdma_list[9]
        cbdma11 = self.cbdma_list[10]
        cbdma12 = self.cbdma_list[11]
        cbdma13 = self.cbdma_list[12]
        cbdma14 = self.cbdma_list[13]
        cbdma15 = self.cbdma_list[14]
        cbdma16 = self.cbdma_list[15]
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma2},lcore{core1}@{cbdma3},"
            f"lcore{core1}@{cbdma4},lcore{core1}@{cbdma5},lcore{core1}@{cbdma6},"
            f"lcore{core2}@{cbdma7},lcore{core2}@{cbdma8},"
            f"lcore{core3}@{cbdma9},lcore{core3}@{cbdma10},lcore{core3}@{cbdma11},lcore{core3}@{cbdma12},"
            f"lcore{core3}@{cbdma13},lcore{core3}@{cbdma14},lcore{core3}@{cbdma15},"
            f"lcore{core4}@{cbdma16}]"
        )

        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas={}'".format(
                dmas
            )
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas={}'".format(
                dmas
            )
        )
        param = (
            " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        self.logger.info("Quit and relaunch vhost w/ diff CBDMA channels")
        self.pmdout_vhost_user.execute_cmd("quit", "#")
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma2},"
            f"lcore{core1}@{cbdma3},lcore{core1}@{cbdma4},"
            f"lcore{core2}@{cbdma1},lcore{core2}@{cbdma3},lcore{core2}@{cbdma5},"
            f"lcore{core2}@{cbdma6},lcore{core2}@{cbdma7},lcore{core2}@{cbdma8},"
            f"lcore{core3}@{cbdma2},lcore{core3}@{cbdma4},lcore{core3}@{cbdma9},"
            f"lcore{core3}@{cbdma10},lcore{core3}@{cbdma11},lcore{core3}@{cbdma12},"
            f"lcore{core3}@{cbdma13},lcore{core3}@{cbdma14},lcore{core3}@{cbdma15},"
            f"lcore{core4}@{cbdma16}]"
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]'"
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,dmas=[txq1;txq2;txq3;txq4;txq5;txq6]'"
        )
        param = (
            " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.check_scp_file_valid_between_vms()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()

        self.logger.info("Quit and relaunch vhost w/o CBDMA channels")
        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8'"
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.config_vm_combined(combined=4)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        self.logger.info("Quit and relaunch vhost w/o CBDMA channels with 1 queue")
        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8'"
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
        )
        self.config_vm_combined(combined=1)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_vm2vm_split_ring_with_mergeable_path_16queue_check_large_packet_and_cbdma_enable(
        self,
    ):
        """
        Test Case 4: VM2VM split ring vhost-user/virtio-net mergeable 16 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
        dmas = self.generate_dms_param(16)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:9]
        )
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,dmas={}'".format(
                dmas
            )
            + " --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,dmas={}'".format(
                dmas
            )
        )
        param = (
            " --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=16)
        self.config_vm_ip()
        self.config_vm_combined(combined=16)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_vm2vm_packed_ring_iperf_with_tso_and_cbdma_enable(self):
        """
        Test Case 5: VM2VM packed ring vhost-user/virtio-net CBDMA enable test with tcp traffic
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        dmas = self.generate_dms_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:3]
        )
        eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas={}'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas={}'".format(dmas)
        param = (
            " --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_vm2vm_packed_ring_with_mergeable_path_8queue_check_large_packet_and_cbdma_enable(
        self,
    ):
        """
        Test Case 6: VM2VM virtio-net packed ring mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(16, allow_diff_socket=True)
        dmas = self.generate_dms_param(7)
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        cbdma1 = self.cbdma_list[0]
        cbdma2 = self.cbdma_list[1]
        cbdma3 = self.cbdma_list[2]
        cbdma4 = self.cbdma_list[3]
        cbdma5 = self.cbdma_list[4]
        cbdma6 = self.cbdma_list[5]
        cbdma7 = self.cbdma_list[6]
        cbdma8 = self.cbdma_list[7]
        cbdma9 = self.cbdma_list[8]
        cbdma10 = self.cbdma_list[9]
        cbdma11 = self.cbdma_list[10]
        cbdma12 = self.cbdma_list[11]
        cbdma13 = self.cbdma_list[12]
        cbdma14 = self.cbdma_list[13]
        cbdma15 = self.cbdma_list[14]
        cbdma16 = self.cbdma_list[15]
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma2},lcore{core1}@{cbdma3},lcore{core1}@{cbdma4},"
            f"lcore{core2}@{cbdma1},lcore{core2}@{cbdma3},lcore{core2}@{cbdma5},lcore{core2}@{cbdma6},lcore{core2}@{cbdma7},lcore{core2}@{cbdma8},"
            f"lcore{core3}@{cbdma2},lcore{core3}@{cbdma4},lcore{core3}@{cbdma9},lcore{core3}@{cbdma10},lcore{core3}@{cbdma11},lcore{core3}@{cbdma12},lcore{core3}@{cbdma13},lcore{core3}@{cbdma14},lcore{core3}@{cbdma15},"
            f"lcore{core4}@{cbdma16}]"
        )
        eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas={}'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas={}'".format(dmas)
        param = (
            " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        # self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.config_vm_combined(combined=8)
        for _ in range(6):
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

    def test_vm2vm_packed_ring_with_non_mergeable_path_8queue_check_large_packet_and_cbdma_enable(
        self,
    ):
        """
        Test Case 7: VM2VM virtio-net packed ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(16, allow_diff_socket=True)
        dmas = self.generate_dms_param(8)
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        cbdma1 = self.cbdma_list[0]
        cbdma2 = self.cbdma_list[1]
        cbdma3 = self.cbdma_list[2]
        cbdma4 = self.cbdma_list[3]
        cbdma5 = self.cbdma_list[4]
        cbdma6 = self.cbdma_list[5]
        cbdma7 = self.cbdma_list[6]
        cbdma8 = self.cbdma_list[7]
        cbdma9 = self.cbdma_list[8]
        cbdma10 = self.cbdma_list[9]
        cbdma11 = self.cbdma_list[10]
        cbdma12 = self.cbdma_list[11]
        cbdma13 = self.cbdma_list[12]
        cbdma14 = self.cbdma_list[13]
        cbdma15 = self.cbdma_list[14]
        cbdma16 = self.cbdma_list[15]
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma2},lcore{core1}@{cbdma3},"
            f"lcore{core1}@{cbdma4},lcore{core1}@{cbdma5},lcore{core1}@{cbdma6},"
            f"lcore{core2}@{cbdma7},lcore{core2}@{cbdma8},"
            f"lcore{core3}@{cbdma9},lcore{core3}@{cbdma10},lcore{core3}@{cbdma11},lcore{core3}@{cbdma12},"
            f"lcore{core3}@{cbdma13},lcore{core3}@{cbdma14},lcore{core3}@{cbdma15},"
            f"lcore{core4}@{cbdma16}]"
        )
        eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas={}'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas={}'".format(dmas)
        param = (
            " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        for _ in range(6):
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

    def test_vm2vm_packed_ring_with_mergeable_path_16queue_check_large_packet_and_cbdma_enable(
        self,
    ):
        """
        Test Case 8: VM2VM virtio-net packed ring mergeable 16 queues CBDMA enabled test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(16, allow_diff_socket=True)
        dmas = self.generate_dms_param(16)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:9]
        )
        eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=16,dmas={}'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=16,dmas={}'".format(dmas)
        param = (
            " --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=16)
        self.config_vm_ip()
        self.config_vm_combined(combined=16)
        self.check_ping_between_vms()
        for _ in range(6):
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

    def test_vm2vm_packed_ring_iperf_with_tso_when_set_ivoa_pa_and_cbdma_enable(self):
        """
        Test Case 9: VM2VM packed ring vhost-user/virtio-net CBDMA enable test with tcp traffic when set iova=pa
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        dmas = self.generate_dms_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:3]
        )
        eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas={}'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,dmas={}'".format(dmas)
        param = (
            " --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="pa",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_vm2vm_packed_ring_with_mergeable_path_8queue_check_large_packet_when_set_ivoa_pa_and_cbdma_enable(
        self,
    ):
        """
        Test Case 10: VM2VM virtio-net packed ring mergeable 8 queues CBDMA enable and PA mode test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
        dmas = self.generate_dms_param(7)
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        cbdma1 = self.cbdma_list[0]
        cbdma2 = self.cbdma_list[1]
        cbdma3 = self.cbdma_list[2]
        cbdma4 = self.cbdma_list[3]
        cbdma5 = self.cbdma_list[4]
        cbdma6 = self.cbdma_list[5]
        cbdma7 = self.cbdma_list[6]
        cbdma8 = self.cbdma_list[7]
        cbdma9 = self.cbdma_list[8]
        cbdma10 = self.cbdma_list[9]
        cbdma11 = self.cbdma_list[10]
        cbdma12 = self.cbdma_list[11]
        cbdma13 = self.cbdma_list[12]
        cbdma14 = self.cbdma_list[13]
        cbdma15 = self.cbdma_list[14]
        cbdma16 = self.cbdma_list[15]
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma2},lcore{core1}@{cbdma3},"
            f"lcore{core1}@{cbdma4},lcore{core1}@{cbdma5},lcore{core1}@{cbdma6},"
            f"lcore{core2}@{cbdma7},lcore{core2}@{cbdma8},"
            f"lcore{core3}@{cbdma9},lcore{core3}@{cbdma10},lcore{core3}@{cbdma11},lcore{core3}@{cbdma12},"
            f"lcore{core3}@{cbdma13},lcore{core3}@{cbdma14},lcore{core3}@{cbdma15},"
            f"lcore{core4}@{cbdma16}]"
        )
        eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas={}'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas={}'".format(dmas)
        param = (
            " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="pa",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_ip()
        self.check_ping_between_vms()
        for _ in range(1):
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

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
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost)

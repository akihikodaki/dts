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

    def bind_cbdma_device_to_kernel(self):
        if self.cbdma_str:
            self.dut.send_expect("modprobe ioatdma", "# ")
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py -u %s" % self.cbdma_str, "# ", 30
            )
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py --force --bind=ioatdma  %s"
                % self.cbdma_str,
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

        tx_info = re.search("tx_q0_size_1519_max_packets:\s*(\d*)", out_tx)
        rx_info = re.search("rx_q0_size_1519_max_packets:\s*(\d*)", out_rx)

        self.verify(
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1518"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1518"
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
            "scp root@%s:/tmp/payload /root" % self.virtio_ip1, timeout=10
        )
        if "Are you sure you want to continue connecting" in out:
            self.vm_dut[1].send_command("yes", timeout=10)
        self.vm_dut[1].send_command(self.vm[0].password, timeout=10)
        # get the file info in vm1, and check it valid
        md5_send = self.vm_dut[0].send_expect("md5sum /tmp/payload", "# ")
        md5_revd = self.vm_dut[1].send_expect("md5sum /root/payload", "# ")
        md5_send = md5_send[: md5_send.find(" ")]
        md5_revd = md5_revd[: md5_revd.find(" ")]
        self.verify(
            md5_send == md5_revd, "the received file is different with send file"
        )

    def test_vm2vm_virtio_net_split_ring_cbdma_enable_test_with_tcp_traffic(self):
        """
        Test Case 1: VM2VM virtio-net split ring CBDMA enable test with tcp traffic
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)

        dmas1 = "txq0@%s;rxq0@%s" % (self.cbdma_list[0], self.cbdma_list[0])
        dmas2 = "txq0@%s;rxq0@%s" % (self.cbdma_list[1], self.cbdma_list[1])
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=2 --txd=1024 --rxd=1024 --rxq=1 --txq=1"

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

    def test_vm2vm_virtio_net_split_ring_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 2: VM2VM virtio-net split ring mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[7],
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
            ports=self.cbdma_list[0:8],
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
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
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
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
            ports=self.cbdma_list[0:2],
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        if not self.check_2M_env:
            dmas1 = (
                "txq0@%s;"
                "txq1@%s;"
                "txq2@%s;"
                "txq3@%s;"
                "txq4@%s;"
                "txq5@%s;"
                "txq6@%s"
                % (
                    self.cbdma_list[0],
                    self.cbdma_list[1],
                    self.cbdma_list[0],
                    self.cbdma_list[1],
                    self.cbdma_list[0],
                    self.cbdma_list[1],
                    self.cbdma_list[2],
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
                    self.cbdma_list[2],
                    self.cbdma_list[3],
                    self.cbdma_list[2],
                    self.cbdma_list[3],
                    self.cbdma_list[2],
                    self.cbdma_list[3],
                    self.cbdma_list[4],
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
                ports=self.cbdma_list[0:8],
                eal_param=eal_param,
                param=param,
                iova_mode="pa",
            )
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
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

        self.pmdout_vhost_user.execute_cmd("quit", "#")

        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=4,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=4,tso=1'"
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

    def test_vm2vm_virtio_net_split_ring_with_non_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 3: VM2VM virtio-net split ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
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
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[0],
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
                self.cbdma_list[8],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[13],
                self.cbdma_list[14],
                self.cbdma_list[15],
                self.cbdma_list[8],
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
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,tso=1,queues=8,dmas=[%s],dma-ring-size=1024' "
            "--vdev 'net_vhost1,iface=vhost-net1,client=1,tso=1,queues=8,dmas=[%s],dma-ring-size=1024'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
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

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
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
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
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
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        for _ in range(5):
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
        )
        param = " --nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        self.pmdout_vhost_user.execute_cmd("quit", "#")
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=8,tso=1' "
            + "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=8,tso=1'"
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

    def test_vm2vm_virtio_net_split_ring_mergeable_16_queues_cbdma_enable_test_with_Rx_Tx_csum_in_SW(
        self,
    ):
        """
        Test Case 4: VM2VM virtio-net split ring mergeable 16 queues CBDMA enable test with Rx/Tx csum in SW
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[7],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
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
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[8],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[13],
                self.cbdma_list[14],
                self.cbdma_list[15],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[8],
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
            "--vdev 'net_vhost0,iface=vhost-net0,client=1,queues=16,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,client=1,queues=16,tso=1,dmas=[%s]'"
        ) % (dmas1, dmas2)

        param = " --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
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
        self.config_vm_ip()
        self.config_vm_combined(combined=16)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_vm2vm_virtio_net_packed_ring_cbdma_enable_test_with_tcp_traffic(self):
        """
        Test Case 5: VM2VM virtio-net packed ring CBDMA enable test with tcp traffic
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
        dmas1 = "txq0@%s;rxq0@%s" % (self.cbdma_list[0], self.cbdma_list[0])
        dmas2 = "txq0@%s;rxq0@%s" % (self.cbdma_list[1], self.cbdma_list[1])
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'"
        ) % (dmas1, dmas2)
        param = " --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
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

    def test_vm2vm_virtio_net_packed_ring_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 6: VM2VM virtio-net packed ring mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[7],
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
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()
        for _ in range(5):
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

    def test_vm2vm_virtio_net_packed_ring_non_mergeable_8_queues_cbdma_enable_test_with_large_packet_payload_valid_check(
        self,
    ):
        """
        Test Case 7: VM2VM virtio-net packed ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
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
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
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
                self.cbdma_list[8],
                self.cbdma_list[8],
                self.cbdma_list[9],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[12],
                self.cbdma_list[13],
                self.cbdma_list[13],
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
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()
        for _ in range(5):
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

    def test_vm2vm_virtio_net_packed_ring_mergeable_16_queues_cbdma_enable_test_with_Rx_Tx_csum_in_SW(
        self,
    ):
        """
        Test Case 8: VM2VM virtio-net packed ring mergeable 16 queues CBDMA enabled test with Rx/Tx csum in SW
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[7],
                self.cbdma_list[8],
                self.cbdma_list[8],
                self.cbdma_list[9],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[12],
                self.cbdma_list[13],
                self.cbdma_list[13],
                self.cbdma_list[14],
                self.cbdma_list[14],
                self.cbdma_list[15],
                self.cbdma_list[15],
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
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[8],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[13],
                self.cbdma_list[14],
                self.cbdma_list[15],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[8],
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
            "--vdev 'net_vhost0,iface=vhost-net0,queues=16,tso=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=16,tso=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=8 --txd=1024 --rxd=1024 --txq=16 --rxq=16"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            ports=self.cbdma_list,
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
        self.config_vm_ip()
        self.config_vm_combined(combined=16)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()
        for _ in range(5):
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

    def test_vm2vm_virtio_net_packed_ring_cbdma_enable_test_dma_ring_size_with_tcp_traffic(
        self,
    ):
        """
        Test Case 9: VM2VM virtio-net packed ring CBDMA enable test dma-ring-size with tcp traffic
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        dmas1 = "txq0@%s;rxq0@%s" % (self.cbdma_list[0], self.cbdma_list[0])
        dmas2 = "txq0@%s;rxq0@%s" % (self.cbdma_list[1], self.cbdma_list[1])
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s],dma-ring-size=256' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s],dma-ring-size=256'"
            % (dmas1, dmas2)
        )
        param = " --nb-cores=2 --txd=1024 --rxd=1024 --txq=1 --rxq=1"
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
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()
        for _ in range(5):
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

    def test_vm2vm_virtio_net_packed_ring_8_queues_cbdma_enable_test_with_legacy_mode(
        self,
    ):
        """
        Test Case 10: VM2VM virtio-net packed ring 8 queues CBDMA enable test with legacy mode
        """
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
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
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
                self.cbdma_list[8],
                self.cbdma_list[8],
                self.cbdma_list[9],
                self.cbdma_list[9],
                self.cbdma_list[10],
                self.cbdma_list[10],
                self.cbdma_list[11],
                self.cbdma_list[11],
                self.cbdma_list[12],
                self.cbdma_list[12],
                self.cbdma_list[13],
                self.cbdma_list[13],
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
            ports=self.cbdma_list,
            eal_param=eal_param,
            param=param,
            iova_mode="va",
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()
        for _ in range(5):
            self.check_ping_between_vms()
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

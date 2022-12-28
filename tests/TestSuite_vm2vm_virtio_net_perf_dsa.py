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

from .virtio_common import dsa_common as DC


class TestVM2VMVirtioNetPerfDsa(TestCase):
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
        self.vhost_user = self.dut.new_session(suite="vhost")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.DC = DC(self)

    def set_up(self):
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.vm_dut = []
        self.vm = []
        self.use_dsa_list = []
        self.DC.reset_all_work_queue()
        self.DC.bind_all_dsa_to_kernel()

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
        self.vhost_user_pmd.execute_cmd("clear port xstats all")

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

    def test_split_tso_with_dpdk_driver(self):
        """
        Test Case 1: VM2VM vhost-user/virtio-net split ring test TSO with dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q0" % (self.use_dsa_list[0], self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=2"}
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
            ports=self.use_dsa_list,
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_split_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 2: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
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
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
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
            ports=self.use_dsa_list[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.config_vm_combined(combined=8)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
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
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,client=1,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,client=1,queues=8,tso=1,legacy-ol-flags=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            self.use_dsa_list[0]: "max_queues=8",
            self.use_dsa_list[1]: "max_queues=8",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.use_dsa_list,
            port_options=port_options,
        )
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        if not self.check_2M_env:
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.use_dsa_list,
                port_options=port_options,
                iova_mode="pa",
            )
            self.check_ping_between_vms()
            self.check_scp_file_valid_between_vms()
            self.start_iperf()
            self.get_perf_result()

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
        self.config_vm_combined(combined=4)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.config_vm_combined(combined=1)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_split_non_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 3: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
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
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        port_options = {self.use_dsa_list[0]: "max_queues=8"}
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
            ports=self.use_dsa_list[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vms(server_mode=True, vm_queue=8)
        self.config_vm_combined(combined=8)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.config_vm_combined(combined=4)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.config_vm_combined(combined=1)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_packed_tso_with_dpdk_driver(self):
        """
        Test Case 4: VM2VM vhost-user/virtio-net packed ring test TSO with dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = "txq0@%s-q0;rxq0@%s-q1" % (self.use_dsa_list[0], self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=2"}
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
            ports=self.use_dsa_list[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_packed_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 5: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
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
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
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
            ports=self.use_dsa_list[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_combined(combined=8)
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

    def test_packed_non_mergeable_8_queues_large_packet_paylocad_with_dpdk_driver(self):
        """
        Test Case 6: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2, driver_name="vfio-pci", socket=self.ports_socket
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
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
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
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
            )
        )
        port_options = {
            self.use_dsa_list[0]: "max_queues=8",
            self.use_dsa_list[1]: "max_queues=8",
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
            ports=self.use_dsa_list,
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=off,guest_tso4=off,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_combined(combined=8)
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

    def test_packed_dma_ring_size_with_tcp_and_dpdk_driver(self):
        """
        Test Case 7: VM2VM vhost-user/virtio-net packed ring test dma-ring-size with tcp traffic and dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s-q0;rxq0@%s-q0" % (self.use_dsa_list[0], self.use_dsa_list[0])
        dmas2 = "txq0@%s-q1;rxq0@%s-q1" % (self.use_dsa_list[0], self.use_dsa_list[0])
        port_options = {self.use_dsa_list[0]: "max_queues=2"}
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
            ports=self.use_dsa_list[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=1)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_packed_mergeable_8_queues_with_legacy_mode_and_dpdk_driver(self):
        """
        Test Case 8: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with legacy mode with dsa dpdk driver
        """
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=1, driver_name="vfio-pci", socket=self.ports_socket
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
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        port_options = {self.use_dsa_list[0]: "max_queues=4"}
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
            ports=self.use_dsa_list[0:1],
            port_options=port_options,
        )
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vms(server_mode=False, vm_queue=8)
        self.config_vm_combined(combined=8)
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

    def test_split_tso_with_kernel_driver(self):
        """
        Test Case 9: VM2VM vhost-user/virtio-net split ring test TSO with dsa kernel driver
        """
        self.DC.create_work_queue(work_queue_number=1, dsa_index=0)
        dmas = "txq0@wq0.0;rxq0@wq0.0"
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
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_split_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(self):
        """
        Test Case 10: VM2VM vhost-user/virtio-net split ring mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "txq4@wq0.4;"
            "txq5@wq0.5;"
            "txq6@wq0.6;"
            "txq7@wq0.7;"
            "rxq0@wq0.0;"
            "rxq1@wq0.1;"
            "rxq2@wq0.2;"
            "rxq3@wq0.3;"
            "rxq4@wq0.4;"
            "rxq5@wq0.5;"
            "rxq6@wq0.6;"
            "rxq7@wq0.7"
        )
        dmas2 = (
            "txq0@wq1.0;"
            "txq1@wq1.1;"
            "txq2@wq1.2;"
            "txq3@wq1.3;"
            "txq4@wq1.4;"
            "txq5@wq1.5;"
            "txq6@wq1.6;"
            "txq7@wq1.7;"
            "rxq0@wq1.0;"
            "rxq1@wq1.1;"
            "rxq2@wq1.2;"
            "rxq3@wq1.3;"
            "rxq4@wq1.4;"
            "rxq5@wq1.5;"
            "rxq6@wq1.6;"
            "rxq7@wq1.7"
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
        self.config_vm_combined(combined=8)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

        self.vhost_user_pmd.quit()
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "rxq2@wq0.1;"
            "rxq3@wq0.1;"
            "rxq4@wq0.2;"
            "rxq5@wq0.2;"
            "rxq6@wq0.2;"
            "rxq7@wq0.2"
        )
        dmas2 = (
            "txq0@wq0.3;"
            "txq1@wq0.3;"
            "txq2@wq0.3;"
            "txq3@wq0.3;"
            "txq4@wq0.4;"
            "txq5@wq0.4;"
            "rxq2@wq0.4;"
            "rxq3@wq0.4;"
            "rxq4@wq0.5;"
            "rxq5@wq0.5;"
            "rxq6@wq0.5;"
            "rxq7@wq0.5"
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
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.config_vm_combined(combined=4)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.config_vm_combined(combined=1)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_split_non_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(
        self,
    ):
        """
        Test Case 11: VM2VM vhost-user/virtio-net split ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "rxq2@wq0.1;"
            "rxq3@wq0.1;"
            "rxq4@wq0.2;"
            "rxq5@wq0.2;"
            "rxq6@wq0.2;"
            "rxq7@wq0.2"
        )
        dmas2 = (
            "txq0@wq1.0;"
            "txq1@wq1.0;"
            "txq2@wq1.0;"
            "txq3@wq1.0;"
            "txq4@wq1.1;"
            "txq5@wq1.1;"
            "rxq2@wq1.1;"
            "rxq3@wq1.1;"
            "rxq4@wq1.2;"
            "rxq5@wq1.2;"
            "rxq6@wq1.2;"
            "rxq7@wq1.2"
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
        self.config_vm_combined(combined=8)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.config_vm_combined(combined=1)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_packed_tso_with_kernel_driver(self):
        """
        Test Case 12: VM2VM vhost-user/virtio-net packed ring test TSO with dsa kernel driver
        """
        self.DC.create_work_queue(work_queue_number=1, dsa_index=0)
        dmas = "txq0@wq0.0;rxq0@wq0.0"
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
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()

    def test_packed_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(self):
        """
        Test Case 13: VM2VM vhost-user/virtio-net packed ring mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "txq4@wq0.4;"
            "txq5@wq0.5;"
            "rxq2@wq0.2;"
            "rxq3@wq0.3;"
            "rxq4@wq0.4;"
            "rxq5@wq0.5;"
            "rxq6@wq0.6;"
            "rxq7@wq0.7"
        )
        dmas2 = (
            "txq0@wq1.0;"
            "txq1@wq1.1;"
            "txq2@wq1.2;"
            "txq3@wq1.3;"
            "txq4@wq1.4;"
            "txq5@wq1.5;"
            "rxq2@wq1.2;"
            "rxq3@wq1.3;"
            "rxq4@wq1.4;"
            "rxq5@wq1.5;"
            "rxq6@wq1.6;"
            "rxq7@wq1.7"
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
        self.config_vm_combined(combined=8)
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

    def test_packed_non_mergeable_8_queues_large_packet_paylocad_with_kernel_driver(
        self,
    ):
        """
        Test Case 14: VM2VM vhost-user/virtio-net packed ring non-mergeable path 8 queues test with large packet payload with dsa kernel driver
        """
        self.DC.create_work_queue(work_queue_number=4, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=4, dsa_index=1)
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.1;"
            "txq3@wq0.1;"
            "txq4@wq0.2;"
            "txq5@wq0.2;"
            "txq6@wq0.3;"
            "txq7@wq0.3;"
            "rxq0@wq0.0;"
            "rxq1@wq0.0;"
            "rxq2@wq0.1;"
            "rxq3@wq0.1;"
            "rxq4@wq0.2;"
            "rxq5@wq0.2;"
            "rxq6@wq0.3;"
            "rxq7@wq0.3"
        )
        dmas2 = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.1;"
            "txq3@wq0.1;"
            "txq4@wq0.2;"
            "txq5@wq0.2;"
            "txq6@wq0.3;"
            "txq7@wq0.3;"
            "rxq0@wq0.0;"
            "rxq1@wq0.0;"
            "rxq2@wq0.1;"
            "rxq3@wq0.1;"
            "rxq4@wq0.2;"
            "rxq5@wq0.2;"
            "rxq6@wq0.3;"
            "rxq7@wq0.3"
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
        self.config_vm_combined(combined=8)
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

    def test_split_non_mergeable_16_queues_with_rx_tx_csum_in_sw(self):
        """
        Test Case 15: VM2VM vhost-user/virtio-net split ring non-mergeable 16 queues test with Rx/Tx csum in SW
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2,
            driver_name="vfio-pci",
            dsa_index_list=[2, 3],
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
            "rxq0@wq0.0;"
            "rxq1@wq0.0;"
            "rxq2@wq0.0;"
            "rxq3@wq0.0;"
            "rxq4@wq0.0;"
            "rxq5@wq0.0;"
            "rxq6@wq0.0;"
            "rxq7@wq0.0;"
            "rxq8@wq0.0;"
            "rxq9@wq0.0;"
            "rxq10@wq0.0;"
            "rxq11@wq0.0;"
            "rxq12@wq0.0;"
            "rxq13@wq0.0;"
            "rxq14@wq0.0;"
            "rxq15@wq0.0"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
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
            "rxq0@wq0.0;"
            "rxq1@wq0.1;"
            "rxq2@wq0.2;"
            "rxq3@wq0.3;"
            "rxq4@wq0.4;"
            "rxq5@wq0.5;"
            "rxq6@wq0.6;"
            "rxq7@wq0.7;"
            "rxq8@wq1.0;"
            "rxq9@wq1.1;"
            "rxq10@wq1.2;"
            "rxq11@wq1.3;"
            "rxq12@wq1.4;"
            "rxq13@wq1.5;"
            "rxq14@wq1.6;"
            "rxq15@wq1.7"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
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
            ports=self.use_dsa_list,
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
        self.config_vm_combined(combined=16)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
            )
        )
        dmas2 = (
            "txq12@wq1.0;"
            "txq13@wq1.0;"
            "txq14@wq1.0;"
            "txq15@wq1.0;"
            "rxq12@wq1.1;"
            "rxq13@wq1.1;"
            "rxq14@wq1.1;"
            "rxq15@wq1.1"
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
            ports=self.use_dsa_list,
        )
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

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
        self.config_vm_combined(combined=1)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_perf_result()

    def test_packed_mergeable_16_queues_with_rx_tx_csum_in_sw(self):
        """
        Test Case 16: VM2VM vhost-user/virtio-net packed ring mergeable 16 queues test with Rx/Tx csum in SW
        """
        self.DC.create_work_queue(work_queue_number=8, dsa_index=0)
        self.DC.create_work_queue(work_queue_number=8, dsa_index=1)
        self.use_dsa_list = self.DC.bind_dsa_to_dpdk(
            dsa_number=2,
            driver_name="vfio-pci",
            dsa_index_list=[2, 3],
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
            "rxq0@wq0.0;"
            "rxq1@wq0.0;"
            "rxq2@wq0.0;"
            "rxq3@wq0.0;"
            "rxq4@wq0.0;"
            "rxq5@wq0.0;"
            "rxq6@wq0.0;"
            "rxq7@wq0.0;"
            "rxq8@wq0.0;"
            "rxq9@wq0.0;"
            "rxq10@wq0.0;"
            "rxq11@wq0.0;"
            "rxq12@wq0.0;"
            "rxq13@wq0.0;"
            "rxq14@wq0.0;"
            "rxq15@wq0.0"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
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
            "rxq0@wq0.0;"
            "rxq1@wq0.1;"
            "rxq2@wq0.2;"
            "rxq3@wq0.3;"
            "rxq4@wq0.4;"
            "rxq5@wq0.5;"
            "rxq6@wq0.6;"
            "rxq7@wq0.7;"
            "rxq8@wq1.0;"
            "rxq9@wq1.1;"
            "rxq10@wq1.2;"
            "rxq11@wq1.3;"
            "rxq12@wq1.4;"
            "rxq13@wq1.5;"
            "rxq14@wq1.6;"
            "rxq15@wq1.7"
            % (
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[0],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
                self.use_dsa_list[1],
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
            ports=self.use_dsa_list,
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

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vhost_user_pmd.quit()

    def tear_down(self):
        self.stop_all_apps()
        self.dut.kill_all()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.DC.reset_all_work_queue()
        self.DC.bind_all_dsa_to_kernel()

    def tear_down_all(self):
        self.dut.close_session(self.vhost_user)

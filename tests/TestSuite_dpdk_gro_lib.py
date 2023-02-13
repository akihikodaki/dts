# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.

dpdk gro lib test suite.
In this suite, in order to check the performance of gso lib, will use one
hostcpu to start qemu and only have one vcpu
"""
import re
import time

import framework.utils as utils
import tests.vhost_peer_conf as peer
from framework.test_case import TestCase
from framework.virt_common import VM


class TestDPDKGROLib(TestCase):
    def set_up_all(self):
        # get and bind the port in config file
        self.pci = peer.get_pci_info()
        self.pci_drv = peer.get_pci_driver_info()
        self.peer_pci = peer.get_pci_peer_info()
        self.nic_in_kernel = peer.get_pci_peer_intf_info()
        self.verify(
            len(self.pci) != 0
            and len(self.pci_drv) != 0
            and len(self.peer_pci) != 0
            and len(self.nic_in_kernel) != 0,
            "Pls config the direct connection info in vhost_peer_conf.cfg",
        )
        bind_script_path = self.dut.get_dpdk_bind_script()
        self.dut.send_expect(
            "%s --bind=%s %s" % (bind_script_path, self.drivername, self.pci), "# "
        )
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]

        # get the numa info about the pci info which config in peer cfg
        bus = int(self.pci[5:7], base=16)
        if bus >= 128:
            self.socket = 1
        else:
            self.socket = 0
        # get core list on this socket, 2 cores for testpmd, 1 core for qemu
        cores_config = "1S/3C/1T"
        self.verify(
            self.dut.number_of_cores >= 3,
            "There has not enought cores to test this case %s" % self.suite_name,
        )
        cores_list = self.dut.get_core_list("1S/3C/1T", socket=self.socket)
        self.vhost_list = cores_list[0:2]
        self.qemu_cpupin = cores_list[2:3][0]

        # Set the params for VM
        self.virtio_ip1 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.memory_channel = self.dut.get_memory_channels()
        if len(set([int(core["socket"]) for core in self.dut.cores])) == 1:
            self.socket_mem = "1024"
        else:
            self.socket_mem = "1024,1024"
        self.base_dir = self.dut.base_dir.replace("~", "/root")

    def set_up(self):
        #
        # Run before each test case.
        #
        # Clean the execution ENV
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def launch_testpmd_gro_on(self, mode=1, queue=1):
        #
        # Launch the vhost sample with different parameters
        # mode 1 : tcp traffic light mode
        # mode 2 : tcp traffic heavy mode
        # mode 3 : vxlan traffic light mode
        # mode 4 : tcp traffic flush 4
        eal_param = self.dut.create_eal_parameters(
            cores=self.vhost_list,
            vdevs=["net_vhost0,iface=%s/vhost-net,queues=%s" % (self.base_dir, queue)],
            ports=[self.pci],
        )
        self.testcmd_start = (
            self.path
            + eal_param
            + " -- -i  --enable-hw-vlan-strip --tx-offloads=0x00 --txd=1024 --rxd=1024"
        )
        self.vhost_user = self.dut.new_session(suite="user")
        self.vhost_user.send_expect(self.testcmd_start, "testpmd> ", 120)
        self.set_testpmd_params()

    def set_testpmd_params(self, mode=1):
        # set testpmd params
        self.vhost_user.send_expect("set fwd csum", "testpmd> ", 120)
        self.vhost_user.send_expect("csum mac-swap off 0", "testpmd> ", 120)
        self.vhost_user.send_expect("csum mac-swap off 1", "testpmd> ", 120)
        self.vhost_user.send_expect("stop", "testpmd> ", 120)
        self.vhost_user.send_expect("port stop 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port stop 1", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set tcp hw 0", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set ip hw 0", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set tcp hw 1", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set ip hw 1", "testpmd> ", 120)
        if mode == 1 or mode == 5:
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 1", "testpmd> ", 120)
        elif mode == 2:
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 2", "testpmd> ", 120)
        elif mode == 3:
            self.vhost_user.send_expect("csum parse-tunnel on 1", "testpmd> ", 120)
            self.vhost_user.send_expect("csum parse-tunnel on 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set outer-ip hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 2", "testpmd> ", 120)
        else:
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 4", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 1", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def set_testpmd_gro_off(self):
        #
        # Launch the vhost sample with different parameters
        #
        self.vhost_user.send_expect("stop", "testpmd> ", 120)
        self.vhost_user.send_expect("set port 0 gro off", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def quit_testpmd(self):
        # Quit testpmd and close temp ssh session
        self.vhost_user.send_expect("quit", "#", 120)
        self.dut.close_session(self.vhost_user)

    def config_kernel_nic_host(self, mode=1):
        if mode == 0:
            self.dut.send_expect("ip netns del ns1", "#")
            self.dut.send_expect("ip netns add ns1", "#")
            self.dut.send_expect("ip link set %s netns ns1" % self.nic_in_kernel, "#")
            self.dut.send_expect(
                "ip netns exec ns1 ifconfig %s 1.1.1.8 up" % self.nic_in_kernel, "#"
            )
            self.dut.send_expect(
                "ip netns exec ns1 ethtool -K %s tso on" % self.nic_in_kernel, "#"
            )
        if mode == 1:
            self.dut.send_expect("ip netns del ns1", "#")
            self.dut.send_expect("ip netns add ns1", "#")
            self.dut.send_expect("ip link set %s netns ns1" % self.nic_in_kernel, "#")
            self.dut.send_expect(
                "ip netns exec ns1 ifconfig %s 1.1.2.4/24 up" % self.nic_in_kernel, "#"
            )
            self.dut.send_expect(
                "ip netns exec ns1 ip link add vxlan1 type vxlan id 42 dev %s dstport 4789"
                % self.nic_in_kernel,
                "#",
            )
            self.dut.send_expect(
                "ip netns exec ns1 bridge fdb append to 00:00:00:00:00:00 dst 1.1.2.3 dev vxlan1",
                "#",
            )
            self.dut.send_expect(
                "ip netns exec ns1 ip addr add 50.1.1.1/24 dev vxlan1", "#"
            )
            self.dut.send_expect("ip netns exec ns1 ip link set up dev vxlan1", "#")

    def set_vm_cpu_number(self, vm_config):
        # config the vcpu numbers = 1
        # config the cpupin only have one core
        params_number = len(vm_config.params)
        for i in range(params_number):
            if list(vm_config.params[i].keys())[0] == "cpu":
                vm_config.params[i]["cpu"][0]["number"] = 1
                vm_config.params[i]["cpu"][0]["cpupin"] = self.qemu_cpupin

    def start_vm(self, queue=1):
        self.vm1 = VM(self.dut, "vm0", "vhost_sample")
        self.vm1.load_config()
        vm_params_1 = {}
        vm_params_1["driver"] = "vhost-user"
        vm_params_1["opt_path"] = self.base_dir + "/vhost-net"
        vm_params_1["opt_mac"] = self.virtio_mac1
        vm_params_1["opt_queue"] = queue
        if int(queue) > 1:
            mq_pram = ",mq=on,vectors=%s" % (2 + 2 * int(queue))
        else:
            mq_pram = ""
        vm_params_1["opt_settings"] = (
            "mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on%s" % mq_pram
        )
        self.vm1.set_vm_device(**vm_params_1)
        self.set_vm_cpu_number(self.vm1)
        try:
            self.vm1_dut = self.vm1.start(load_config=False, set_target=False)
            if self.vm1_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            print((utils.RED("Failure for %s" % str(e))))

    def iperf_result_verify(self, run_info):
        """
        Get the iperf test result
        """
        fmsg = self.dut.send_expect("cat /root/iperf_client.log", "#")
        print(fmsg)
        iperfdata = re.compile("[\d+]*.[\d+]* [M|G|K]bits/sec").findall(fmsg)
        print(iperfdata)
        self.verify(iperfdata, "There no data about this case")
        self.result_table_create(["Data", "Unit"])
        results_row = [run_info]
        results_row.append(iperfdata[-1])
        self.result_table_add(results_row)
        self.result_table_print()
        self.output_result = "Iperf throughput is %s" % iperfdata[-1]
        self.logger.info(self.output_result)
        iperfdata_kb = 0
        tmp_value = iperfdata[-1].split(" ")[0]
        if "Gbits" in iperfdata[-1]:
            iperfdata_kb = float(tmp_value) * 1000000
        elif "Mbits" in iperfdata[-1]:
            iperfdata_kb = float(tmp_value) * 1000
        else:
            iperfdata_kb = float(tmp_value)
        return iperfdata_kb

    def test_vhost_gro_tcp_lightmode(self):
        self.config_kernel_nic_host(0)
        self.launch_testpmd_gro_on()
        self.start_vm()
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port["intf"]
        # Start the Iperf test
        self.vm1_dut.send_expect("ifconfig -a", "#", 30)
        self.vm1_dut.send_expect(
            "ifconfig %s %s" % (self.vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm1_dut.send_expect("ifconfig %s up" % self.vm1_intf, "#", 10)
        self.vm1_dut.send_expect("ethtool -K %s gro off" % (self.vm1_intf), "#", 10)
        self.vm1_dut.send_expect("iperf -s", "", 10)
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.dut.send_expect(
            "ip netns exec ns1 iperf -c %s -i 1 -t 10 -P 1> /root/iperf_client.log &"
            % (self.virtio_ip1),
            "",
            180,
        )
        time.sleep(30)
        tc1_perfdata = self.iperf_result_verify("GRO lib")
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        # Turn off DPDK GRO lib and Kernel GRO off
        self.set_testpmd_gro_off()
        self.dut.send_expect(
            "ip netns exec ns1 iperf -c %s -i 1 -t 10  -P 1 > /root/iperf_client.log &"
            % (self.virtio_ip1),
            "",
            180,
        )
        time.sleep(30)
        self.iperf_result_verify("Kernel GRO")
        print(("the Kernel GRO %s " % (self.output_result)))
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect(
            "echo %s > /root/dpdk_gro_lib_on_iperf_tc1.log" % tc1_perfdata, "#", 10
        )

    def test_vhost_gro_tcp_heavymode(self):
        self.config_kernel_nic_host(0)
        self.heavymode = 2
        self.launch_testpmd_gro_on(self.heavymode)
        self.start_vm()
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port["intf"]
        # Start the Iperf test
        self.vm1_dut.send_expect("ifconfig -a", "#", 30)
        self.vm1_dut.send_expect(
            "ifconfig %s %s" % (self.vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm1_dut.send_expect("ifconfig %s up" % self.vm1_intf, "#", 10)
        self.vm1_dut.send_expect("ethtool -K %s gro off" % (self.vm1_intf), "#", 10)
        self.vm1_dut.send_expect("iperf -s", "", 10)
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.dut.send_expect(
            "ip netns exec ns1 iperf -c %s -i 1 -t 10 -P 1> /root/iperf_client.log &"
            % (self.virtio_ip1),
            "",
            180,
        )
        time.sleep(30)
        self.iperf_result_verify("GRO lib")
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_gro_tcp_heavymode_flush4(self):
        self.config_kernel_nic_host(0)
        self.heavymode = 4
        self.launch_testpmd_gro_on(self.heavymode)
        self.start_vm()
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port["intf"]
        # Start the Iperf test
        self.vm1_dut.send_expect("ifconfig -a", "#", 30)
        self.vm1_dut.send_expect(
            "ifconfig %s %s" % (self.vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm1_dut.send_expect("ifconfig %s up" % self.vm1_intf, "#", 10)
        self.vm1_dut.send_expect("ethtool -K %s gro off" % (self.vm1_intf), "#", 10)
        self.vm1_dut.send_expect("iperf -s", "", 10)
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.dut.send_expect(
            "ip netns exec ns1 iperf -c %s -i 1 -t 10 -P 1> /root/iperf_client.log &"
            % (self.virtio_ip1),
            "",
            180,
        )
        time.sleep(30)
        self.iperf_result_verify("GRO lib")
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_gro_with_2queues_tcp_lightmode(self):
        """
        Test Case5: DPDK GRO test with 2 queues using tcp/ipv4 traffic
        """
        self.config_kernel_nic_host(0)
        self.launch_testpmd_gro_on(mode=1, queue=2)
        self.start_vm(queue=2)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port["intf"]
        # Start the Iperf test
        self.vm1_dut.send_expect("ifconfig -a", "#", 30)
        self.vm1_dut.send_expect(
            "ifconfig %s %s" % (self.vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm1_dut.send_expect("ifconfig %s up" % self.vm1_intf, "#", 10)
        self.vm1_dut.send_expect("ethtool -K %s gro off" % (self.vm1_intf), "#", 10)
        self.vm1_dut.send_expect("iperf -s", "", 10)
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.dut.send_expect(
            "ip netns exec ns1 iperf -c %s -i 2 -t 60 -f g -m > /root/iperf_client.log &"
            % (self.virtio_ip1),
            "",
            180,
        )
        time.sleep(60)
        perfdata = self.iperf_result_verify("GRO lib")
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        # Turn off DPDK GRO lib and Kernel GRO off
        self.set_testpmd_gro_off()
        self.dut.send_expect(
            "ip netns exec ns1 iperf -c %s -i 2 -t 60 -f g -m > /root/iperf_client.log &"
            % (self.virtio_ip1),
            "",
            180,
        )
        time.sleep(60)
        self.iperf_result_verify("Kernel GRO")
        print(("the Kernel GRO %s " % (self.output_result)))
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect(
            "echo %s > /root/dpdk_gro_lib_on_iperf_tc5.log" % perfdata, "#", 10
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net" % self.base_dir, "#")
        time.sleep(2)
        self.dut.send_expect("ip netns del ns1", "# ", 30)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % (self.peer_pci), "# ", 30
        )
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -b %s %s" % (self.pci_drv, self.peer_pci),
            "# ",
            30,
        )

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("ip netns del ns1", "# ", 30)
        self.dut.send_expect("./usertools/dpdk-devbind.py -u %s" % (self.pci), "# ", 30)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -b %s %s" % (self.pci_drv, self.pci), "# ", 30
        )

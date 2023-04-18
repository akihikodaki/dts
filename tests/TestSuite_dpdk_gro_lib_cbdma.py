# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re
import time

import framework.utils as utils
import tests.vhost_peer_conf as peer
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM
from tests.virtio_common import basic_common as BC
from tests.virtio_common import cbdma_common as CC


class TestDPDKGROLibCbdma(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.def_driver = self.dut.ports_info[self.dut_ports[0]][
            "port"
        ].get_nic_driver()
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
            "%s --bind=%s %s" % (bind_script_path, self.def_driver, self.pci), "# "
        )
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:3]
        self.qemu_cpupin = self.cores_list[3:4][0]

        # Set the params for VM
        self.virtio_ip1 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.memory_channel = self.dut.get_memory_channels()
        if len(set([int(core["socket"]) for core in self.dut.cores])) == 1:
            self.socket_mem = "1024"
        else:
            self.socket_mem = "1024,1024"
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_pmd = PmdOutput(self.dut, self.vhost_user)
        self.BC = BC(self)
        self.CC = CC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def set_testpmd_params(self):
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
        self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
        self.vhost_user.send_expect("set gro flush 1", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 1", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def quit_testpmd(self):
        self.vhost_user.send_expect("quit", "#", 120)
        self.dut.close_session(self.vhost_user)

    def config_kernel_nic_host(self):
        self.dut.send_expect("ip netns del ns1", "#")
        self.dut.send_expect("ip netns add ns1", "#")
        self.dut.send_expect("ip link set %s netns ns1" % self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ifconfig %s 1.1.1.8 up" % self.nic_in_kernel, "#"
        )
        self.dut.send_expect(
            "ip netns exec ns1 ethtool -K %s tso on" % self.nic_in_kernel, "#"
        )

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
        vm_params_1[
            "opt_settings"
        ] = "mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,mq=on,vectors=15"
        self.vm1.set_vm_device(**vm_params_1)
        self.set_vm_cpu_number(self.vm1)
        try:
            self.vm1_dut = self.vm1.start(load_config=False, set_target=False)
            if self.vm1_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            print((utils.RED("Failure for %s" % str(e))))
        self.vm1_dut.restore_interfaces()

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

    def test_vhost_gro_tcp_ipv4_with_cbdma_enable(self):
        """
        Test Case1: DPDK GRO test with two queues and cbdma channels using tcp/ipv4 traffic
        """
        self.config_kernel_nic_host()
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "rxq0@%s;"
            "rxq1@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
            )
        )
        param = "--txd=1024 --rxd=1024 --txq=2 --rxq=2 --nb-cores=2"
        eal_param = "--vdev 'net_vhost0,iface=vhost-net,queues=2,dmas=[%s]'" % dmas
        ports = cbdmas
        ports.append(self.pci)
        self.vhost_pmd.start_testpmd(
            cores=self.vhost_core_list,
            ports=ports,
            prefix="vhost",
            eal_param=eal_param,
            param=param,
        )
        self.set_testpmd_params()
        self.start_vm(queue=2)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port["intf"]
        self.vm1_dut.send_expect(
            "ifconfig %s %s up" % (self.vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm1_dut.send_expect("ethtool -L %s combined 2" % self.vm1_intf, "#", 10)
        self.vm1_dut.send_expect("ethtool -K %s gro off" % (self.vm1_intf), "#", 10)
        self.vm1_dut.send_expect("iperf -s", "", 10)
        self.dut.send_expect("rm /root/iperf_client.log", "#", 10)
        out = self.dut.send_expect(
            "ip netns exec ns1 iperf -c %s -i 1 -t 60 -m -P 2 > /root/iperf_client.log &"
            % (self.virtio_ip1),
            "",
            180,
        )
        self.func_name_list = ["virtio_dev_rx_async", "virtio_dev_tx_async"]
        self.get_and_verify_func_name_of_perf_top(self.func_name_list)
        time.sleep(30)
        perfdata = self.iperf_result_verify("GRO lib")
        print(("the GRO lib %s " % (self.output_result)))
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        exp_perfdata = 10000000
        if exp_perfdata:
            self.verify(
                float(perfdata) > float(exp_perfdata),
                "TestFailed: W/cbdma iperf data is %s Kbits/sec, W/O cbdma iperf data is %s Kbits/sec"
                % (perfdata, exp_perfdata),
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
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
        self.dut.send_expect("ip netns del ns1", "# ", 30)
        self.dut.send_expect("./usertools/dpdk-devbind.py -u %s" % (self.pci), "# ", 30)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -b %s %s" % (self.pci_drv, self.pci), "# ", 30
        )

# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import re

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM

from .virtio_common import basic_common as BC


class TestVM2VMVirtioNetPerf(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list("all", socket=self.ports_socket)
        self.vhost_user_cores = self.cores_list[0:3]
        self.vm_num = 2
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.BC = BC(self)

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -I qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_dut = []
        self.vm = []

    def start_vhost_testpmd(self):
        """
        start vhost-user testpmd
        """
        eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1'"
        )
        param = "--nb-cores=2 --txd=1024 --rxd=1024"
        self.vhost_user_pmd.start_testpmd(
            cores=self.vhost_user_cores,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="vhost-user",
            fixed_prefix=True,
        )
        self.vhost_user_pmd.execute_cmd("start")

    def start_vms(self, mrg_rxbuf=True, packed=False):
        """
        start two VM, each VM has one virtio device
        """
        mrg_rxbuf_param = "on" if mrg_rxbuf else "off"
        packed_param = ",packed=on" if packed else ""
        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, "vm%d" % i, "vhost_sample")
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            vm_params["opt_settings"] = (
                "disable-modern=false,mrg_rxbuf=%s,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on%s"
                % (mrg_rxbuf_param, packed_param)
            )
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

    def verify_xstats_info_on_vhost(self):
        """
        check both 2VMs can receive and send big packets to each other
        """
        out_tx = self.vhost_user_pmd.execute_cmd("show port xstats 0")
        out_rx = self.vhost_user_pmd.execute_cmd("show port xstats 1")
        rx_info = re.search("rx_q0_size_1519_max_packets:\s*(\d*)", out_rx)
        tx_info = re.search("tx_q0_size_1519_max_packets:\s*(\d*)", out_tx)
        self.verify(
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1522"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1522"
        )

    def offload_capbility_check(self, vm_session):
        """
        check UFO and TSO offload status on for the Virtio-net driver in VM
        """
        vm_intf = vm_session.ports_info[0]["intf"]
        vm_session.send_expect("ethtool -k %s > offload.log" % vm_intf, "#", 10)
        fmsg = vm_session.send_expect("cat ./offload.log", "#")
        tcp_info = re.search("tx-tcp-segmentation:\s*(\S*)", fmsg)
        tcp_enc_info = re.search("tx-tcp-ecn-segmentation:\s*(\S*)", fmsg)
        tcp6_info = re.search("tx-tcp6-segmentation:\s*(\S*)", fmsg)
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

    def test_vm2vm_split_ring_iperf_with_tso(self):
        """
        Test Case 1: VM2VM split ring vhost-user/virtio-net test with tcp traffic
        """
        self.start_vhost_testpmd()
        self.start_vms(mrg_rxbuf=False, packed=False)
        self.BC.config_2_vms_ip()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_vm2vm_split_ring_device_capbility(self):
        """
        Test Case 2: Check split ring virtio-net device capability
        """
        self.start_vhost_testpmd()
        self.start_vms(mrg_rxbuf=True, packed=False)
        self.offload_capbility_check(self.vm_dut[0])
        self.offload_capbility_check(self.vm_dut[1])

    def test_vm2vm_packed_ring_iperf_with_tso(self):
        """
        Test Case 3: VM2VM packed ring vhost-user/virtio-net test with tcp traffic
        """
        self.start_vhost_testpmd()
        self.start_vms(mrg_rxbuf=True, packed=True)
        self.BC.config_2_vms_ip()
        self.BC.run_iperf_test_between_2_vms()
        self.BC.check_iperf_result_between_2_vms()
        self.verify_xstats_info_on_vhost()

    def test_vm2vm_packed_ring_device_capbility(self):
        """
        Test Case 4: Check packed ring virtio-net device capability
        """
        self.start_vhost_testpmd()
        self.start_vms(mrg_rxbuf=True, packed=True)
        self.offload_capbility_check(self.vm_dut[0])
        self.offload_capbility_check(self.vm_dut[1])

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vhost_user_pmd.quit()

    def tear_down(self):
        """
        run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)

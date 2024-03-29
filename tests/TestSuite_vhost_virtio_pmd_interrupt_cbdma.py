# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
vhost virtio pmd interrupt need test with l3fwd-power sample
"""

import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM
from tests.virtio_common import cbdma_common as CC


class TestVhostVirtioPmdInterruptCbdma(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.fix_ip = False
        self.nb_cores = 4
        self.queues = 4
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len(
            [n for n in self.dut.cores if int(n["socket"]) == self.ports_socket]
        )
        self.core_list = self.dut.get_core_list("all", socket=self.ports_socket)
        self.vhost_core_list = self.core_list[0:17]
        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.logger.info(
            "Please comfirm the kernel of vm greater than 4.8.0 and enable vfio-noiommu in kernel"
        )
        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.app_l3fwd_power_path = self.dut.apps_name["l3fwd-power"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.l3fwdpower_name = self.app_l3fwd_power_path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vhost_pmd = PmdOutput(self.dut, self.vhost_user)
        self.vm_dut = None
        self.CC = CC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.verify_info = []
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    def prepare_vm_env(self):
        """
        rebuild l3fwd-power in vm and set the virtio-net driver
        """
        out = self.vm_dut.build_dpdk_apps("examples/l3fwd-power")
        self.verify("Error" not in out, "compilation l3fwd-power error")
        self.vm_dut.send_expect("modprobe vfio enable_unsafe_noiommu_mode=1", "#")
        self.vm_dut.send_expect("modprobe vfio-pci", "#")
        self.vm_dut.ports_info[0]["port"].bind_driver("vfio-pci")

    def launch_l3fwd_power_in_vm(self):
        """
        launch l3fwd-power with a virtual vhost device
        """
        self.verify(
            len(self.vm_dut.cores) >= self.nb_cores,
            "The vm done not has enought cores to use, please config it",
        )
        core_config = "1S/%dC/1T" % self.nb_cores
        core_list_l3fwd = self.vm_dut.get_core_list(core_config)
        core_mask_l3fwd = utils.create_mask(core_list_l3fwd)

        res = True
        self.logger.info("Launch l3fwd_sample sample:")
        config_info = ""
        for queue in range(self.queues):
            if config_info != "":
                config_info += ","
            config_info += "(%d,%d,%s)" % (0, queue, core_list_l3fwd[queue])
            info = {"core": core_list_l3fwd[queue], "port": 0, "queue": queue}
            self.verify_info.append(info)

        command_client = (
            "./%s " % self.app_l3fwd_power_path
            + "-c %s -n 4 --log-level='user1,7' -- -p 1 -P "
            + "--config '%s' --no-numa  --parse-ptype --interrupt-only"
        )
        command_line_client = command_client % (core_mask_l3fwd, config_info)
        self.vm_dut.get_session_output(timeout=2)
        self.vm_dut.send_expect(command_line_client, "POWER", 40)
        time.sleep(10)
        out = self.vm_dut.get_session_output()
        if "Error" in out and "Error opening" not in out:
            self.logger.error("Launch l3fwd-power sample error")
            res = False
        else:
            self.logger.info("Launch l3fwd-power sample finished")
        self.verify(res is True, "Lanuch l3fwd failed")

    def set_vm_vcpu_number(self):
        # config the vcpu numbers
        params_number = len(self.vm.params)
        for i in range(params_number):
            if list(self.vm.params[i].keys())[0] == "cpu":
                self.vm.params[i]["cpu"][0]["number"] = self.queues

    def start_vms(self, mode=0, packed=False):
        """
        start qemus
        """
        self.vm = VM(self.dut, "vm0", "vhost_sample")
        self.vm.load_config()
        vm_params = {}
        vm_params["driver"] = "vhost-user"
        vm_params["opt_path"] = "%s/vhost-net" % self.base_dir
        vm_params["opt_mac"] = "00:11:22:33:44:55"
        vm_params["opt_queue"] = self.queues
        packed_path = ",packed=on" if packed else ""
        opt_param = "mrg_rxbuf=on,csum=on,mq=on,vectors=%d%s" % (
            (2 * self.queues + 2),
            packed_path,
        )
        if mode == 0:
            vm_params["opt_settings"] = "disable-modern=true," + opt_param
        elif mode == 1:
            vm_params["opt_settings"] = "disable-modern=false," + opt_param
        self.vm.set_vm_device(**vm_params)
        self.set_vm_vcpu_number()
        try:
            # Due to we have change the params info before,
            # so need to start vm with load_config=False
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def check_related_cores_status_in_l3fwd(self, out_result, status, fix_ip):
        """
        check the vcpu status
        when tester send fix_ip packet, the cores in l3fwd only one can change the status
        when tester send not fix_ip packets, all the cores in l3fwd will change the status
        """
        change = 0
        for i in range(len(self.verify_info)):
            if status == "waked up":
                info = "lcore %s is waked up from rx interrupt on port %d queue %d"
                info = info % (
                    self.verify_info[i]["core"],
                    self.verify_info[i]["port"],
                    self.verify_info[i]["queue"],
                )
            elif status == "sleeps":
                info = (
                    "lcore %s sleeps until interrupt triggers"
                    % self.verify_info[i]["core"]
                )
            if info in out_result:
                change = change + 1
                self.logger.info(info)
        # if use fix ip, only one cores can waked up/sleep
        # if use dynamic ip, all the cores will waked up/sleep
        if fix_ip is True:
            self.verify(change == 1, "There has other cores change the status")
        else:
            self.verify(change == self.queues, "There has cores not change the status")

    def set_fields(self):
        """
        set ip protocol field behavior
        """
        fields_config = {
            "ip": {
                "dst": {"action": "random"},
            },
        }
        return fields_config

    def send_packets(self):
        tgen_input = []
        if self.fix_ip is True:
            pkt = Packet(pkt_type="UDP")
        else:
            pkt = Packet(pkt_type="IP_RAW")
        pkt.config_layer("ether", {"dst": "%s" % self.dst_mac})
        pkt.save_pcapfile(self.tester, "%s/interrupt.pcap" % self.out_path)
        tgen_input.append(
            (self.tx_port, self.tx_port, "%s/interrupt.pcap" % self.out_path)
        )
        self.tester.pktgen.clear_streams()
        vm_config = self.set_fields()
        if self.fix_ip is True:
            vm_config = None
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, 100, vm_config, self.tester.pktgen
        )
        # set traffic option
        traffic_opt = {"delay": 5, "duration": 20}
        _, pps = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=traffic_opt
        )

    def send_and_verify(self):
        """
        start to send packets and check the cpu status
        stop to send packets and check the cpu status
        """
        # Send random dest ip address packets to host nic
        # packets will distribute to all queues
        self.fix_ip = False
        self.send_packets()
        out = self.vm_dut.get_session_output(timeout=5)
        self.check_related_cores_status_in_l3fwd(out, "waked up", fix_ip=False)
        self.check_related_cores_status_in_l3fwd(out, "sleeps", fix_ip=False)

        # Send fixed dest ip address packets to host nic
        # packets will distribute to 1 queue
        self.fix_ip = True
        self.send_packets()
        out = self.vm_dut.get_session_output(timeout=5)
        self.check_related_cores_status_in_l3fwd(out, "waked up", fix_ip=True)
        self.check_related_cores_status_in_l3fwd(out, "sleeps", fix_ip=True)

    def stop_all_apps(self):
        """
        close all vms
        """
        if self.vm_dut is not None:
            vm_dut2 = self.vm_dut.create_session(name="vm_dut2")
            vm_dut2.send_expect("killall %s" % self.l3fwdpower_name, "# ", 10)
            self.vm.stop()
            self.dut.close_session(vm_dut2)
        self.vhost_pmd.quit()

    def test_perf_virtio95_interrupt_test_with_16_queues_and_cbdma_enable(self):
        """
        Test Case 1: Basic virtio0.95 interrupt test with 16 queues and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(cbdma_num=16, driver_name="vfio-pci")
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
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
                cbdmas[8],
                cbdmas[9],
                cbdmas[10],
                cbdmas[11],
                cbdmas[12],
                cbdmas[13],
                cbdmas[14],
                cbdmas[15],
            )
        )
        vhost_param = "--nb-cores=16 --rxq=16 --txq=16 --rss-ip"
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net,queues=16,dmas=[%s]'" % dmas
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
        self.start_vms(mode=0, packed=False)
        self.prepare_vm_env()
        self.nb_cores = 16
        self.launch_l3fwd_power_in_vm()
        self.send_and_verify()

    def test_perf_virtio10_interrupt_test_with_4_queues_and_cbdma_enable(self):
        """
        Test Case 2: Basic virtio-1.0 interrupt test with 4 queues and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "rxq0@%s;"
            "rxq1@%s;"
            "rxq2@%s;"
            "rxq3@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_param = "--nb-cores=4 --rxq=4 --txq=4 --rss-ip"
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net,queues=4,dmas=[%s]'" % dmas
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
        self.queues = 4
        self.start_vms(mode=1, packed=False)
        self.prepare_vm_env()
        self.nb_cores = 4
        self.launch_l3fwd_power_in_vm()
        self.send_and_verify()

    def test_perf_virtio11_interrupt_test_with_16_queues_and_cbdma_enable(
        self,
    ):
        """
        Test Case 3: Packed ring virtio interrupt test with 16 queues and cbdma enable
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
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
                cbdmas[3],
            )
        )
        vhost_param = "--nb-cores=16 --rxq=16 --txq=16 --rss-ip"
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net,queues=16,dmas=[%s]'" % dmas
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
        self.start_vms(mode=1, packed=True)
        self.prepare_vm_env()
        self.nb_cores = 16
        self.launch_l3fwd_power_in_vm()
        self.send_and_verify()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
        self.dut.close_session(self.vhost_user)

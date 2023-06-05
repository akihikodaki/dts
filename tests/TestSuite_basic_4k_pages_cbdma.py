# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import os
import random
import re
import string
import time
from copy import deepcopy

from framework.config import VirtConf
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.qemu_kvm import QEMUKvm
from framework.settings import (
    CONFIG_ROOT_PATH,
    UPDATE_EXPECTED,
    get_host_ip,
    load_global_setting,
)
from framework.test_case import TestCase


class TestBasic4kPagesCbdma(TestCase):
    def get_virt_config(self, vm_name):
        conf = VirtConf(CONFIG_ROOT_PATH + os.sep + self.suite_name + ".cfg")
        conf.load_virt_config(vm_name)
        virt_conf = conf.get_virt_config()
        return virt_conf

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            self.cores_num >= 4,
            "There has not enought cores to test this suite %s" % self.suite_name,
        )
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.virtio0_core_list = self.cores_list[9:11]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.nb_ports = 1
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.vm_num = 2
        self.virtio_ip1 = "1.1.1.1"
        self.virtio_ip2 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.virtio_mac2 = "52:54:00:00:00:02"
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.random_string = string.ascii_letters + string.digits
        self.addr = str(self.dut.get_ip_address())
        self.host_addr = get_host_ip(self.addr).split(":")[0]

        self.mount_tmpfs_for_4k(number=2)
        self.vm0_virt_conf = self.get_virt_config(vm_name="vm0")
        for param in self.vm0_virt_conf:
            if "cpu" in param.keys():
                self.vm0_cpupin = param["cpu"][0]["cpupin"]
                self.vm0_lcore = ",".join(list(self.vm0_cpupin.split()))
                self.vm0_lcore_smp = len(list(self.vm0_cpupin.split()))
            if "qemu" in param.keys():
                self.vm0_qemu_path = param["qemu"][0]["path"]
            if "mem" in param.keys():
                self.vm0_mem_size = param["mem"][0]["size"]
            if "disk" in param.keys():
                self.vm0_image_path = param["disk"][0]["file"]
            if "vnc" in param.keys():
                self.vm0_vnc = param["vnc"][0]["displayNum"]
            if "login" in param.keys():
                self.vm0_user = param["login"][0]["user"]
                self.vm0_passwd = param["login"][0]["password"]

        self.vm1_virt_conf = self.get_virt_config(vm_name="vm1")
        for param in self.vm1_virt_conf:
            if "cpu" in param.keys():
                self.vm1_cpupin = param["cpu"][0]["cpupin"]
                self.vm1_lcore = ",".join(list(self.vm1_cpupin.split()))
                self.vm1_lcore_smp = len(list(self.vm1_cpupin.split()))
            if "qemu" in param.keys():
                self.vm1_qemu_path = param["qemu"][0]["path"]
            if "mem" in param.keys():
                self.vm1_mem_size = param["mem"][0]["size"]
            if "disk" in param.keys():
                self.vm1_image_path = param["disk"][0]["file"]
            if "vnc" in param.keys():
                self.vm1_vnc = param["vnc"][0]["displayNum"]
            if "login" in param.keys():
                self.vm1_user = param["login"][0]["user"]
                self.vm1_passwd = param["login"][0]["password"]

        self.logger.info(
            "You can config packet_size in file %s.cfg," % self.suite_name
            + " in region 'suite' like packet_sizes=[64, 128, 256]"
        )
        if "packet_sizes" in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()["packet_sizes"]
        self.test_duration = self.get_suite_cfg()["test_duration"]
        self.gap = self.get_suite_cfg()["accepted_tolerance"]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "# ")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf /root/dpdk/vhost-net*", "# ")
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)
        self.vm_dut = []
        self.vm = []
        self.throughput = {}
        self.test_result = {}

    def start_vm0(self, packed=False, queues=1, server=False):
        packed_param = ",packed=on" if packed else ""
        mq_param = ",mq=on,vectors=%s" % (2 + 2 * queues) if queues > 1 else ""
        server = ",server" if server else ""
        self.qemu_cmd0 = (
            f"taskset -c {self.vm0_lcore} {self.vm0_qemu_path} -name vm0 -enable-kvm "
            f"-pidfile /tmp/.vm0.pid -daemonize -monitor unix:/tmp/vm0_monitor.sock,server,nowait "
            f"-netdev user,id=nttsip1,hostfwd=tcp:%s:6000-:22 -device e1000,netdev=nttsip1  "
            f"-chardev socket,id=char0,path=/root/dpdk/vhost-net0{server} "
            f"-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues={queues} "
            f"-device virtio-net-pci,netdev=netdev0,mac=%s,"
            f"disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on{packed_param}{mq_param} "
            f"-cpu host -smp {self.vm0_lcore_smp} -m {self.vm0_mem_size} -object memory-backend-file,id=mem,size={self.vm0_mem_size}M,mem-path=/mnt/tmpfs_nohuge0,share=on "
            f"-numa node,memdev=mem -mem-prealloc -drive file={self.vm0_image_path} "
            f"-chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 -device virtio-serial "
            f"-device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 -vnc :{self.vm0_vnc} "
        )

        self.vm0_session = self.dut.new_session(suite="vm0_session")
        cmd0 = self.qemu_cmd0 % (
            self.host_addr,
            self.virtio_mac1,
        )
        self.vm0_session.send_expect(cmd0, "# ")
        time.sleep(10)
        self.monitor_socket = "/tmp/vm0_monitor.sock"
        lcores = self.vm0_cpupin.split(" ")
        self.pin_threads(lcores)
        self.vm0_dut = self.connect_vm0()
        self.verify(self.vm0_dut is not None, "vm start fail")
        self.vm_session = self.vm0_dut.new_session(suite="vm_session")

    def start_vm1(self, packed=False, queues=1, server=False):
        packed_param = ",packed=on" if packed else ""
        mq_param = ",mq=on,vectors=%s" % (2 + 2 * queues) if queues > 1 else ""
        server = ",server" if server else ""
        self.qemu_cmd1 = (
            f"taskset -c {self.vm1_lcore} {self.vm1_qemu_path} -name vm1 -enable-kvm "
            f"-pidfile /tmp/.vm1.pid -daemonize -monitor unix:/tmp/vm1_monitor.sock,server,nowait "
            f"-netdev user,id=nttsip1,hostfwd=tcp:%s:6001-:22 -device e1000,netdev=nttsip1  "
            f"-chardev socket,id=char0,path=/root/dpdk/vhost-net1{server} "
            f"-netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues={queues} "
            f"-device virtio-net-pci,netdev=netdev0,mac=%s,"
            f"disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on{packed_param}{mq_param} "
            f"-cpu host -smp {self.vm1_lcore_smp} -m {self.vm1_mem_size} -object memory-backend-file,id=mem,size={self.vm1_mem_size}M,mem-path=/mnt/tmpfs_nohuge1,share=on "
            f"-numa node,memdev=mem -mem-prealloc -drive file={self.vm1_image_path} "
            f"-chardev socket,path=/tmp/vm1_qga0.sock,server,nowait,id=vm1_qga0 -device virtio-serial "
            f"-device virtserialport,chardev=vm1_qga0,name=org.qemu.guest_agent.0 -vnc :{self.vm1_vnc} "
        )

        self.vm1_session = self.dut.new_session(suite="vm1_session")
        cmd1 = self.qemu_cmd1 % (
            self.host_addr,
            self.virtio_mac2,
        )
        self.vm1_session.send_expect(cmd1, "# ")
        time.sleep(10)
        self.monitor_socket = "/tmp/vm1_monitor.sock"
        lcores = self.vm1_cpupin.split(" ")
        self.pin_threads(lcores)
        self.vm1_dut = self.connect_vm1()
        self.verify(self.vm1_dut is not None, "vm start fail")
        self.vm_session = self.vm1_dut.new_session(suite="vm_session")

    def __monitor_session(self, command, *args):
        """
        Connect the qemu monitor session, send command and return output message.
        """
        self.dut.send_expect("nc -U %s" % self.monitor_socket, "(qemu)")

        cmd = command
        for arg in args:
            cmd += " " + str(arg)

        # after quit command, qemu will exit
        if "quit" in cmd:
            self.dut.send_command("%s" % cmd)
            out = self.dut.send_expect(" ", "#")
        else:
            out = self.dut.send_expect("%s" % cmd, "(qemu)", 30)
        self.dut.send_expect("^C", "# ")
        return out

    def pin_threads(self, lcores):
        thread_reg = r"CPU #\d+: thread_id=(\d+)"
        output = self.__monitor_session("info", "cpus")
        threads = re.findall(thread_reg, output)
        if len(threads) <= len(lcores):
            map = list(zip(threads, lcores))
        else:
            self.logger.warning(
                "lcores is less than VM's threads, 1 lcore will pin multiple VM's threads"
            )
            lcore_len = len(lcores)
            for item in threads:
                thread_idx = threads.index(item)
                if thread_idx >= lcore_len:
                    lcore_idx = thread_idx % lcore_len
                    lcores.append(lcores[lcore_idx])
            map = list(zip(threads, lcores))
        for thread, lcore in map:
            self.dut.send_expect("taskset -pc %s %s" % (lcore, thread), "#")

    def connect_vm0(self):
        self.vm0 = QEMUKvm(self.dut, "vm0", self.suite_name)
        self.vm0.net_type = "hostfwd"
        self.vm0.hostfwd_addr = "%s:6000" % self.host_addr
        self.vm0.def_driver = "vfio-pci"
        self.vm0.driver_mode = "noiommu"
        self.wait_vm_net_ready(vm_index=0)
        vm_dut = self.vm0.instantiate_vm_dut(autodetect_topo=False, bind_dev=False)
        if vm_dut:
            return vm_dut
        else:
            return None

    def connect_vm1(self):
        self.vm1 = QEMUKvm(self.dut, "vm1", "vm_hotplug")
        self.vm1.net_type = "hostfwd"
        self.vm1.hostfwd_addr = "%s:6001" % self.host_addr
        self.vm1.def_driver = "vfio-pci"
        self.vm1.driver_mode = "noiommu"
        self.wait_vm_net_ready(vm_index=1)
        vm_dut = self.vm1.instantiate_vm_dut(autodetect_topo=False, bind_dev=False)
        if vm_dut:
            return vm_dut
        else:
            return None

    def wait_vm_net_ready(self, vm_index=0):
        self.vm_net_session = self.dut.new_session(suite="vm_net_session")
        self.start_time = time.time()
        cur_time = time.time()
        time_diff = cur_time - self.start_time
        while time_diff < 120:
            try:
                out = self.vm_net_session.send_expect(
                    "~/QMP/qemu-ga-client --address=/tmp/vm%s_qga0.sock ifconfig"
                    % vm_index,
                    "#",
                )
            except Exception as EnvironmentError:
                pass
            if "10.0.2" in out:
                pos = self.vm0.hostfwd_addr.find(":")
                ssh_key = (
                    "["
                    + self.vm0.hostfwd_addr[:pos]
                    + "]"
                    + self.vm0.hostfwd_addr[pos:]
                )
                os.system("ssh-keygen -R %s" % ssh_key)
                break
            time.sleep(1)
            cur_time = time.time()
            time_diff = cur_time - self.start_time
        self.dut.close_session(self.vm_net_session)

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
        self.dut.send_expect("modprobe ioatdma", "# ")
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % self.cbdma_str, "# ", 30
        )
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=ioatdma  %s" % self.cbdma_str,
            "# ",
            60,
        )

    def send_and_verify(self):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            tgen_input = []
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            pkt = Packet(pkt_type="UDP", pkt_len=frame_size)
            pkt.config_layer("ether", {"dst": "%s" % self.dst_mac})
            pkt.save_pcapfile(self.tester, "%s/vhost.pcap" % self.out_path)
            tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgen_input, 100, None, self.tester.pktgen
            )
            # set traffic option
            traffic_opt = {
                "delay": 5,
                "duration": self.get_suite_cfg()["test_duration"],
            }
            _, pps = self.tester.pktgen.measure_throughput(
                stream_ids=streams, options=traffic_opt
            )
            Mpps = pps / 1000000.0
            self.throughput[frame_size] = Mpps
            linerate = Mpps * 100 / float(self.wirespeed(self.nic, 64, 1))
            results_row = [frame_size]
            results_row.append(Mpps)
            results_row.append(linerate)
            self.result_table_add(results_row)
        self.result_table_print()

    def handle_expected(self):
        """
        Update expected numbers to configurate file: $DTS_CFG_FOLDER/$suite_name.cfg
        """
        if load_global_setting(UPDATE_EXPECTED) == "yes":
            for frame_size in self.frame_sizes:
                self.expected_throughput[frame_size] = round(
                    self.throughput[frame_size], 3
                )

    def handle_results(self):
        """
        results handled process:
        1, save to self.test_results
        2, create test results table
        """
        # save test results to self.test_result
        header = self.table_header
        header.append("Expected Throughput(Mpps)")
        header.append("Status")
        self.result_table_create(self.table_header)
        for frame_size in self.frame_sizes:
            wirespeed = self.wirespeed(self.nic, frame_size, self.nb_ports)
            ret_data = {}
            ret_data[header[0]] = str(frame_size)
            _real = float(self.throughput[frame_size])
            _exp = float(self.expected_throughput[frame_size])
            ret_data[header[1]] = "{:.3f}".format(_real)
            ret_data[header[2]] = "{:.3f}%".format(_real * 100 / wirespeed)
            ret_data[header[3]] = "{:.3f}".format(_exp)
            gap = _exp * -self.gap * 0.01
            if _real > _exp + gap:
                ret_data[header[4]] = "PASS"
            else:
                ret_data[header[4]] = "FAIL"
            self.test_result[frame_size] = deepcopy(ret_data)

        for frame_size in self.test_result.keys():
            table_row = list()
            for i in range(len(header)):
                table_row.append(self.test_result[frame_size][header[i]])
            self.result_table_add(table_row)
        # present test results to screen
        self.result_table_print()
        self.verify(
            "FAIL" not in self.test_result,
            "Excessive gap between test results and expectations",
        )

    def start_vhost_user_testpmd(
        self, cores, param="", eal_param="", ports="", no_pci=False
    ):
        """
        launch the testpmd as virtio with vhost_user
        """
        if no_pci:
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                param=param,
                eal_param=eal_param,
                no_pci=True,
                prefix="vhost",
                fixed_prefix=True,
            )
        else:
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                param=param,
                eal_param=eal_param,
                ports=ports,
                prefix="vhost",
                fixed_prefix=True,
            )

    def start_virtio_user0_testpmd(self, cores, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net0
        """
        self.virtio_user0_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user0",
            fixed_prefix=True,
        )

    def config_vm_ip(self):
        """
        set virtio device IP and run arp protocal
        """
        vm1_intf = self.vm0_dut.ports_info[0]["intf"]
        vm2_intf = self.vm1_dut.ports_info[0]["intf"]
        self.vm0_dut.send_expect(
            "ifconfig %s %s" % (vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm1_dut.send_expect(
            "ifconfig %s %s" % (vm2_intf, self.virtio_ip2), "#", 10
        )
        self.vm0_dut.send_expect(
            "arp -s %s %s" % (self.virtio_ip2, self.virtio_mac2), "#", 10
        )
        self.vm1_dut.send_expect(
            "arp -s %s %s" % (self.virtio_ip1, self.virtio_mac1), "#", 10
        )

    def config_vm_combined(self, combined=1):
        """
        set virtio device combined
        """
        vm1_intf = self.vm0_dut.ports_info[0]["intf"]
        vm2_intf = self.vm1_dut.ports_info[0]["intf"]
        self.vm0_dut.send_expect(
            "ethtool -L %s combined %d" % (vm1_intf, combined), "#", 10
        )
        self.vm1_dut.send_expect(
            "ethtool -L %s combined %d" % (vm2_intf, combined), "#", 10
        )

    def check_ping_between_vms(self):
        ping_out = self.vm0_dut.send_expect(
            "ping {} -c 4".format(self.virtio_ip2), "#", 60
        )
        self.logger.info(ping_out)

    def check_scp_file_valid_between_vms(self, file_size=1024):
        """
        scp file form VM1 to VM2, check the data is valid
        """
        # default file_size=1024K
        data = ""
        for _ in range(file_size * 1024):
            data += random.choice(self.random_string)
        self.vm0_dut.send_expect('echo "%s" > /tmp/payload' % data, "# ")
        # scp this file to vm1
        out = self.vm1_dut.send_command(
            "scp root@%s:/tmp/payload /root" % self.virtio_ip1, timeout=5
        )
        if "Are you sure you want to continue connecting" in out:
            self.vm1_dut.send_command("yes", timeout=3)
        self.vm1_dut.send_command(self.vm0_passwd, timeout=3)
        # get the file info in vm1, and check it valid
        md5_send = self.vm0_dut.send_expect("md5sum /tmp/payload", "# ")
        md5_revd = self.vm1_dut.send_expect("md5sum /root/payload", "# ")
        md5_send = md5_send[: md5_send.find(" ")]
        md5_revd = md5_revd[: md5_revd.find(" ")]
        self.verify(
            md5_send == md5_revd, "the received file is different with send file"
        )

    def start_iperf(self):
        """
        run perf command between to vms
        """
        iperf_server = "iperf -s -i 1"
        iperf_client = "iperf -c {} -i 1 -t 60".format(self.virtio_ip1)
        self.vm0_dut.send_expect("{} > iperf_server.log &".format(iperf_server), "", 10)
        self.vm1_dut.send_expect("{} > iperf_client.log &".format(iperf_client), "", 60)
        time.sleep(60)

    def get_iperf_result(self):
        """
        get the iperf test result
        """
        self.table_header = ["Mode", "[M|G]bits/sec"]
        self.result_table_create(self.table_header)
        self.vm0_dut.send_expect("pkill iperf", "# ")
        self.vm1_dut.session.copy_file_from("%s/iperf_client.log" % self.dut.base_dir)
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
        self.vm0_dut.send_expect("rm iperf_server.log", "#", 10)
        self.vm1_dut.send_expect("rm iperf_client.log", "#", 10)

    def verify_xstats_info_on_vhost(self):
        """
        check both 2VMs can receive and send big packets to each other
        """
        out_tx = self.vhost_user_pmd.execute_cmd("show port xstats 0")
        out_rx = self.vhost_user_pmd.execute_cmd("show port xstats 1")

        tx_info = re.search("tx_q0_size_1519_max_packets:\s*(\d*)", out_tx)
        rx_info = re.search("rx_q0_size_1519_max_packets:\s*(\d*)", out_rx)

        self.verify(
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1518"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1518"
        )

    def mount_tmpfs_for_4k(self, number=1):
        """
        Prepare tmpfs with 4K-pages
        """
        for num in range(number):
            self.dut.send_expect("mkdir /mnt/tmpfs_nohuge{}".format(num), "# ")
            self.dut.send_expect(
                "mount tmpfs /mnt/tmpfs_nohuge{} -t tmpfs -o size=4G".format(num), "# "
            )

    def umount_tmpfs_for_4k(self):
        """
        Prepare tmpfs with 4K-pages
        """
        out = self.dut.send_expect(
            "mount |grep 'mnt/tmpfs' |awk -F ' ' {'print $3'}", "#"
        )
        if out != "":
            mount_points = out.replace("\r", "").split("\n")
        else:
            mount_points = []
        if len(mount_points) != 0:
            for mount_info in mount_points:
                self.dut.send_expect("umount {}".format(mount_info), "# ")

    def test_perf_pvp_split_ring_vhost_async_operation_using_4K_pages_and_cbdma_enable(
        self,
    ):
        """
        Test Case 1: Basic test vhost-user/virtio-user split ring vhost async operation using 4K-pages and cbdma enable
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=1)
        dmas = "txq0@%s;rxq0@%s" % (self.cbdma_list[0], self.cbdma_list[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--no-numa --socket-num=%s " % self.ports_socket
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.cbdma_list:
            ports.append(i)
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )
        self.vhost_user_pmd.execute_cmd("start")
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param
        )
        self.virtio_user0_pmd.execute_cmd("set fwd mac")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_and_verify()
        self.handle_expected()
        self.handle_results()

    def test_perf_pvp_packed_ring_vhost_async_operation_using_4K_pages_and_cbdma_enable(
        self,
    ):
        """
        Test Case 2: Basic test vhost-user/virtio-user packed ring vhost async operation using 4K-pages and cbdma enable
        """
        self.test_target = self.running_case
        self.expected_throughput = self.get_suite_cfg()["expected_throughput"][
            self.test_target
        ]
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=1)
        dmas = "txq0@%s;rxq0@%s" % (self.cbdma_list[0], self.cbdma_list[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net,queues=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--no-numa --socket-num=%s " % self.ports_socket
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.cbdma_list:
            ports.append(i)
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )
        self.vhost_user_pmd.execute_cmd("start")
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,packed_vq=1,queues=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param
        )
        self.virtio_user0_pmd.execute_cmd("set fwd mac")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_and_verify()
        self.handle_expected()
        self.handle_results()

    def test_vm2vm_split_ring_vhost_async_operaiton_test_with_tcp_traffic_using_4k_pages_and_cbdma_enable(
        self,
    ):
        """
        Test Case 3: VM2VM vhost-user/virtio-net split ring vhost async operation test with tcp traffic using 4K-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
        dmas1 = "txq0@%s;rxq0@%s" % (self.cbdma_list[0], self.cbdma_list[0])
        dmas2 = "txq0@%s;rxq0@%s" % (self.cbdma_list[1], self.cbdma_list[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,queues=1,tso=1,dmas=[%s],dma-ring-size=2048'"
            % dmas1
            + " --vdev 'net_vhost1,iface=./vhost-net1,queues=1,tso=1,dmas=[%s],dma-ring-size=2048'"
            % dmas2
        )
        vhost_param = "--nb-cores=2 --txd=1024 --rxd=1024"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=False, queues=1, server=False)
        self.start_vm1(packed=False, queues=1, server=False)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_iperf_result()
        self.verify_xstats_info_on_vhost()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_vm2vm_packed_ring_vhost_async_operaiton_test_with_tcp_traffic_using_4k_pages_and_cbdma_enable(
        self,
    ):
        """
        Test Case 4: VM2VM vhost-user/virtio-net packed ring vhost async operation test with tcp traffic using 4K-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
        dmas1 = "txq0@%s;rxq0@%s" % (self.cbdma_list[0], self.cbdma_list[0])
        dmas2 = "txq0@%s;rxq0@%s" % (self.cbdma_list[1], self.cbdma_list[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,queues=1,tso=1,dmas=[%s],dma-ring-size=2048'"
            % dmas1
            + " --vdev 'net_vhost1,iface=./vhost-net1,queues=1,tso=1,dmas=[%s],dma-ring-size=2048'"
            % dmas2
        )
        vhost_param = "--nb-cores=2 --txd=1024 --rxd=1024"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=True, queues=1, server=False)
        self.start_vm1(packed=True, queues=1, server=False)
        self.config_vm_ip()
        self.check_ping_between_vms()
        self.start_iperf()
        self.get_iperf_result()
        self.verify_xstats_info_on_vhost()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_vm2vm_split_ring_multi_queues_using_4k_pages_and_cbdma_enable(self):
        """
        Test Case 5: vm2vm vhost/virtio-net split ring multi queues using 4K-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=4, allow_diff_socket=True)
        dmas1 = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
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
            "txq7@%s"
            % (
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=8,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=8,dmas=[%s]'"
            % dmas2
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=False, queues=8, server=True)
        self.start_vm1(packed=False, queues=8, server=True)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vhost_user_pmd.quit()
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        dmas2 = (
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
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=8,dmas=[%s],dma-ring-size=1024'"
            % dmas1
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=8,dmas=[%s],dma-ring-size=1024'"
            % dmas2
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=4'"
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=4'"
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.config_vm_combined(combined=4)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vhost_user_pmd.quit()
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=4'"
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=4'"
        )
        vhost_param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=1 --txq=1"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.config_vm_combined(combined=1)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_vm2vm_packed_ring_multi_queues_using_4k_pages_and_cbdma_enable(self):
        """
        Test Case 6: vm2vm vhost/virtio-net packed ring multi queues using 4K-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2, allow_diff_socket=True)
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s"
            % (
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=8,tso=1,dmas=[%s]'"
            % dmas
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % dmas
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=True, queues=8, server=True)
        self.start_vm1(packed=True, queues=8, server=True)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_vm2vm_split_ring_multi_queues_using_1G_and_4k_pages_and_cbdma_enable(self):
        """
        Test Case 7: vm2vm vhost/virtio-net split ring multi queues using 1G/4k-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=4, allow_diff_socket=True)
        dmas = (
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=8,tso=1,dmas=[%s],dma-ring-size=1024'"
            % dmas
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=8,tso=1,dmas=[%s],dma-ring-size=1024'"
            % dmas
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=False, queues=8, server=True)
        self.start_vm1(packed=False, queues=8, server=True)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vhost_user_pmd.quit()
        dmas = (
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=8,tso=1,dmas=[%s]'"
            % dmas
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=8,tso=1,dmas=[%s]'"
            % dmas
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_vm2vm_split_packed_ring_multi_queues_using_1G_and_4k_pages_and_cbdma_enable(
        self,
    ):
        """
        Test Case 8: vm2vm vhost/virtio-net split packed ring multi queues with 1G/4k-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=8, allow_diff_socket=True)
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
                self.cbdma_list[0],
                self.cbdma_list[0],
                self.cbdma_list[1],
                self.cbdma_list[1],
                self.cbdma_list[2],
                self.cbdma_list[2],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
                self.cbdma_list[3],
            )
        )
        dmas2 = (
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
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[4],
                self.cbdma_list[5],
                self.cbdma_list[5],
                self.cbdma_list[6],
                self.cbdma_list[6],
                self.cbdma_list[7],
                self.cbdma_list[7],
                self.cbdma_list[7],
                self.cbdma_list[7],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=./vhost-net0,client=1,queues=8,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=./vhost-net1,client=1,queues=8,dmas=[%s]'"
            % dmas2
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=False, queues=8, server=True)
        self.start_vm1(packed=True, queues=8, server=True)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.virtio_user0_pmd.quit()
        self.vhost_user_pmd.quit()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "# ")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf /tmp/vhost-net*", "# ")
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.umount_tmpfs_for_4k()
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user0)

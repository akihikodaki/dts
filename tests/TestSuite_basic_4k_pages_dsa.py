# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import os
import random
import re
import string
import time

from framework.config import VirtConf
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.qemu_kvm import QEMUKvm
from framework.settings import CONFIG_ROOT_PATH, HEADER_SIZE, get_host_ip
from framework.test_case import TestCase

from .virtio_common import dsa_common as DC


class TestBasic4kPagesDsa(TestCase):
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
        self.virtio0_core_list = self.cores_list[9:14]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.number_of_ports = 1
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.virtio_mac = "00:01:02:03:04:05"
        self.vm_num = 2
        self.virtio_ip1 = "1.1.1.1"
        self.virtio_ip2 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.virtio_mac2 = "52:54:00:00:00:02"
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.random_string = string.ascii_letters + string.digits
        self.addr = str(self.dut.get_ip_address())
        self.host_addr = get_host_ip(self.addr).split(":")[0]
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["tcp"]
        self.DC = DC(self)

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

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "# ")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf /root/dpdk/vhost-net*", "# ")
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)
        self.vm_dut = []
        self.vm = []
        self.packed = False

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
        self.vm1_dut = self.connect_vm1()
        self.verify(self.vm1_dut is not None, "vm start fail")
        self.vm_session = self.vm1_dut.new_session(suite="vm_session")

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

    def send_imix_and_verify(self, mode):
        """
        Send imix packet with packet generator and verify
        """
        frame_sizes = [64, 128, 256, 512, 1024, 1518]
        tgenInput = []
        for frame_size in frame_sizes:
            payload_size = frame_size - self.headers_size
            port = self.tester.get_local_port(self.dut_ports[0])
            fields_config = {
                "ip": {
                    "src": {"action": "random"},
                },
            }
            pkt = Packet()
            pkt.assign_layers(["ether", "ipv4", "tcp", "raw"])
            pkt.config_layers(
                [
                    ("ether", {"dst": "%s" % self.virtio_mac}),
                    ("ipv4", {"src": "1.1.1.1"}),
                    ("raw", {"payload": ["01"] * int("%d" % payload_size)}),
                ]
            )
            pkt.save_pcapfile(
                self.tester,
                "%s/%s_%s.pcap" % (self.out_path, self.suite_name, frame_size),
            )
            tgenInput.append(
                (
                    port,
                    port,
                    "%s/%s_%s.pcap" % (self.out_path, self.suite_name, frame_size),
                )
            )

        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgenInput, 100, fields_config, self.tester.pktgen
        )
        bps, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
        Mpps = pps / 1000000.0
        Mbps = bps / 1000000.0
        self.verify(
            Mbps > 0,
            f"{self.running_case} can not receive packets of frame size {frame_sizes}",
        )
        bps_linerate = self.wirespeed(self.nic, 64, 1) * 8 * (64 + 20)
        throughput = Mbps * 100 / float(bps_linerate)
        results_row = ["imix"]
        results_row.append(mode)
        results_row.append(Mpps)
        results_row.append(throughput)
        self.result_table_add(results_row)

    def start_vhost_user_testpmd(
        self,
        cores,
        eal_param="",
        param="",
        no_pci=False,
        ports="",
        port_options="",
    ):
        """
        launch the testpmd as virtio with vhost_user
        """
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
            "ping {} -c 4".format(self.virtio_ip2), "#", 20
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
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1522"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1522"
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

    def check_packets_of_vhost_each_queue(self, queues):
        self.vhost_user_pmd.execute_cmd("show port stats all")
        out = self.vhost_user_pmd.execute_cmd("stop")
        self.logger.info(out)
        for queue in range(queues):
            reg = "Queue= %d" % queue
            index = out.find(reg)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(
                rx_packets > 0 and tx_packets > 0,
                "The queue {} rx-packets or tx-packets is 0 about ".format(queue)
                + "rx-packets: {}, tx-packets: {}".format(rx_packets, tx_packets),
            )

    def test_perf_pvp_split_ring_multi_queues_with_4k_pages_and_dsa_dpdk_driver(
        self,
    ):
        """
        Test Case 1: PVP split ring multi-queues with 4K-pages and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--no-huge -m 1024 --vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'"
            % dmas
        )
        vhost_param = (
            "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        ports = [self.dut.ports_info[0]["pci"]]
        for i in dsas:
            ports.append(i)
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=1,queues=8,server=1"
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="split ring inorder mergeable with 4k page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="split ring inorder mergeable with 4k page restart vhost"
        )

        self.vhost_user_pmd.quit()
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
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
            )
        )

        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in dsas:
            ports.append(i)
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="split ring inorder mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="split ring inorder mergeable with 1G page restart vhost"
        )

        self.virtio_user0_pmd.quit()
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=0,queues=8,server=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="split ring mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="split ring mergeable with 1G page restart vhost"
        )
        self.result_table_print()

    def test_perf_pvp_packed_ring_multi_queues_with_4k_pages_and_dsa_dpdk_driver(
        self,
    ):
        """
        Test Case 2: PVP packed ring multi-queues with 4K-pages and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--no-huge -m 1024 --vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'"
            % dmas
        )
        vhost_param = (
            "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        ports = [self.dut.ports_info[0]["pci"]]
        for i in dsas:
            ports.append(i)
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1"
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="packed ring inorder mergeable with 4k page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="packed ring inorder mergeable with 4k page restart vhost"
        )

        self.vhost_user_pmd.quit()
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
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        ports = [self.dut.ports_info[0]["pci"]]
        for i in dsas:
            ports.append(i)
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options=port_options,
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="packed ring inorder mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="packed ring inorder mergeable with 1G page restart vhost"
        )

        self.virtio_user0_pmd.quit()
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=0,packed_vq=1,queues=8,server=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="packed ring mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="packed ring mergeable with 1G page restart vhost"
        )
        self.result_table_print()

    def test_vm2vm_split_ring_vhost_user_virtio_net_4k_pages_and_dsa_dpdk_driver_test_with_tcp_traffic(
        self,
    ):
        """
        Test Case 3: VM2VM split ring vhost-user/virtio-net 4K-pages and dsa dpdk driver test with tcp traffic
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s-q0;rxq0@%s-q0" % (dsas[0], dsas[0])
        dmas2 = "txq0@%s-q1;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--no-huge -m 1024 "
            + "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'" % dmas2
        )
        vhost_param = (
            " --nb-cores=2 --txd=1024 --rxd=1024 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
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

    def test_vm2vm_packed_ring_vhost_user_virtio_net_4k_pages_and_dsa_dpdk_driver_test_with_tcp_traffic(
        self,
    ):
        """
        Test Case 4: VM2VM packed ring vhost-user/virtio-net 4K-pages and dsa dpdk driver test with tcp traffic
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        dmas2 = "txq0@%s-q0;rxq0@%s-q1" % (dsas[0], dsas[0])
        vhost_eal_param = (
            "--no-huge -m 1024 "
            + "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'" % dmas2
        )
        vhost_param = (
            " --nb-cores=2 --txd=1024 --rxd=1024 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
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

    def test_vm2vm_vhost_virtio_net_split_packed_ring_multi_queues_with_1G_4k_pages_and_dsa_dpdk_driver(
        self,
    ):
        """
        Test Case 5: VM2VM vhost/virtio-net split packed ring multi queues with 1G/4k-pages and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        dmas2 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[%s]'" % dmas2
        )
        vhost_param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=False, queues=8, server=False)
        self.start_vm1(packed=True, queues=8, server=False)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_vm2vm_vhost_virtio_net_split_ring_multi_queues_with_1G_4k_pages_and_dsa_dpdk_driver(
        self,
    ):
        """
        Test Case 6: VM2VM vhost/virtio-net split ring multi queues with 1G/4k-pages and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        dmas2 = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
                dsas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas2
        )
        vhost_param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
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
        dmas1 = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q0;"
            "txq3@%s-q1;"
            "rxq0@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q0;"
            "rxq3@%s-q1"
            % (
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
            )
        )
        dmas2 = (
            "txq0@%s-q0;"
            "txq1@%s-q1;"
            "txq2@%s-q0;"
            "txq3@%s-q1;"
            "rxq0@%s-q0;"
            "rxq1@%s-q1;"
            "rxq2@%s-q0;"
            "rxq3@%s-q1"
            % (
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
                dsas[0],
                dsas[0],
                dsas[1],
                dsas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas2
        )
        vhost_param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
        port_options = {
            dsas[0]: "max_queues=2",
            dsas[1]: "max_queues=2",
        }
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=dsas,
            port_options=port_options,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.config_vm_combined(combined=4)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_perf_pvp_split_ring_multi_queues_with_4k_pages_and_dsa_kernel_driver(self):
        """
        Test Case 7: PVP split ring multi-queues with 4K-pages and dsa kernel driver
        """
        self.DC.create_wq(wq_num=4, dsa_idxs=[0, 1])
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "rxq2@wq1.0;"
            "rxq3@wq1.0;"
            "rxq4@wq1.1;"
            "rxq5@wq1.1;"
            "rxq6@wq1.1;"
            "rxq7@wq1.1"
        )
        vhost_eal_param = (
            "--no-huge -m 1024 --vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'"
            % dmas
        )
        vhost_param = (
            "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options="",
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=1,queues=8,server=1"
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="split ring inorder mergeable with 4k page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="split ring inorder mergeable with 4k page restart vhost"
        )

        self.vhost_user_pmd.quit()
        dmas = (
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
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options="",
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="split ring inorder mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="split ring inorder mergeable with 1G page restart vhost"
        )

        self.virtio_user0_pmd.quit()
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=0,queues=8,server=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="split ring mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="split ring mergeable with 1G page restart vhost"
        )
        self.result_table_print()

    def test_perf_pvp_packed_ring_multi_queues_with_4k_pages_and_dsa_kernel_driver(
        self,
    ):
        """
        Test Case 8: PVP packed ring multi-queues with 4K-pages and dsa kernel driver
        """
        self.DC.create_wq(wq_num=4, dsa_idxs=[0, 1])
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "rxq2@wq1.0;"
            "rxq3@wq1.0;"
            "rxq4@wq1.1;"
            "rxq5@wq1.1;"
            "rxq6@wq1.1;"
            "rxq7@wq1.1"
        )
        vhost_eal_param = (
            "--no-huge -m 1024 --vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'"
            % dmas
        )
        vhost_param = (
            "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        ports = [self.dut.ports_info[0]["pci"]]
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options="",
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")

        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=1,packed_vq=1,queues=8,server=1"
        virtio_param = "--nb-cores=4 --txq=8 --rxq=8 --txd=1024 --rxd=1024"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="packed ring inorder mergeable with 4k page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="packed ring inorder mergeable with 4k page restart vhost"
        )

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "txq6@wq0.1;"
            "txq7@wq0.1;"
            "rxq0@wq0.0;"
            "rxq1@wq0.0;"
            "rxq2@wq0.0;"
            "rxq3@wq0.0;"
            "rxq4@wq0.1;"
            "rxq5@wq0.1;"
            "rxq6@wq0.1;"
            "rxq7@wq0.1"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --txd=1024 --rxd=1024 --txq=8 --rxq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
            port_options="",
        )
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="packed ring inorder mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="packed ring inorder mergeable with 1G page restart vhost"
        )

        self.virtio_user0_pmd.quit()
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net0,mrg_rxbuf=1,in_order=0,packed_vq=1,queues=8,server=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
        )
        self.virtio_user0_pmd.execute_cmd("set fwd csum")
        self.virtio_user0_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(mode="packed ring mergeable with 1G page")
        self.check_packets_of_vhost_each_queue(queues=8)

        self.vhost_user_pmd.execute_cmd("start")
        self.send_imix_and_verify(
            mode="packed ring mergeable with 1G page restart vhost"
        )
        self.result_table_print()

    def test_vm2vm_split_ring_vhost_user_virtio_net_4k_pages_and_dsa_kernel_driver_test_with_tcp_traffic(
        self,
    ):
        """
        Test Case 9: VM2VM split ring vhost-user/virtio-net 4K-pages and dsa kernel driver test with tcp traffic
        """
        self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        dmas1 = "txq0@wq0.0;rxq0@wq0.1"
        dmas2 = "txq0@wq0.2;rxq0@wq0.3"
        vhost_eal_param = (
            "--no-huge -m 1024 "
            + "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'" % dmas2
        )
        vhost_param = (
            " --nb-cores=2 --txd=1024 --rxd=1024 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
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

    def test_vm2vm_packed_ring_vhost_user_virtio_net_4k_pages_and_dsa_kernel_driver_test_with_tcp_traffic(
        self,
    ):
        """
        Test Case 10: VM2VM packed ring vhost-user/virtio-net 4K-pages and dsa kernel driver test with tcp traffic
        """
        self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas1 = "txq0@wq0.0;rxq0@wq0.0"
        dmas2 = "txq0@wq0.1;rxq0@wq0.1"
        vhost_eal_param = (
            "--no-huge -m 1024 "
            + "--vdev 'net_vhost0,iface=vhost-net0,queues=1,tso=1,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,tso=1,dmas=[%s]'" % dmas2
        )
        vhost_param = (
            " --nb-cores=2 --txd=1024 --rxd=1024 --no-numa --socket-num=%d"
            % self.ports_socket
        )
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
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

    def test_vm2vm_vhost_virtio_net_split_packed_ring_multi_queues_with_1G_4k_pages_and_dsa_kenel_driver(
        self,
    ):
        """
        Test Case 11: VM2VM vhost/virtio-net split packed ring multi queues with 1G/4k-pages and dsa kernel driver
        """
        self.DC.create_wq(wq_num=4, dsa_idxs=[0, 1])
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "rxq2@wq1.0;"
            "rxq3@wq1.0;"
            "rxq4@wq1.1;"
            "rxq5@wq1.1;"
            "rxq6@wq1.1;"
            "rxq7@wq1.1"
        )
        dmas2 = (
            "txq0@wq0.2;"
            "txq1@wq0.2;"
            "txq2@wq0.2;"
            "txq3@wq0.2;"
            "txq4@wq0.3;"
            "txq5@wq0.3;"
            "rxq2@wq1.2;"
            "rxq3@wq1.2;"
            "rxq4@wq1.3;"
            "rxq5@wq1.3;"
            "rxq6@wq1.3;"
            "rxq7@wq1.3"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,dmas=[%s]'" % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,dmas=[%s]'" % dmas2
        )
        vhost_param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
        )
        self.vhost_user_pmd.execute_cmd("start")

        self.start_vm0(packed=False, queues=8, server=False)
        self.start_vm1(packed=True, queues=8, server=False)
        self.config_vm_ip()
        self.config_vm_combined(combined=8)
        self.check_ping_between_vms()
        self.check_scp_file_valid_between_vms()
        self.start_iperf()
        self.get_iperf_result()

        self.vm0.stop()
        self.vm1.stop()
        self.vhost_user_pmd.quit()

    def test_vm2vm_vhost_virtio_net_split_ring_multi_queues_with_1G_4k_pages_and_dsa_kernel_driver(
        self,
    ):
        """
        Test Case 12: VM2VM vhost/virtio-net split ring multi queues with 1G/4k-pages and dsa kernel driver
        """
        self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "rxq2@wq1.0;"
            "rxq3@wq1.0;"
            "rxq4@wq1.1;"
            "rxq5@wq1.1;"
            "rxq6@wq1.1;"
            "rxq7@wq1.1"
        )
        dmas2 = (
            "txq0@wq0.0;"
            "txq1@wq0.0;"
            "txq2@wq0.0;"
            "txq3@wq0.0;"
            "txq4@wq0.1;"
            "txq5@wq0.1;"
            "rxq2@wq1.0;"
            "rxq3@wq1.0;"
            "rxq4@wq1.1;"
            "rxq5@wq1.1;"
            "rxq6@wq1.1;"
            "rxq7@wq1.1"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas2
        )
        vhost_param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=8 --txq=8"
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
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
        dmas1 = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "rxq0@wq0.0;"
            "rxq1@wq0.1;"
            "rxq2@wq0.2;"
            "rxq3@wq0.3"
        )
        dmas2 = (
            "txq0@wq0.0;"
            "txq1@wq0.1;"
            "txq2@wq0.2;"
            "txq3@wq0.3;"
            "rxq0@wq0.0;"
            "rxq1@wq0.1;"
            "rxq2@wq0.2;"
            "rxq3@wq0.3"
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas1
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=8,client=1,tso=1,dmas=[%s]'"
            % dmas2
        )
        vhost_param = " --nb-cores=4 --txd=1024 --rxd=1024 --rxq=4 --txq=4"
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

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.umount_tmpfs_for_4k()
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user0)

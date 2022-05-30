# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import os
import re
import time

from framework.config import UserConf
from framework.pmd_output import PmdOutput
from framework.settings import CONFIG_ROOT_PATH
from framework.test_case import TestCase


class Testiavf_package_and_driver_check(TestCase):
    def set_up_all(self):
        self.verify(
            self.nic
            in ["ICE_100G-E810C_QSFP", "ICE_25G-E810_XXV_SFP", "ICE_25G-E810C_SFP"],
            "NIC Unsupported: " + str(self.nic),
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.used_dut_port = self.dut_ports[0]
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.PF_QUEUE = 16

        conf_file = os.path.join(CONFIG_ROOT_PATH, "iavf_driver_package.cfg")
        conf_peer = UserConf(conf_file)
        conf_session = conf_peer.conf._sections["suite"]
        self.driverPath_latest = conf_session["ice_driver_file_location_latest"]
        self.driverPath_old = conf_session["ice_driver_ice_10_rc17_driver"]
        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_p0 = self.tester.get_interface(localPort0)
        self.tester.send_expect("ifconfig %s -promisc" % self.tester_p0, "#")

        self.dut_p0_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.tester_p0_mac = self.tester.get_mac(localPort0)
        self.dut_testpmd = PmdOutput(self.dut)

        self.pkg_file1 = "/lib/firmware/intel/ice/ddp/ice.pkg"
        self.pkg_file2 = "/lib/firmware/updates/intel/ice/ddp/ice.pkg"
        out = self.dut.send_expect("ls %s" % self.pkg_file1, "#")
        self.verify(
            "No such file or directory" not in out,
            "Cannot find %s, please check you system/driver." % self.pkg_file1,
        )
        out = self.dut.send_expect("ls %s" % self.pkg_file2, "#")
        self.verify(
            "No such file or directory" not in out,
            "Cannot find %s, please check you system/driver." % self.pkg_file2,
        )
        self.backup_recover_ice_pkg("backup")

    def set_up(self):
        pass

    def backup_recover_ice_pkg(self, flag="backup"):
        """
        if backup == true: backup /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg to /opt/ice.pkg_backup
        else: recover /opt/ice.pkg_backup to /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg
        """
        backup_file = "/opt/ice.pkg_backup"
        if flag == "backup":
            self.dut.send_expect("\cp %s %s" % (self.pkg_file1, backup_file), "#")
        else:
            self.dut.send_expect("\cp %s %s" % (backup_file, self.pkg_file1), "#")
            self.dut.send_expect("\cp %s %s" % (backup_file, self.pkg_file2), "#")

    def use_correct_ice_pkg(self, flag="true"):
        """
        if flag == true: use correct /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg
        else: touch a wrong /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg
        """
        if flag == "true":
            self.backup_recover_ice_pkg("recover")
        else:
            self.dut.send_expect("rm -rf %s" % self.pkg_file1, "#")
            self.dut.send_expect("touch %s" % self.pkg_file1, "#")
            self.dut.send_expect("rm -rf %s" % self.pkg_file2, "#")
            self.dut.send_expect("touch %s" % self.pkg_file2, "#")

    def start_testpmd(self, ice_pkg="true", safe_mode_support="false"):
        self.eal_param = ""
        if safe_mode_support == "true":
            for i in range(len(self.dut_ports)):
                self.eal_param = (
                    self.eal_param
                    + "-a %s,safe-mode-support=1 " % self.dut.ports_info[i]["pci"]
                )
        out = self.dut_testpmd.start_testpmd(
            "all",
            "--nb-cores=8 --rxq=%s --txq=%s --port-topology=chained"
            % (self.PF_QUEUE, self.PF_QUEUE),
            eal_param=self.eal_param,
        )
        if ice_pkg == "false":
            if safe_mode_support == "true":
                error_messages = [
                    "ice_load_pkg(): failed to allocate buf of size 0 for package",
                    "ice_dev_init(): Failed to load the DDP package,Entering Safe Mode",
                    "ice_init_rss(): RSS is not supported in safe mode",
                ]
            if safe_mode_support == "false":
                error_messages = [
                    "ice_load_pkg(): failed to allocate buf of size 0 for package",
                    "ice_dev_init(): Failed to load the DDP package,Use safe-mode-support=1 to enter Safe Mode",
                ]
            for error_message in error_messages:
                self.verify(
                    error_message in out,
                    "There should be error messages in out: %s" % out,
                )
        self.dut_testpmd.execute_cmd("set promisc all off")
        self.dut_testpmd.execute_cmd("set verbose 1")

    def number_of_packets(self, iface):
        """
        By reading the file generated by tcpdump it counts how many packets were
        forwarded by the sample app and received in the self.tester. The sample app
        will add a known MAC address for the test to look for.
        """
        command = (
            "tcpdump -A -nn -e -v -r tcpdump_{iface}.pcap 2>/dev/null | "
            + 'grep -c "IPv4"'
        )
        return self.tcpdump_command(command.format(**locals()))

    def send_packet(self, tran_type, flag):
        """
        Sends packets.
        """
        self.loading_size = 30
        self.tester.scapy_foreground()
        if tran_type == "ipv4-other":
            for i in range(1):
                packet = (
                    r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/("X"*%s)], iface="%s")'
                    % (
                        self.dut_p0_mac,
                        self.tester_p0_mac,
                        i + 1,
                        i + 2,
                        self.loading_size,
                        self.tester_p0,
                    )
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "ipv4-tcp":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1024,dport=1024)], iface="%s")'
                    % (
                        self.dut_p0_mac,
                        self.tester_p0_mac,
                        i + 1,
                        i + 2,
                        self.tester_p0,
                    )
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "ipv4-udp":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1024,dport=1024)], iface="%s")'
                    % (
                        self.dut_p0_mac,
                        self.tester_p0_mac,
                        i + 1,
                        i + 2,
                        self.tester_p0,
                    )
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "ipv4-sctp":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1024,dport=1024)], iface="%s")'
                    % (
                        self.dut_p0_mac,
                        self.tester_p0_mac,
                        i + 1,
                        i + 2,
                        self.tester_p0,
                    )
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "ipv6-tcp":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="%s")/IPv6(src="::%d", dst="::%d")/TCP(sport=1024,dport=1024)], iface="%s")'
                    % (
                        self.dut_p0_mac,
                        self.tester_p0_mac,
                        i + 1,
                        i + 2,
                        self.tester_p0,
                    )
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "ipv6-udp":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="%s")/IPv6(src="::%d", dst="::%d")/UDP(sport=1024,dport=1024)], iface="%s")'
                    % (
                        self.dut_p0_mac,
                        self.tester_p0_mac,
                        i + 1,
                        i + 2,
                        self.tester_p0,
                    )
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "ipv6-sctp":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="%s")/IPv6(src="::%d", dst="::%d",nh=132)/SCTP(sport=1024,dport=1024)], iface="%s")'
                    % (
                        self.dut_p0_mac,
                        self.tester_p0_mac,
                        i + 1,
                        i + 2,
                        self.tester_p0,
                    )
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        else:
            print("\ntran_type error!\n")

        self.verifyResult(tran_type=tran_type, flag=flag)

    def verifyResult(self, tran_type, flag):
        """
        if flag == true: all packets should enter different queues of port 0
        else: all packets enter queue 0 of port 0
        """
        if tran_type == "ipv4-other":
            self.tcpdump_stop_sniff()
            p0_stats = self.number_of_packets(self.tester_p0)
            p1_stats = self.number_of_packets(self.tester_p1)
            self.verify(p0_stats == p1_stats, "tester p0 and p1: packet number match")
        else:
            out = self.dut.get_session_output()
            queue_list = []
            lines = out.split("\r\n")
            for line in lines:
                line = line.strip()
                if len(line) != 0 and line.startswith(("port 0/queue ",)):
                    for item in line.split(":"):
                        item = item.strip()
                        if item.startswith("port 0/queue "):
                            queue_id = item.split(" ", 2)[-1]
                            queue_list.append(queue_id)
            print(list(set(queue_list)))
            if flag == "true":
                self.verify(
                    len(list(set(queue_list))) > 1,
                    "All packets enter the same queue: %s" % queue_list,
                )
            else:
                self.verify(
                    len(list(set(queue_list))) == 1
                    and int(list(set(queue_list))[0]) == 0,
                    "All packets should enter queue 0, but entered %s" % queue_list,
                )

    def test_invalid_pkg_in_iavf(self):
        """
        use wrong ice.pkg and start testpmd without "safe-mode-suppor", no port is loaded in testpmd
        """
        self.dut.bind_interfaces_linux("ice")
        self.use_correct_ice_pkg(flag="false")
        # import pdb
        # pdb.set_trace()
        self.dut.send_expect("rmmod -f ice", "#")
        self.dut.send_expect("insmod %s" % self.driverPath_latest, "#")
        # self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2)
        self.dut.bind_interfaces_linux("ice")
        self.used_dut_port_pci = self.dut.ports_info[self.used_dut_port]["port"].pci
        cmd = "echo 2 > /sys/bus/pci/devices/%s/sriov_numvfs" % self.used_dut_port_pci
        out = self.dut.send_expect(cmd, "#", 60)
        # import pdb
        # pdb.set_trace()
        self.verify(
            "write error: Operation not supported" in out,
            "There should be '%s' in out: %s"
            % ("write error: Operation not supported", out),
        )

    def test_invalid_driver_in_iavf(self):
        """
        use wrong ice.pkg and start testpmd without "safe-mode-suppor", no port is loaded in testpmd
        """
        self.dut.bind_interfaces_linux("ice")
        self.use_correct_ice_pkg("true")
        self.dut.send_expect("rmmod -f ice", "#")
        self.dut.send_expect("insmod %s" % self.driverPath_old, "#")
        self.used_dut_port_pci = self.dut.ports_info[self.used_dut_port]["port"].pci

        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]

        for port in self.sriov_vfs_port:
            port.bind_driver("vfio-pci")

        testpmdcmd = (
            self.dut.apps_name["test-pmd"]
            + "-l 6-9 -n 4  --file-prefix=vf -- -i --rxq=4 --txq=4  --nb-cores=2"
        )
        self.dut_testpmd.execute_cmd(testpmdcmd)
        out = self.dut_testpmd.execute_cmd(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end"
        )
        self.verify(
            "iavf_flow_create(): Failed to create flow" in out,
            "There should be '%s' in out: %s"
            % ("iavf_flow_create(): Failed to create flow", out),
        )

    def copy_specify_ice_pkg(self, pkg_ver):
        """
        Copy 2 different ``ice-xxx.pkg`` from dts/dep to dut /tmp/
        pkg_files = ['ice-1.3.4.0.pkg', 'ice-1.3.10.0.pkg']
        """
        dst = "/tmp"
        pkg_file = "ice-%s.pkg" % pkg_ver
        src_file = r"./dep/%s" % pkg_file
        self.dut.session.copy_file_to(src_file, dst)

    def generate_delete_specify_pkg(self, pkg_ver, sn, key="true"):
        self.dut.send_expect("rm -rf /lib/firmware/intel/ice/ddp/ice-%s.pkg" % sn, "#")
        if key == "true":
            self.dut.send_expect(
                "\cp /tmp/ice-%s.pkg /lib/firmware/intel/ice/ddp/ice-%s.pkg"
                % (pkg_ver, sn),
                "#",
            )

    def tear_down(self):
        self.dut_testpmd.quit()

    def tear_down_all(self):
        """
        After test, recover the default ice.pkg
        """
        self.backup_recover_ice_pkg("recover")

# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import os
import random
import re
import string
import time


class basic_common(object):
    def __init__(self, test_case):
        self.test_case = test_case
        self.logger = test_case.logger
        self.verify = self.test_case.verify
        self.dut_ip = self.test_case.dut.get_ip_address()
        self.tester_ip = self.test_case.tester.get_ip_address()
        self.dut_passwd = self.test_case.dut.get_password()
        self.tester_passwd = self.test_case.tester.get_password()
        self.random_string = string.ascii_letters + string.digits
        self.vm0_ip = "1.1.1.1"
        self.vm1_ip = "1.1.1.2"
        self.vm0_mac = "52:54:00:00:00:01"
        self.vm1_mac = "52:54:00:00:00:02"

    def check_2M_env(self):
        out = self.test_case.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def config_2_vms_ip(self):
        """
        config VM interface IP and run arp protocal
        """
        vm0_intf = self.test_case.vm_dut[0].ports_info[0]["intf"]
        vm1_intf = self.test_case.vm_dut[1].ports_info[0]["intf"]
        self.test_case.vm_dut[0].send_expect(
            "ifconfig %s %s" % (vm0_intf, self.vm0_ip), "#"
        )
        self.test_case.vm_dut[1].send_expect(
            "ifconfig %s %s" % (vm1_intf, self.vm1_ip), "#"
        )
        self.test_case.vm_dut[0].send_expect(
            "arp -s %s %s" % (self.vm1_ip, self.vm1_mac), "#"
        )
        self.test_case.vm_dut[1].send_expect(
            "arp -s %s %s" % (self.vm0_ip, self.vm0_mac), "#"
        )

    def config_2_vms_combined(self, combined=1):
        """
        config 2 VM interface combined
        """
        vm0_intf = self.test_case.vm_dut[0].ports_info[0]["intf"]
        vm1_intf = self.test_case.vm_dut[1].ports_info[0]["intf"]
        self.test_case.vm_dut[0].send_expect(
            "ethtool -L %s combined %d" % (vm0_intf, combined), "#"
        )
        self.test_case.vm_dut[1].send_expect(
            "ethtool -L %s combined %d" % (vm1_intf, combined), "#"
        )

    def check_ping_between_2_vms(self):
        """
        check ICMP request and response between 2 VMs
        """
        out = self.test_case.vm_dut[0].send_expect(
            "ping {} -c 4".format(self.vm1_ip), "#"
        )
        self.logger.info(out)

    def check_scp_file_between_2_vms(self, file_size=10):
        """
        check scp file request and response between 2 VMs
        """
        # generate random string file on tester
        data = ""
        for _ in range(file_size * 1024 * 1024):
            data += random.choice(self.random_string)
        fp = open("/tmp/payload", "w")
        fp.write(data)
        fp.close()

        # scp file from tester on VM0
        out = self.test_case.vm_dut[0].send_command(
            "scp root@%s:/tmp/payload /tmp" % self.tester_ip, timeout=5
        )
        if "Are you sure you want to continue connecting" in out:
            self.test_case.vm_dut[0].send_command("yes", timeout=3)
        self.test_case.vm_dut[0].send_command(self.tester_passwd, timeout=3)

        # scp file from VM0 on VM1
        out = self.test_case.vm_dut[1].send_command(
            "scp root@%s:/tmp/payload /tmp" % self.vm0_ip, timeout=5
        )
        if "Are you sure you want to continue connecting" in out:
            self.test_case.vm_dut[1].send_command("yes", timeout=3)
        self.test_case.vm_dut[1].send_command(self.test_case.vm[0].password, timeout=3)

        # verify the file on VM0 and VM1's MD5 value is same or not
        md5_send = self.test_case.vm_dut[0].send_expect("md5sum /tmp/payload", "# ")
        md5_revd = self.test_case.vm_dut[1].send_expect("md5sum /tmp/payload", "# ")
        md5_send = md5_send[: md5_send.find(" ")]
        md5_revd = md5_revd[: md5_revd.find(" ")]
        self.verify(
            md5_send == md5_revd, "the received file is different with send file"
        )

    def run_iperf_test_between_2_vms(self):
        """
        run iperf test between 2 VMs
        """
        server_cmd = "iperf -s -i 1"
        client_cmd = "iperf -c {} -i 1 -t 60".format(self.vm0_ip)
        self.test_case.vm_dut[0].send_expect(
            "{} > iperf_server.log &".format(server_cmd), ""
        )
        self.test_case.vm_dut[1].send_expect(
            "{} > iperf_client.log &".format(client_cmd), ""
        )
        time.sleep(60)

    def check_iperf_result_between_2_vms(self):
        """
        check iperf test result between 2 VMs
        """
        self.test_case.vm_dut[0].send_expect("pkill iperf", "# ")
        self.test_case.vm_dut[1].session.copy_file_from(
            "%s/iperf_client.log" % self.test_case.dut.base_dir
        )
        fp = open("./iperf_client.log")
        fmsg = fp.read()
        fp.close()
        # remove the server report info from msg
        index = fmsg.find("Server Report")
        if index != -1:
            fmsg = fmsg[:index]
        iperfdata = re.compile("\S*\s*[M|G]bits/sec").findall(fmsg)
        # the last data of iperf is the ave data from 0-30 sec
        self.logger.info("The iperf data between vms is %s" % iperfdata[-1])
        self.verify(len(iperfdata) != 0, "The iperf data between to vms is 0")
        self.verify(
            iperfdata[-1].split()[-1] == "Gbits/sec",
            "The iperf data between can't reach Gbits/sec",
        )
        # rm the iperf log file in vm
        self.test_case.vm_dut[0].send_expect("rm iperf_server.log", "#")
        self.test_case.vm_dut[1].send_expect("rm iperf_client.log", "#")


class cbdma_common(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def get_all_cbdma_pci(self):
        """
        Get all the CBDMA device PCI of DUT.
        :return: [0000:00:04.0, 0000:00:04.1, 0000:00:04.2, 0000:00:04.3]
        """
        cbdma_pci = []
        out = self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "#"
        )
        info = out.split("\n")
        for item in info:
            pci = re.search("\s*(0000:\S*:\d*.\d*)", item)
            if pci is not None:
                cbdma_pci.append(pci.group(1))
        return cbdma_pci

    def bind_cbdma_to_dpdk(self, cbdma_number, driver_name="vfio-pci", socket=-1):
        """
        Bind CBDMA device to driver
        :param cbdma_number: number of CBDMA device to be bind.
        :param driver_name: driver name, like `vfio-pci`.
        :param socket: socket id: like 0 or 1, if socket=-1, use all the CBDMA deveice no matter on which socket.
        :return: bind_cbdma_list, like [0000:00:04.0, 0000:00:04.1]
        """
        cbdma_list = []
        cbdma_pci = self.get_all_cbdma_pci()
        for pci in cbdma_pci:
            addr_array = pci.split(":")
            domain_id, bus_id, devfun_id = addr_array[0], addr_array[1], addr_array[2]
            cur_socket = self.test_case.dut.send_expect(
                "cat /sys/bus/pci/devices/%s\:%s\:%s/numa_node"
                % (domain_id, bus_id, devfun_id),
                "# ",
                alt_session=True,
            )
            if socket != -1:
                if int(cur_socket) == socket:
                    cbdma_list.append(pci)
            else:
                cbdma_list.append(pci)
        bind_cbdma_list = cbdma_list[0:cbdma_number]
        bind_cbdma_string = " ".join(bind_cbdma_list)
        self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (driver_name, bind_cbdma_string),
            "# ",
            60,
        )
        return bind_cbdma_list

    def bind_all_cbdma_to_kernel(self):
        """
        Check the CBDMA device is bind to kernel driver or not, if not bind to kernel driver, then bind to kernel driver.
        """
        cbdma_pci = self.get_all_cbdma_pci()
        for pci in cbdma_pci:
            addr_array = pci.split(":")
            domain_id, bus_id, devfun_id = addr_array[0], addr_array[1], addr_array[2]
            out = self.test_case.dut.send_expect(
                "cat /sys/bus/pci/devices/%s\:%s\:%s/uevent"
                % (domain_id, bus_id, devfun_id),
                "# ",
                alt_session=True,
            )
            rexp = r"DRIVER=(.+?)\r"
            pattern = re.compile(rexp)
            match = pattern.search(out)
            if not match:
                driver = None
            else:
                driver = match.group(1)
            if driver != "ioatdma":
                self.test_case.dut.send_expect(
                    "./usertools/dpdk-devbind.py --force --bind=ioatdma %s" % pci,
                    "# ",
                    60,
                )


class dsa_common(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def get_all_work_queue_index(self):
        """
        Get all DSA device work queue index.
        Example: `wq0.0 wq0.1 wq1.0 wq1.1`, return [0, 1]
        """
        dsa_index_list = []
        if os.path.exists("/dev/dsa"):
            out = self.test_case.dut.send_expect("ls /dev/dsa", "# ")
            info = out.split()
            for item in info:
                index = int(re.search("(\d+)", item).group(0))
                dsa_index_list.append(index)
        return list(set(dsa_index_list))

    def reset_all_work_queue(self):
        """
        Reset all DSA device work queue which have created work queue.
        After reset all DSA device work queues, the `/dev/dsa/` path will not exist.
        """
        dsa_index_list = self.get_all_work_queue_index()
        if len(dsa_index_list) > 0:
            for dsa_index in dsa_index_list:
                self.test_case.dut.send_expect(
                    "./drivers/dma/idxd/dpdk_idxd_cfg.py --reset %s" % dsa_index, "# "
                )

    def check_dsa_has_work_queue(self, dsa_index):
        """
        Check DSA device has work queue or not, if has work queue, return True, or return False
        """
        if dsa_index in self.get_all_work_queue_index():
            return True
        else:
            return False

    def create_work_queue(self, work_queue_number, dsa_index):
        """
        Create work queue by work_queue_number and dsa_index.
        :param work_queue_number: number of work queue to be create.
        :param dsa_index: index of DSA device which to create work queue.
        Example: work_queue_number=4, dsa_index=0, will create 4 work queue under this first DSA device
        root@dpdk:~# ls /dev/dsa/
        wq0.0  wq0.1  wq0.2  wq0.3
        """
        if self.check_dsa_has_work_queue(dsa_index=dsa_index):
            self.test_case.dut.send_expect(
                "./drivers/dma/idxd/dpdk_idxd_cfg.py --reset %s" % dsa_index, "# "
            )
        self.test_case.dut.send_expect(
            "./drivers/dma/idxd/dpdk_idxd_cfg.py -q %d %d"
            % (work_queue_number, dsa_index),
            "# ",
        )

    def get_all_dsa_pci(self):
        """
        Get all the DSA device PCI of DUT.
        :return: [0000:6a:01.0, 0000:6f:01.0, 0000:74:01.0, 0000:79:01.0]
        """
        dsa_pci = []
        out = self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "#"
        )
        info = out.split("\n")
        for item in info:
            pci = re.search("\s*(0000:\S*:\d*.\d*)", item)
            if pci is not None:
                dsa_pci.append(pci.group(1))
        return dsa_pci

    def bind_dsa_to_dpdk(
        self, dsa_number, driver_name="vfio-pci", dsa_index_list="all", socket=-1
    ):
        """
        Bind DSA device to driver
        :param dsa_number: number of DSA device to be bind.
        :param driver_name: driver name, like `vfio-pci`.
        :param dsa_index_list: the index list of DSA device, like [2,3]
        :param socket: socket id: like 0 or 1, if socket=-1, use all the DSA deveice no matter on which socket.
        :return: bind_dsa_list, like [0000:6a:01.0, 0000:6f:01.0]
        """
        dsa_list = []
        dsa_pci = self.get_all_dsa_pci()
        for pci in dsa_pci:
            addr_array = pci.split(":")
            domain_id, bus_id, devfun_id = addr_array[0], addr_array[1], addr_array[2]
            cur_socket = self.test_case.dut.send_expect(
                "cat /sys/bus/pci/devices/%s\:%s\:%s/numa_node"
                % (domain_id, bus_id, devfun_id),
                "# ",
                alt_session=True,
            )
            if socket != -1:
                if int(cur_socket) == socket:
                    dsa_list.append(pci)
            else:
                dsa_list.append(pci)
        if dsa_index_list == "all":
            bind_dsa_list = dsa_list[0:dsa_number]
        else:
            tmp_dsa_list = []
            for i in dsa_index_list:
                tmp_dsa_list.append(dsa_list[i])
            bind_dsa_list = tmp_dsa_list[0:dsa_number]
        bind_dsa_string = " ".join(bind_dsa_list)
        self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (driver_name, bind_dsa_string),
            "# ",
            60,
        )
        return bind_dsa_list

    def bind_all_dsa_to_kernel(self):
        """
        Check the DSA device is bind to kernel driver or not, if not bind to kernel driver, then bind to kernel driver.
        """
        dsa_pci = self.get_all_dsa_pci()
        for pci in dsa_pci:
            addr_array = pci.split(":")
            domain_id, bus_id, devfun_id = addr_array[0], addr_array[1], addr_array[2]
            out = self.test_case.dut.send_expect(
                "cat /sys/bus/pci/devices/%s\:%s\:%s/uevent"
                % (domain_id, bus_id, devfun_id),
                "# ",
                alt_session=True,
            )
            rexp = r"DRIVER=(.+?)\r"
            pattern = re.compile(rexp)
            match = pattern.search(out)
            if not match:
                driver = None
            else:
                driver = match.group(1)
            if driver != "idxd":
                self.test_case.dut.send_expect(
                    "./usertools/dpdk-devbind.py --force --bind=idxd %s" % pci, "# ", 60
                )

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

    def check_2M_hugepage_size(self):
        """
        check the Hugepage size is 2M or not on DUT
        :return: True or False
        """
        out = self.test_case.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def config_2_vms_ip(self):
        """
        config VM interface IP address and send ARP request
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
        return iperfdata[-1]


class cbdma_common(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def get_all_cbdma_pcis(self):
        """
        get all the CBDMA device PCIs on DUT
        :return: cbdma_pcis, like [0000:00:04.0, 0000:00:04.1, 0000:00:04.2, 0000:00:04.3, 0000:00:04.4]
        """
        cbdma_pcis = []
        out = self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "#"
        )
        info = out.split("\n")
        for item in info:
            pci = re.search("\s*(0000:\S*:\d*.\d*)", item)
            if pci is not None:
                cbdma_pcis.append(pci.group(1))
        cbdma_pcis.sort()
        return cbdma_pcis

    def bind_cbdma_to_dpdk_driver(
        self, cbdma_num, driver_name="vfio-pci", cbdma_idxs="all", socket=-1
    ):
        """
        bind CBDMA device to DPDK driver
        :param cbdma_num: number of CBDMA device to be bind.
        :param driver_name: driver name, like `vfio-pci`.
        :param cbdma_idxs: the index list of DSA device, like [2,3]
        :param socket: socket id: like 0 or 1, if socket=-1, use all the CBDMA deveice no matter on which socket.
        :return: bind_cbdmas, like [0000:00:04.0, 0000:00:04.1]
        """
        cbdmas = []
        cbdma_pcis = self.get_all_cbdma_pcis()
        for pci in cbdma_pcis:
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
                    cbdmas.append(pci)
            else:
                cbdmas.append(pci)
        if cbdma_idxs == "all":
            bind_cbdmas = cbdmas[0:cbdma_num]
        else:
            tmp_cbdmas = []
            for i in cbdma_idxs:
                tmp_cbdmas.append(cbdmas[i])
            bind_cbdmas = tmp_cbdmas[0:cbdma_num]
        bind_cbdma_str = " ".join(bind_cbdmas)
        self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (driver_name, bind_cbdma_str),
            "# ",
            60,
        )
        return bind_cbdmas

    def bind_cbdma_to_kernel_driver(self, cbdma_idxs="all"):
        """
        check the CBDMA device is bind to kernel driver or not,
        if not bind to kernel driver, then bind to kernel driver.
        """
        cbdma_pcis = self.get_all_cbdma_pcis()
        pcis = []
        if cbdma_idxs == "all":
            pcis = cbdma_pcis
        else:
            for cbdma_idx in cbdma_idxs:
                pcis.append(cbdma_pcis[cbdma_idx])
        for pci in pcis:
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

    def get_all_dsa_pcis(self):
        """
        get all the DSA device PCIs on DUT
        :return: dsa_pcis, like [0000:6a:01.0, 0000:6f:01.0, 0000:74:01.0, 0000:79:01.0]
        """
        dsa_pcis = []
        out = self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "#"
        )
        info = out.split("\n")
        for item in info:
            pci = re.search("\s*(0000:\S*:\d*.\d*)", item)
            if pci is not None:
                dsa_pcis.append(pci.group(1))
        dsa_pcis.sort()
        return dsa_pcis

    def bind_dsa_to_kernel_driver(self, dsa_idx):
        """
        check the DSA device is bind to kernel driver or not,
        if not bind to kernel driver, then bind to kernel driver.
        """
        dsa_pcis = self.get_all_dsa_pcis()
        pci = dsa_pcis[dsa_idx]
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

    def get_all_dsa_idxs(self):
        """
        get all DSA device work queue index
        Example: `wq0.0 wq0.1 wq1.0 wq1.1`, return [0, 1]
        """
        dsa_idxs = []
        if os.path.exists("/dev/dsa"):
            out = self.test_case.dut.send_expect("ls /dev/dsa", "# ")
            info = out.split()
            for item in info:
                idx = int(re.search("(\d+)", item).group(0))
                dsa_idxs.append(idx)
        return list(set(dsa_idxs))

    def check_wq_exist(self, dsa_idx):
        """
        check DSA device has work queue or not,
        if has work queue, return True or False
        """
        if dsa_idx in self.get_all_dsa_idxs():
            return True
        else:
            return False

    def reset_wq(self, dsa_idx):
        """
        reset DSA device work queue which have created work queue
        """
        if self.check_wq_exist(dsa_idx):
            self.test_case.dut.send_expect(
                "./drivers/dma/idxd/dpdk_idxd_cfg.py --reset %s" % dsa_idx, "# "
            )

    def create_wq(self, wq_num, dsa_idxs):
        """
        create work queue by work_queue_number and dsa_idx
        :param wq_num: number of work queue to be create.
        :param dsa_idxs: index of DSA device which to create work queue.
        :return: wqs, like [wq0.0, wq0.1, wq1.0, wq1.1]
        Example: wq_num=4, dsa_idx=[0, 1], will create 4 work queue:
        root@dpdk:~# ls /dev/dsa/
        wq0.0  wq0.1  wq1.0  wq1.1
        """
        for dsa_idx in dsa_idxs:
            if self.check_wq_exist(dsa_idx):
                self.reset_wq(dsa_idx)
            self.bind_dsa_to_kernel_driver(dsa_idx)
            self.test_case.dut.send_expect(
                "./drivers/dma/idxd/dpdk_idxd_cfg.py -q %d %d" % (wq_num, dsa_idx),
                "# ",
            )
        wqs = []
        if os.path.exists("/dev/dsa"):
            out = self.test_case.dut.send_expect("ls /dev/dsa", "# ")
            info = out.split()
            for item in info:
                idx = int(re.search("(\d+)", item).group(0))
                if idx in dsa_idxs:
                    wqs.append(item)
        return wqs

    def bind_dsa_to_dpdk_driver(
        self, dsa_num, driver_name="vfio-pci", dsa_idxs="all", socket=-1
    ):
        """
        bind DSA device to driver
        :param dsa_num: number of DSA device to be bind.
        :param driver_name: driver name, like `vfio-pci`.
        :param dsa_idxs: the index list of DSA device, like [2,3]
        :param socket: socket id: like 0 or 1, if socket=-1, use all the DSA deveice no matter on which socket.
        :return: bind_dsas, like [0000:6a:01.0, 0000:6f:01.0]
        """
        dsas = []
        dsa_pcis = self.get_all_dsa_pcis()
        for pci in dsa_pcis:
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
                    dsas.append(pci)
            else:
                dsas.append(pci)
        if dsa_idxs == "all":
            bind_dsas = dsas[0:dsa_num]
        else:
            tmp_dsas = []
            for i in dsa_idxs:
                tmp_dsas.append(dsas[i])
            bind_dsas = tmp_dsas[0:dsa_num]
        bind_dsas_str = " ".join(bind_dsas)
        self.test_case.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (driver_name, bind_dsas_str),
            "# ",
            60,
        )
        return bind_dsas

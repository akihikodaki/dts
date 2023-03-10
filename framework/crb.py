# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

import os
import re
import time

from .config import PORTCONF, PktgenConf, PortConf
from .logger import getLogger
from .settings import TIMEOUT
from .ssh_connection import SSHConnection

"""
CRB (customer reference board) basic functions and handlers
"""


class Crb(object):

    """
    Basic module for customer reference board. This module implement functions
    interact with CRB. With these function, we can get the information of
    CPU/PCI/NIC on the board and setup running environment for DPDK.
    """

    PCI_DEV_CACHE_KEY = None
    NUMBER_CORES_CACHE_KEY = None
    CORE_LIST_CACHE_KEY = None

    def __init__(self, crb, serializer, dut_id=0, name=None, alt_session=True):
        self.dut_id = dut_id
        self.crb = crb
        self.read_cache = False
        self.skip_setup = False
        self.serializer = serializer
        self.ports_info = []
        self.sessions = []
        self.stage = "pre-init"
        self.name = name
        self.trex_prefix = None
        self.default_hugepages_cleared = False
        self.prefix_list = []

        self.logger = getLogger(name)
        self.session = SSHConnection(
            self.get_ip_address(),
            name,
            self.get_username(),
            self.get_password(),
            dut_id,
        )
        self.session.init_log(self.logger)
        if alt_session:
            self.alt_session = SSHConnection(
                self.get_ip_address(),
                name + "_alt",
                self.get_username(),
                self.get_password(),
                dut_id,
            )
            self.alt_session.init_log(self.logger)
        else:
            self.alt_session = None
        self.is_container = self._is_container()

    def get_ip_address(self):
        """
        Get CRB's ip address.
        """
        raise NotImplementedError

    def get_password(self):
        """
        Get CRB's login password.
        """
        raise NotImplementedError

    def get_username(self):
        """
        Get CRB's login username.
        """
        raise NotImplementedError

    def send_expect(
        self,
        cmds,
        expected,
        timeout=TIMEOUT,
        alt_session=False,
        verify=False,
        trim_whitespace=True,
    ):
        """
        Send commands to crb and return string before expected string. If
        there's no expected string found before timeout, TimeoutException will
        be raised.

        By default, it will trim the whitespace from the expected string. This
        behavior can be turned off via the trim_whitespace argument.
        """

        if trim_whitespace:
            expected = expected.strip()

        # sometimes there will be no alt_session like VM dut
        if alt_session and self.alt_session:
            return self.alt_session.session.send_expect(cmds, expected, timeout, verify)

        return self.session.send_expect(cmds, expected, timeout, verify)

    def create_session(self, name=""):
        """
        Create new session for additional usage. This session will not enable log.
        """
        logger = getLogger(name)
        session = SSHConnection(
            self.get_ip_address(),
            name,
            self.get_username(),
            self.get_password(),
            dut_id=self.dut_id,
        )
        session.init_log(logger)
        self.sessions.append(session)
        return session

    def destroy_session(self, session=None):
        """
        Destroy additional session.
        """
        for save_session in self.sessions:
            if save_session == session:
                save_session.close(force=True)
                logger = getLogger(save_session.name)
                logger.logger_exit()
                self.sessions.remove(save_session)
                break

    def reconnect_session(self, alt_session=False):
        """
        When session can't used anymore, recreate another one for replace
        """
        try:
            if alt_session:
                self.alt_session.close(force=True)
            else:
                self.session.close(force=True)
        except Exception as e:
            self.logger.error("Session close failed for [%s]" % e)

        if alt_session:
            session = SSHConnection(
                self.get_ip_address(),
                self.name + "_alt",
                self.get_username(),
                self.get_password(),
            )
            self.alt_session = session
        else:
            session = SSHConnection(
                self.get_ip_address(),
                self.name,
                self.get_username(),
                self.get_password(),
            )
            self.session = session

        session.init_log(self.logger)

    def send_command(self, cmds, timeout=TIMEOUT, alt_session=False):
        """
        Send commands to crb and return string before timeout.
        """

        if alt_session and self.alt_session:
            return self.alt_session.session.send_command(cmds, timeout)

        return self.session.send_command(cmds, timeout)

    def get_session_output(self, timeout=TIMEOUT):
        """
        Get session output message before timeout
        """
        return self.session.get_session_before(timeout)

    def set_test_types(self, func_tests, perf_tests):
        """
        Enable or disable function/performance test.
        """
        self.want_func_tests = func_tests
        self.want_perf_tests = perf_tests

    def get_total_huge_pages(self):
        """
        Get the huge page number of CRB.
        """
        huge_pages = self.send_expect(
            "awk '/HugePages_Total/ { print $2 }' /proc/meminfo", "# ", alt_session=True
        )
        if huge_pages != "":
            return int(huge_pages.split()[0])
        return 0

    def mount_huge_pages(self):
        """
        Mount hugepage file system on CRB.
        """
        out = self.send_expect("awk '/hugetlbfs/ { print $2 }' /proc/mounts", "# ")
        # if no hugetlbfs mounted, then above command will return " [PEXPECT]#"
        # so strip the unexptectd " [PEXPECT]#", to proceed to mount the hugetlbfs
        out = out.strip(" [PEXPECT]#")
        # only mount hugepage when no hugetlbfs mounted
        if not len(out):
            if self.is_container:
                raise ValueError(
                    "container hugepage not mount, please check hugepage config"
                )
            else:
                self.send_expect("mkdir -p /mnt/huge", "# ")
                self.send_expect("mount -t hugetlbfs nodev /mnt/huge", "# ")
                out = self.send_expect(
                    "awk '/hugetlbfs/ { print $2 }' /proc/mounts", "# "
                )
                if not len(out.strip(" [PEXPECT]#")):
                    raise ValueError(
                        "hugepage config error, please check hugepage config"
                    )

    def strip_hugepage_path(self):
        mounts = self.send_expect("cat /proc/mounts |grep hugetlbfs", "# ")
        infos = mounts.split()
        if len(infos) >= 2:
            return infos[1]
        else:
            return ""

    def set_huge_pages(self, huge_pages, numa=""):
        """
        Set numbers of huge pages
        """
        page_size = self.send_expect(
            "awk '/Hugepagesize/ {print $2}' /proc/meminfo", "# "
        )

        if not numa:
            self.send_expect(
                "echo %d > /sys/kernel/mm/hugepages/hugepages-%skB/nr_hugepages"
                % (huge_pages, page_size),
                "# ",
                5,
            )
        else:
            # sometimes we set hugepage on kernel cmdline, so we clear it
            if not self.default_hugepages_cleared:
                self.send_expect(
                    "echo 0 > /sys/kernel/mm/hugepages/hugepages-%skB/nr_hugepages"
                    % (page_size),
                    "# ",
                    5,
                )
                self.default_hugepages_cleared = True

            # some platform not support numa, example vm dut
            try:
                self.send_expect(
                    "echo %d > /sys/devices/system/node/%s/hugepages/hugepages-%skB/nr_hugepages"
                    % (huge_pages, numa, page_size),
                    "# ",
                    5,
                )
            except:
                self.logger.warning("set %d hugepage on %s error" % (huge_pages, numa))
                self.send_expect(
                    "echo %d > /sys/kernel/mm/hugepages/hugepages-%skB/nr_hugepages"
                    % (huge_pages.page_size),
                    "# ",
                    5,
                )

    def set_speedup_options(self, read_cache, skip_setup):
        """
        Configure skip network topology scan or skip DPDK packet setup.
        """
        self.read_cache = read_cache
        self.skip_setup = skip_setup

    def set_directory(self, base_dir):
        """
        Set DPDK package folder name.
        """
        self.base_dir = base_dir

    def admin_ports(self, port, status):
        """
        Force set port's interface status.
        """
        admin_ports_freebsd = getattr(
            self, "admin_ports_freebsd_%s" % self.get_os_type()
        )
        return admin_ports_freebsd()

    def admin_ports_freebsd(self, port, status):
        """
        Force set remote interface link status in FreeBSD.
        """
        eth = self.ports_info[port]["intf"]
        self.send_expect("ifconfig %s %s" % (eth, status), "# ", alt_session=True)

    def admin_ports_linux(self, eth, status):
        """
        Force set remote interface link status in Linux.
        """
        self.send_expect("ip link set  %s %s" % (eth, status), "# ", alt_session=True)

    def pci_devices_information(self):
        """
        Scan CRB pci device information and save it into cache file.
        """
        if self.read_cache:
            self.pci_devices_info = self.serializer.load(self.PCI_DEV_CACHE_KEY)

        if not self.read_cache or self.pci_devices_info is None:
            self.pci_devices_information_uncached()
            self.serializer.save(self.PCI_DEV_CACHE_KEY, self.pci_devices_info)

    def pci_devices_information_uncached(self):
        """
        Scan CRB NIC's information on different OS.
        """
        pci_devices_information_uncached = getattr(
            self, "pci_devices_information_uncached_%s" % self.get_os_type()
        )
        return pci_devices_information_uncached()

    def pci_devices_information_uncached_linux(self):
        """
        Look for the NIC's information (PCI Id and card type).
        """
        out = self.send_expect("lspci -Dnn | grep -i eth", "# ", alt_session=True)
        rexp = r"([\da-f]{4}:[\da-f]{2}:[\da-f]{2}.\d{1}) .*Eth.*?ernet .*?([\da-f]{4}:[\da-f]{4})"
        pattern = re.compile(rexp)
        match = pattern.findall(out)
        self.pci_devices_info = []

        obj_str = str(self)
        if "VirtDut" in obj_str:
            # there is no port.cfg in VM, so need to scan all pci in VM.
            pass
        else:
            # only scan configured pcis
            portconf = PortConf(PORTCONF)
            portconf.load_ports_config(self.crb["IP"])
            configed_pcis = portconf.get_ports_config()
            if configed_pcis:
                if "tester" in str(self):
                    tester_pci_in_cfg = []
                    for item in list(configed_pcis.values()):
                        for pci_info in match:
                            if item["peer"] == pci_info[0]:
                                tester_pci_in_cfg.append(pci_info)
                    match = tester_pci_in_cfg[:]
                else:
                    dut_pci_in_cfg = []
                    for key in list(configed_pcis.keys()):
                        for pci_info in match:
                            if key == pci_info[0]:
                                dut_pci_in_cfg.append(pci_info)
                    match = dut_pci_in_cfg[:]
                # keep the original pci sequence
                match = sorted(match)
            else:
                # INVALID CONFIG FOR NO PCI ADDRESS!!! eg: port.cfg for freeBSD
                pass

        for i in range(len(match)):
            # check if device is cavium and check its linkspeed, append only if it is 10G
            if "177d:" in match[i][1]:
                linkspeed = "10000"
                nic_linkspeed = self.send_expect(
                    "cat /sys/bus/pci/devices/%s/net/*/speed" % match[i][0],
                    "# ",
                    alt_session=True,
                )
                if nic_linkspeed.split()[0] == linkspeed:
                    self.pci_devices_info.append((match[i][0], match[i][1]))
            else:
                self.pci_devices_info.append((match[i][0], match[i][1]))

    def pci_devices_information_uncached_freebsd(self):
        """
        Look for the NIC's information (PCI Id and card type).
        """
        out = self.send_expect("pciconf -l", "# ", alt_session=True)
        rexp = r"pci0:([\da-f]{1,3}:[\da-f]{1,2}:\d{1}):\s*class=0x020000.*0x([\da-f]{4}).*8086"
        pattern = re.compile(rexp)
        match = pattern.findall(out)

        self.pci_devices_info = []
        for i in range(len(match)):
            card_type = "8086:%s" % match[i][1]
            self.pci_devices_info.append((match[i][0], card_type))

    def get_pci_dev_driver(self, domain_id, bus_id, devfun_id):
        """
        Get the driver of specified pci device.
        """
        get_pci_dev_driver = getattr(self, "get_pci_dev_driver_%s" % self.get_os_type())
        return get_pci_dev_driver(domain_id, bus_id, devfun_id)

    def get_pci_dev_driver_linux(self, domain_id, bus_id, devfun_id):
        """
        Get the driver of specified pci device on linux.
        """
        out = self.send_expect(
            "cat /sys/bus/pci/devices/%s\:%s\:%s/uevent"
            % (domain_id, bus_id, devfun_id),
            "# ",
            alt_session=True,
        )
        rexp = r"DRIVER=(.+?)\r"
        pattern = re.compile(rexp)
        match = pattern.search(out)
        if not match:
            return None
        return match.group(1)

    def get_pci_dev_driver_freebsd(self, domain_id, bus_id, devfun_id):
        """
        Get the driver of specified pci device.
        """
        return True

    def get_pci_dev_id(self, domain_id, bus_id, devfun_id):
        """
        Get the pci id of specified pci device.
        """
        get_pci_dev_id = getattr(self, "get_pci_dev_id_%s" % self.get_os_type())
        return get_pci_dev_id(domain_id, bus_id, devfun_id)

    def get_pci_dev_id_linux(self, domain_id, bus_id, devfun_id):
        """
        Get the pci id of specified pci device on linux.
        """
        out = self.send_expect(
            "cat /sys/bus/pci/devices/%s\:%s\:%s/uevent"
            % (domain_id, bus_id, devfun_id),
            "# ",
            alt_session=True,
        )
        rexp = r"PCI_ID=(.+)"
        pattern = re.compile(rexp)
        match = re.search(pattern, out)
        if not match:
            return None
        return match.group(1)

    def get_device_numa(self, domain_id, bus_id, devfun_id):
        """
        Get numa number of specified pci device.
        """
        get_device_numa = getattr(self, "get_device_numa_%s" % self.get_os_type())
        return get_device_numa(domain_id, bus_id, devfun_id)

    def get_device_numa_linux(self, domain_id, bus_id, devfun_id):
        """
        Get numa number of specified pci device on Linux.
        """
        numa = self.send_expect(
            "cat /sys/bus/pci/devices/%s\:%s\:%s/numa_node"
            % (domain_id, bus_id, devfun_id),
            "# ",
            alt_session=True,
        )

        try:
            numa = int(numa)
        except ValueError:
            numa = -1
            self.logger.warning("NUMA not available")
        return numa

    def get_ipv6_addr(self, intf):
        """
        Get ipv6 address of specified pci device.
        """
        get_ipv6_addr = getattr(self, "get_ipv6_addr_%s" % self.get_os_type())
        return get_ipv6_addr(intf)

    def get_ipv6_addr_linux(self, intf):
        """
        Get ipv6 address of specified pci device on linux.
        """
        out = self.send_expect(
            "ip -family inet6 address show dev %s | awk '/inet6/ { print $2 }'" % intf,
            "# ",
            alt_session=True,
        )
        return out.split("/")[0]

    def get_ipv6_addr_freebsd(self, intf):
        """
        Get ipv6 address of specified pci device on Freebsd.
        """
        out = self.send_expect("ifconfig %s" % intf, "# ", alt_session=True)
        rexp = r"inet6 ([\da-f:]*)%"
        pattern = re.compile(rexp)
        match = pattern.findall(out)
        if len(match) == 0:
            return None

        return match[0]

    def disable_ipv6(self, intf):
        """
        Disable ipv6 of of specified interface
        """
        if intf != "N/A":
            self.send_expect(
                "sysctl net.ipv6.conf.%s.disable_ipv6=1" % intf, "# ", alt_session=True
            )

    def enable_ipv6(self, intf):
        """
        Enable ipv6 of of specified interface
        """
        if intf != "N/A":
            self.send_expect(
                "sysctl net.ipv6.conf.%s.disable_ipv6=0" % intf, "# ", alt_session=True
            )

            out = self.send_expect("ifconfig %s" % intf, "# ", alt_session=True)
            if "inet6" not in out:
                self.send_expect("ifconfig %s down" % intf, "# ", alt_session=True)
                self.send_expect("ifconfig %s up" % intf, "# ", alt_session=True)

    def create_file(self, contents, fileName):
        """
        Create file with contents and copy it to CRB.
        """
        with open(fileName, "w") as f:
            f.write(contents)
        self.session.copy_file_to(fileName, password=self.get_password())

    def check_trex_process_existed(self):
        """
        if the tester and dut on same server
        and pktgen is trex, do not kill the process
        """
        if (
            "pktgen" in self.crb
            and (self.crb["pktgen"] is not None)
            and (self.crb["pktgen"].lower() == "trex")
        ):
            if self.crb["IP"] == self.crb["tester IP"] and self.trex_prefix is None:
                conf_inst = PktgenConf("trex")
                conf_info = conf_inst.load_pktgen_config()
                if "config_file" in conf_info:
                    config_file = conf_info["config_file"]
                else:
                    config_file = "/etc/trex_cfg.yaml"
                fd = open(config_file, "r")
                output = fd.read()
                fd.close()
                prefix = re.search("prefix\s*:\s*(\S*)", output)
                if prefix is not None:
                    self.trex_prefix = prefix.group(1)
        return self.trex_prefix

    def get_dpdk_pids(self, prefix_list, alt_session):
        """
        get all dpdk applications on CRB.
        """
        trex_prefix = self.check_trex_process_existed()
        if trex_prefix is not None and trex_prefix in prefix_list:
            prefix_list.remove(trex_prefix)
        file_directorys = [
            "/var/run/dpdk/%s/config" % file_prefix for file_prefix in prefix_list
        ]
        pids = []
        pid_reg = r"p(\d+)"
        for config_file in file_directorys:
            # Covers case where the process is run as a unprivileged user and does not generate the file
            isfile = self.send_expect(
                "ls -l {}".format(config_file), "# ", 20, alt_session
            )
            if isfile:
                cmd = "lsof -Fp %s" % config_file
                out = self.send_expect(cmd, "# ", 20, alt_session)
                if len(out):
                    lines = out.split("\r\n")
                    for line in lines:
                        m = re.match(pid_reg, line)
                        if m:
                            pids.append(m.group(1))
                for pid in pids:
                    self.send_expect("kill -9 %s" % pid, "# ", 20, alt_session)
                    self.get_session_output(timeout=2)

        hugepage_info = [
            "/var/run/dpdk/%s/hugepage_info" % file_prefix
            for file_prefix in prefix_list
        ]
        for hugepage in hugepage_info:
            # Covers case where the process is run as a unprivileged user and does not generate the file
            isfile = self.send_expect(
                "ls -l {}".format(hugepage), "# ", 20, alt_session
            )
            if isfile:
                cmd = "lsof -Fp %s" % hugepage
                out = self.send_expect(cmd, "# ", 20, alt_session)
                if len(out) and "No such file or directory" not in out:
                    self.logger.warning("There are some dpdk process not free hugepage")
                    self.logger.warning("**************************************")
                    self.logger.warning(out)
                    self.logger.warning("**************************************")

        # remove directory
        directorys = ["/var/run/dpdk/%s" % file_prefix for file_prefix in prefix_list]
        for directory in directorys:
            cmd = "rm -rf %s" % directory
            self.send_expect(cmd, "# ", 20, alt_session)

        # delete hugepage on mnt path
        if getattr(self, "hugepage_path", None):
            for file_prefix in prefix_list:
                cmd = "rm -rf %s/%s*" % (self.hugepage_path, file_prefix)
                self.send_expect(cmd, "# ", 20, alt_session)

    def kill_all(self, alt_session=True):
        """
        Kill all dpdk applications on CRB.
        """
        if "tester" in str(self):
            self.logger.info("kill_all: called by tester")
            pass
        else:
            if self.prefix_list:
                self.logger.info("kill_all: called by dut and prefix list has value.")
                self.get_dpdk_pids(self.prefix_list, alt_session)
                # init prefix_list
                self.prefix_list = []
            else:
                self.logger.info("kill_all: called by dut and has no prefix list.")
                out = self.send_command(
                    "ls -l /var/run/dpdk |awk '/^d/ {print $NF}'",
                    timeout=0.5,
                    alt_session=True,
                )
                # the last directory is expect string, eg: [PEXPECT]#
                if out != "":
                    dir_list = out.split("\r\n")
                    self.get_dpdk_pids(dir_list[:-1], alt_session)

    def close(self):
        """
        Close ssh session of CRB.
        """
        self.session.close()
        self.alt_session.close()

    def get_os_type(self):
        """
        Get OS type from execution configuration file.
        """
        from .dut import Dut

        if isinstance(self, Dut) and "OS" in self.crb:
            return str(self.crb["OS"]).lower()

        return "linux"

    def check_os_type(self):
        """
        Check real OS type whether match configured type.
        """
        from .dut import Dut

        expected = "Linux.*#"
        if isinstance(self, Dut) and self.get_os_type() == "freebsd":
            expected = "FreeBSD.*#"

        self.send_expect("uname", expected, 2, alt_session=True)

    def init_core_list(self):
        """
        Load or create core information of CRB.
        """
        if self.read_cache:
            self.number_of_cores = self.serializer.load(self.NUMBER_CORES_CACHE_KEY)
            self.cores = self.serializer.load(self.CORE_LIST_CACHE_KEY)

        if not self.read_cache or self.cores is None or self.number_of_cores is None:
            self.init_core_list_uncached()
            self.serializer.save(self.NUMBER_CORES_CACHE_KEY, self.number_of_cores)
            self.serializer.save(self.CORE_LIST_CACHE_KEY, self.cores)

    def init_core_list_uncached(self):
        """
        Scan cores on CRB and create core information list.
        """
        init_core_list_uncached = getattr(
            self, "init_core_list_uncached_%s" % self.get_os_type()
        )
        init_core_list_uncached()

    def init_core_list_uncached_freebsd(self):
        """
        Scan cores in Freebsd and create core information list.
        """
        self.cores = []

        import xml.etree.ElementTree as ET

        out = self.send_expect("sysctl -n kern.sched.topology_spec", "# ")

        cpu_xml = ET.fromstring(out)

        # WARNING: HARDCODED VALUES FOR CROWN PASS IVB
        thread = 0
        socket_id = 0

        sockets = cpu_xml.findall(".//group[@level='2']")
        for socket in sockets:
            core_id = 0
            core_elements = socket.findall(".//children/group/cpu")
            for core in core_elements:
                threads = [int(x) for x in core.text.split(",")]
                for thread in threads:
                    if self.crb["bypass core0"] and socket_id == 0 and core_id == 0:
                        continue
                    self.cores.append(
                        {"socket": socket_id, "core": core_id, "thread": thread}
                    )
                core_id += 1
            socket_id += 1
        self.number_of_cores = len(self.cores)

    def init_core_list_uncached_linux(self):
        """
        Scan cores in linux and create core information list.
        """
        self.cores = []

        cpuinfo = self.send_expect(
            "lscpu -p=CPU,CORE,SOCKET,NODE|grep -v \#", "#", alt_session=True
        )

        # cpuinfo = cpuinfo.split()
        cpuinfo = [i for i in cpuinfo.split() if re.match("^\d.+", i)]
        # haswell cpu on cottonwood core id not correct
        # need additional coremap for haswell cpu
        core_id = 0
        coremap = {}
        for line in cpuinfo:
            (thread, core, socket, node) = line.split(",")[0:4]

            if core not in list(coremap.keys()):
                coremap[core] = core_id
                core_id += 1

            if self.crb["bypass core0"] and core == "0" and socket == "0":
                self.logger.info("Core0 bypassed")
                continue
            if (
                self.crb.get("dut arch") == "arm64"
                or self.crb.get("dut arch") == "ppc64"
            ):
                self.cores.append(
                    {"thread": thread, "socket": node, "core": coremap[core]}
                )
            else:
                self.cores.append(
                    {"thread": thread, "socket": socket, "core": coremap[core]}
                )

        self.number_of_cores = len(self.cores)

    def get_all_cores(self):
        """
        Return core information list.
        """
        return self.cores

    def remove_hyper_core(self, core_list, key=None):
        """
        Remove hyperthread lcore for core list.
        """
        found = set()
        for core in core_list:
            val = core if key is None else key(core)
            if val not in found:
                yield core
                found.add(val)

    def init_reserved_core(self):
        """
        Remove hyperthread cores from reserved list.
        """
        partial_cores = self.cores
        # remove hyper-threading core
        self.reserved_cores = list(
            self.remove_hyper_core(
                partial_cores, key=lambda d: (d["core"], d["socket"])
            )
        )

    def remove_reserved_cores(self, core_list, args):
        """
        Remove cores from reserved cores.
        """
        indexes = sorted(args, reverse=True)
        for index in indexes:
            del core_list[index]
        return core_list

    def get_reserved_core(self, config, socket):
        """
        Get reserved cores by core config and socket id.
        """
        m = re.match("([1-9]+)C", config)
        nr_cores = int(m.group(1))
        if m is None:
            return []

        partial_cores = [n for n in self.reserved_cores if int(n["socket"]) == socket]
        if len(partial_cores) < nr_cores:
            return []

        thread_list = [self.reserved_cores[n]["thread"] for n in range(nr_cores)]

        # remove used core from reserved_cores
        rsv_list = [n for n in range(nr_cores)]
        self.reserved_cores = self.remove_reserved_cores(partial_cores, rsv_list)

        # return thread list
        return list(map(str, thread_list))

    def get_core_list(self, config, socket=-1, from_last=False):
        """
        Get lcore array according to the core config like "all", "1S/1C/1T".
        We can specify the physical CPU socket by the "socket" parameter.
        """
        if config == "all":
            cores = []
            if socket != -1:
                for core in self.cores:
                    if int(core["socket"]) == socket:
                        cores.append(core["thread"])
            else:
                cores = [core["thread"] for core in self.cores]
            return cores

        m = re.match("([1234])S/([0-9]+)C/([12])T", config)

        if m:
            nr_sockets = int(m.group(1))
            nr_cores = int(m.group(2))
            nr_threads = int(m.group(3))

            partial_cores = self.cores

            # If not specify socket sockList will be [0,1] in numa system
            # If specify socket will just use the socket
            if socket < 0:
                sockList = set([int(core["socket"]) for core in partial_cores])
            else:
                for n in partial_cores:
                    if int(n["socket"]) == socket:
                        sockList = [int(n["socket"])]

            if from_last:
                sockList = list(sockList)[-nr_sockets:]
            else:
                sockList = list(sockList)[:nr_sockets]
            partial_cores = [n for n in partial_cores if int(n["socket"]) in sockList]
            core_list = set([int(n["core"]) for n in partial_cores])
            core_list = list(core_list)
            thread_list = set([int(n["thread"]) for n in partial_cores])
            thread_list = list(thread_list)

            # filter usable core to core_list
            temp = []
            for sock in sockList:
                core_list = set(
                    [int(n["core"]) for n in partial_cores if int(n["socket"]) == sock]
                )
                if from_last:
                    core_list = list(core_list)[-nr_cores:]
                else:
                    core_list = list(core_list)[:nr_cores]
                temp.extend(core_list)

            core_list = temp

            # if system core less than request just use all cores in in socket
            if len(core_list) < (nr_cores * nr_sockets):
                partial_cores = self.cores
                sockList = set([int(n["socket"]) for n in partial_cores])

                if from_last:
                    sockList = list(sockList)[-nr_sockets:]
                else:
                    sockList = list(sockList)[:nr_sockets]
                partial_cores = [
                    n for n in partial_cores if int(n["socket"]) in sockList
                ]

                temp = []
                for sock in sockList:
                    core_list = list(
                        [
                            int(n["thread"])
                            for n in partial_cores
                            if int(n["socket"]) == sock
                        ]
                    )
                    if from_last:
                        core_list = core_list[-nr_cores:]
                    else:
                        core_list = core_list[:nr_cores]
                    temp.extend(core_list)

                core_list = temp

            partial_cores = [n for n in partial_cores if int(n["core"]) in core_list]
            temp = []
            if len(core_list) < nr_cores:
                raise ValueError(
                    "Cannot get requested core configuration "
                    "requested {} have {}".format(config, self.cores)
                )
            if len(sockList) < nr_sockets:
                raise ValueError(
                    "Cannot get requested core configuration "
                    "requested {} have {}".format(config, self.cores)
                )
            # recheck the core_list and create the thread_list
            i = 0
            for sock in sockList:
                coreList_aux = [
                    int(core_list[n])
                    for n in range((nr_cores * i), (nr_cores * i + nr_cores))
                ]
                for core in coreList_aux:
                    thread_list = list(
                        [
                            int(n["thread"])
                            for n in partial_cores
                            if ((int(n["core"]) == core) and (int(n["socket"]) == sock))
                        ]
                    )
                    if from_last:
                        thread_list = thread_list[-nr_threads:]
                    else:
                        thread_list = thread_list[:nr_threads]
                    temp.extend(thread_list)
                    thread_list = temp
                i += 1
            return list(map(str, thread_list))

    def get_lcore_id(self, config, inverse=False):
        """
        Get lcore id of specified core by config "C{socket.core.thread}"
        """

        m = re.match("C{([01]).(\d+).([01])}", config)

        if m:
            sockid = m.group(1)
            coreid = int(m.group(2))
            if inverse:
                coreid += 1
                coreid = -coreid
            threadid = int(m.group(3))
            if inverse:
                threadid += 1
                threadid = -threadid

            perSocklCs = [_ for _ in self.cores if _["socket"] == sockid]
            coreNum = perSocklCs[coreid]["core"]

            perCorelCs = [_ for _ in perSocklCs if _["core"] == coreNum]

            return perCorelCs[threadid]["thread"]

    def get_port_info(self, pci):
        """
        return port info by pci id
        """
        for port_info in self.ports_info:
            if port_info["pci"] == pci:
                return port_info

    def get_port_pci(self, port_id):
        """
        return port pci address by port index
        """
        return self.ports_info[port_id]["pci"]

    def enable_promisc(self, intf):
        if intf != "N/A":
            self.send_expect("ifconfig %s promisc" % intf, "# ", alt_session=True)

    def get_priv_flags_state(self, intf, flag, timeout=TIMEOUT):
        """

        :param intf: nic name
        :param flag: priv-flags flag
        :return: flag state
        """
        check_flag = "ethtool --show-priv-flags %s" % intf
        out = self.send_expect(check_flag, "# ", timeout)
        p = re.compile("%s\s*:\s+(\w+)" % flag)
        state = re.search(p, out)
        if state:
            return state.group(1)
        else:
            self.logger.info("NIC %s may be not find %s" % (intf, flag))
            return False

    def is_interface_up(self, intf, timeout=15):
        """
        check and wait port link status up until timeout
        """
        for i in range(timeout):
            link_status = self.get_interface_link_status(intf)
            if link_status == "Up":
                return True
            time.sleep(1)
        self.logger.error(f"check and wait {intf} link up timeout")
        return False

    def is_interface_down(self, intf, timeout=15):
        """
        check and wait port link status down until timeout
        """
        for i in range(timeout):
            link_status = self.get_interface_link_status(intf)
            if link_status == "Down":
                return True
            time.sleep(1)
        self.logger.error(f"check and wait {intf} link down timeout")
        return False

    def get_interface_link_status(self, intf):
        out = self.send_expect(f"ethtool {intf}", "#")
        link_status_matcher = r"Link detected: (\w+)"
        link_status = re.search(link_status_matcher, out).groups()[0]
        return "Up" if link_status == "yes" else "Down"

    def _is_container(self):
        if self.send_expect("export |grep -i CONTAINER ", "# "):
            return True
        elif self.send_expect("df -h / |grep overlay ", "# "):
            return True
        elif self.get_os_type() == "freebsd":
            return False
        elif self.send_expect(
            "systemd-detect-virt -c|egrep '(systemd-nspawn|lxc|docker|podman|rkt|wsl|container-other)$' ",
            "# ",
        ):
            return True
        else:
            return False

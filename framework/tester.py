# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
Interface for bulk traffic generators.
"""

import os
import random
import re
import subprocess
from multiprocessing import Process
from time import sleep

from nics.net_device import GetNicObj

from .config import PktgenConf
from .crb import Crb
from .exception import ParameterInvalidException
from .packet import (
    Packet,
    compare_pktload,
    get_scapy_module_impcmd,
    start_tcpdump,
    stop_and_load_tcpdump_packets,
    strip_pktload,
)
from .pktgen import getPacketGenerator
from .settings import (
    NICS,
    PERF_SETTING,
    PKTGEN,
    PKTGEN_GRP,
    USERNAME,
    load_global_setting,
)
from .utils import GREEN, check_crb_python_version, convert_int2ip, convert_ip2int


class Tester(Crb):

    """
    Start the DPDK traffic generator on the machine `target`.
    A config file and pcap file must have previously been copied
    to this machine.
    """

    PORT_INFO_CACHE_KEY = "tester_port_info"
    CORE_LIST_CACHE_KEY = "tester_core_list"
    NUMBER_CORES_CACHE_KEY = "tester_number_cores"
    PCI_DEV_CACHE_KEY = "tester_pci_dev_info"

    def __init__(self, crb, serializer):
        self.NAME = "tester"
        self.scapy_session = None
        super(Tester, self).__init__(crb, serializer, name=self.NAME)
        # check the python version of tester
        check_crb_python_version(self)

        self.bgProcIsRunning = False
        self.duts = []
        self.inBg = 0
        self.scapyCmds = []
        self.bgCmds = []
        self.bgItf = ""
        self.re_run_time = 0
        self.pktgen = None
        # prepare for scapy env
        self.scapy_sessions_li = list()
        self.scapy_session = self.prepare_scapy_env()
        self.check_scapy_version()
        self.tmp_file = "/tmp/tester/"
        out = self.send_expect("ls -d %s" % self.tmp_file, "# ", verify=True)
        if out == 2:
            self.send_expect("mkdir -p %s" % self.tmp_file, "# ")

    def prepare_scapy_env(self):
        session_name = (
            "tester_scapy"
            if not self.scapy_sessions_li
            else f"tester_scapy_{random.random()}"
        )
        session = self.create_session(session_name)
        self.scapy_sessions_li.append(session)
        session.send_expect("scapy", ">>> ")

        # import scapy moudle to scapy APP
        out = session.session.send_expect(get_scapy_module_impcmd(), ">>> ")
        if "ImportError" in out or "ModuleNotFoundError" in out:
            session.logger.warning(f"entering import error: {out}")

        return session

    def check_scapy_version(self):
        require_version = "2.4.4"
        self.scapy_session.get_session_before(timeout=1)
        self.scapy_session.send_expect("conf.version", "'")
        out = self.scapy_session.get_session_before(timeout=1)
        cur_version = out[: out.find("'")]
        out = self.session.send_expect("grep scapy requirements.txt", "# ")
        value = re.search("scapy\s*==\s*(\S*)", out)
        if value is not None:
            require_version = value.group(1)
        if cur_version != require_version:
            self.logger.warning(
                "The scapy vesrion not meet the requirement on tester,"
                + "please update your scapy, otherwise maybe some suite will failed"
            )

    def init_ext_gen(self):
        """
        Initialize tester packet generator object.
        """
        if self.it_uses_external_generator():
            if self.is_pktgen:
                self.pktgen_init()
            return

    def set_re_run(self, re_run_time):
        """
        set failed case re-run time
        """
        self.re_run_time = int(re_run_time)

    def get_ip_address(self):
        """
        Get ip address of tester CRB.
        """
        return self.crb["tester IP"]

    def get_username(self):
        """
        Get login username of tester CRB.
        """
        return USERNAME

    def get_password(self):
        """
        Get tester login password of tester CRB.
        """
        return self.crb["tester pass"]

    @property
    def is_pktgen(self):
        """
        Check whether packet generator is configured.
        """
        if PKTGEN not in self.crb or not self.crb[PKTGEN]:
            return False

        if self.crb[PKTGEN].lower() in PKTGEN_GRP:
            return True
        else:
            msg = os.linesep.join(
                [
                    "Packet generator <{0}> is not supported".format(self.crb[PKTGEN]),
                    "Current supports: {0}".format(" | ".join(PKTGEN_GRP)),
                ]
            )
            self.logger.info(msg)
            return False

    def has_external_traffic_generator(self):
        """
        Check whether performance test will base on IXIA equipment.
        """
        try:
            # if pktgen_group is set, take pktgen config file as first selection
            if self.is_pktgen:
                return True
        except Exception as e:
            return False

        return False

    def it_uses_external_generator(self):
        """
        Check whether IXIA generator is ready for performance test.
        """
        return (
            load_global_setting(PERF_SETTING) == "yes"
            and self.has_external_traffic_generator()
        )

    def tester_prerequisites(self):
        """
        Prerequest function should be called before execute any test case.
        Will call function to scan all lcore's information which on Tester.
        Then call pci scan function to collect nic device information.
        Then discovery the network topology and save it into cache file.
        At last setup DUT' environment for validation.
        """
        self.init_core_list()
        self.pci_devices_information()
        self.restore_interfaces()
        self.scan_ports()

        self.disable_lldp()

    def disable_lldp(self):
        """
        Disable tester ports LLDP.
        """
        result = self.send_expect("lldpad -d", "# ")
        if result:
            self.logger.error(result.strip())

        for port in self.ports_info:
            if not "intf" in list(port.keys()):
                continue
            eth = port["intf"]
            out = self.send_expect(
                "ethtool --show-priv-flags %s" % eth, "# ", alt_session=True
            )
            if "disable-fw-lldp" in out:
                self.send_expect(
                    "ethtool --set-priv-flags %s disable-fw-lldp on" % eth,
                    "# ",
                    alt_session=True,
                )
            self.send_expect(
                "lldptool set-lldp -i %s adminStatus=disabled" % eth,
                "# ",
                alt_session=True,
            )

    def get_local_port(self, remotePort):
        """
        Return tester local port connect to specified dut port.
        """
        return self.duts[0].ports_map[remotePort]

    def get_local_port_type(self, remotePort):
        """
        Return tester local port type connect to specified dut port.
        """
        return self.ports_info[self.get_local_port(remotePort)]["type"]

    def get_local_port_bydut(self, remotePort, dutIp):
        """
        Return tester local port connect to specified port and specified dut.
        """
        for dut in self.duts:
            if dut.crb["My IP"] == dutIp:
                return dut.ports_map[remotePort]

    def get_local_index(self, pci):
        """
        Return tester local port index by pci id
        """
        index = -1
        for port in self.ports_info:
            index += 1
            if pci == port["pci"]:
                return index
        return -1

    def get_pci(self, localPort):
        """
        Return tester local port pci id.
        """
        if localPort == -1:
            raise ParameterInvalidException("local port should not be -1")

        return self.ports_info[localPort]["pci"]

    def get_interface(self, localPort):
        """
        Return tester local port interface name.
        """
        if localPort == -1:
            raise ParameterInvalidException("local port should not be -1")

        if "intf" not in self.ports_info[localPort]:
            return "N/A"

        return self.ports_info[localPort]["intf"]

    def get_mac(self, localPort):
        """
        Return tester local port mac address.
        """
        if localPort == -1:
            raise ParameterInvalidException("local port should not be -1")

        if self.ports_info[localPort]["type"] in ("ixia", "trex"):
            return "00:00:00:00:00:01"
        else:
            return self.ports_info[localPort]["mac"]

    def get_port_status(self, port):
        """
        Return link status of ethernet.
        """
        eth = self.ports_info[port]["intf"]
        out = self.send_expect("ethtool %s" % eth, "# ")

        status = re.search(r"Link detected:\s+(yes|no)", out)
        if not status:
            self.logger.error("ERROR: unexpected output")

        if status.group(1) == "yes":
            return "up"
        else:
            return "down"

    def restore_interfaces(self):
        """
        Restore Linux interfaces.
        """
        if self.skip_setup:
            return

        if not self.is_container:
            self.send_expect("modprobe igb", "# ", 20)
            self.send_expect("modprobe ixgbe", "# ", 20)
            self.send_expect("modprobe e1000e", "# ", 20)
            self.send_expect("modprobe e1000", "# ", 20)

        try:
            for (pci_bus, pci_id) in self.pci_devices_info:
                addr_array = pci_bus.split(":")
                port = GetNicObj(self, addr_array[0], addr_array[1], addr_array[2])
                itf = port.get_interface_name()
                self.enable_ipv6(itf)
                self.send_expect("ifconfig %s up" % itf, "# ")
                if port.get_interface2_name():
                    itf = port.get_interface2_name()
                    self.enable_ipv6(itf)
                    self.send_expect("ifconfig %s up" % itf, "# ")

        except Exception as e:
            self.logger.error(f"   !!! Restore ITF: {e}")

        sleep(2)

    def restore_trex_interfaces(self):
        """
        Restore Linux interfaces used by trex
        """
        try:
            for port_info in self.ports_info:
                nic_type = port_info.get("type")
                if nic_type != "trex":
                    continue
                pci_bus = port_info.get("pci")
                port_inst = port_info.get("port")
                port_inst.bind_driver()
                itf = port_inst.get_interface_name()
                self.enable_ipv6(itf)
                self.send_expect("ifconfig %s up" % itf, "# ")
                if port_inst.get_interface2_name():
                    itf = port_inst.get_interface2_name()
                    self.enable_ipv6(itf)
                    self.send_expect("ifconfig %s up" % itf, "# ")
        except Exception as e:
            self.logger.error(f"   !!! Restore ITF: {e}")

        sleep(2)

    def set_promisc(self):
        try:
            for (pci_bus, pci_id) in self.pci_devices_info:
                addr_array = pci_bus.split(":")
                port = GetNicObj(self, addr_array[0], addr_array[1], addr_array[2])
                itf = port.get_interface_name()
                self.enable_promisc(itf)
                if port.get_interface2_name():
                    itf = port.get_interface2_name()
                    self.enable_promisc(itf)
        except Exception as e:
            pass

    def load_serializer_ports(self):
        cached_ports_info = self.serializer.load(self.PORT_INFO_CACHE_KEY)
        if cached_ports_info is None:
            return

        # now not save netdev object, will implemented later
        self.ports_info = cached_ports_info

    def save_serializer_ports(self):
        cached_ports_info = []
        for port in self.ports_info:
            port_info = {}
            for key in list(port.keys()):
                if type(port[key]) is str:
                    port_info[key] = port[key]
                # need save netdev objects
            cached_ports_info.append(port_info)
        self.serializer.save(self.PORT_INFO_CACHE_KEY, cached_ports_info)

    def _scan_pktgen_ports(self):
        """packet generator port setting
        Currently, trex run on tester node
        """
        new_ports_info = []
        pktgen_ports_info = self.pktgen.get_ports()
        for pktgen_port_info in pktgen_ports_info:
            pktgen_port_type = pktgen_port_info["type"]
            if pktgen_port_type.lower() == "ixia":
                self.ports_info.extend(pktgen_ports_info)
                break
            pktgen_port_name = pktgen_port_info["intf"]
            pktgen_pci = pktgen_port_info["pci"]
            pktgen_mac = pktgen_port_info["mac"]
            for port_info in self.ports_info:
                dts_pci = port_info["pci"]
                if dts_pci != pktgen_pci:
                    continue
                port_info["intf"] = pktgen_port_name
                port_info["type"] = pktgen_port_type
                port_info["mac"] = pktgen_mac
                break
            # Since tester port scanning work flow change, non-functional port
            # mapping config will be ignored. Add tester port mapping if no
            # port in ports info
            else:
                addr_array = pktgen_pci.split(":")
                port = GetNicObj(self, addr_array[0], addr_array[1], addr_array[2])
                new_ports_info.append(
                    {
                        "port": port,
                        "intf": pktgen_port_name,
                        "type": pktgen_port_type,
                        "pci": pktgen_pci,
                        "mac": pktgen_mac,
                        "ipv4": None,
                        "ipv6": None,
                    }
                )
        if new_ports_info:
            self.ports_info = self.ports_info + new_ports_info

    def scan_ports(self):
        """
        Scan all ports on tester and save port's pci/mac/interface.
        """
        if self.read_cache:
            self.load_serializer_ports()
            self.scan_ports_cached()

        if not self.read_cache or self.ports_info is None:
            self.scan_ports_uncached()
            if self.it_uses_external_generator():
                if self.is_pktgen:
                    self._scan_pktgen_ports()
            self.save_serializer_ports()

        for port_info in self.ports_info:
            self.logger.info(port_info)

    def scan_ports_cached(self):
        if self.ports_info is None:
            return

        for port_info in self.ports_info:
            if port_info["type"].lower() in ("ixia", "trex"):
                continue

            addr_array = port_info["pci"].split(":")
            domain_id = addr_array[0]
            bus_id = addr_array[1]
            devfun_id = addr_array[2]

            port = GetNicObj(self, domain_id, bus_id, devfun_id)
            intf = port.get_interface_name()

            self.logger.info(
                "Tester cached: [000:%s %s] %s"
                % (port_info["pci"], port_info["type"], intf)
            )
            port_info["port"] = port

    def scan_ports_uncached(self):
        """
        Return tester port pci/mac/interface information.
        """
        self.ports_info = []

        for (pci_bus, pci_id) in self.pci_devices_info:
            # ignore unknown card types
            if pci_id not in list(NICS.values()):
                self.logger.info("Tester: [%s %s] %s" % (pci_bus, pci_id, "unknow_nic"))
                continue

            addr_array = pci_bus.split(":")
            domain_id = addr_array[0]
            bus_id = addr_array[1]
            devfun_id = addr_array[2]

            port = GetNicObj(self, domain_id, bus_id, devfun_id)
            intf = port.get_interface_name()

            if "No such file" in intf:
                self.logger.info(
                    "Tester: [%s %s] %s" % (pci_bus, pci_id, "unknow_interface")
                )
                continue

            self.logger.info("Tester: [%s %s] %s" % (pci_bus, pci_id, intf))
            macaddr = port.get_mac_addr()

            ipv6 = port.get_ipv6_addr()
            ipv4 = port.get_ipv4_addr()

            # store the port info to port mapping
            self.ports_info.append(
                {
                    "port": port,
                    "pci": pci_bus,
                    "type": pci_id,
                    "intf": intf,
                    "mac": macaddr,
                    "ipv4": ipv4,
                    "ipv6": ipv6,
                }
            )

            # return if port does not have two interface
            if not port.get_interface2_name():
                continue

            intf = port.get_interface2_name()

            self.logger.info("Tester: [%s %s] %s" % (pci_bus, pci_id, intf))
            macaddr = port.get_intf2_mac_addr()

            ipv6 = port.get_ipv6_addr()

            # store the port info to port mapping
            self.ports_info.append(
                {
                    "port": port,
                    "pci": pci_bus,
                    "type": pci_id,
                    "intf": intf,
                    "mac": macaddr,
                    "ipv6": ipv6,
                }
            )

    def pktgen_init(self):
        """
        initialize packet generator instance
        """
        pktgen_type = self.crb[PKTGEN]
        # init packet generator instance
        self.pktgen = getPacketGenerator(self, pktgen_type)
        # prepare running environment
        self.pktgen.prepare_generator()

    def send_ping(self, localPort, ipv4, mac):
        """
        Send ping4 packet from local port with destination ipv4 address.
        """
        if self.ports_info[localPort]["type"].lower() in ("ixia", "trex"):
            return "Not implemented yet"
        else:
            return self.send_expect(
                "ping -w 5 -c 5 -A -I %s %s"
                % (self.ports_info[localPort]["intf"], ipv4),
                "# ",
                10,
            )

    def send_ping6(self, localPort, ipv6, mac):
        """
        Send ping6 packet from local port with destination ipv6 address.
        """
        if self.is_pktgen:
            if self.ports_info[localPort]["type"].lower() in "ixia":
                return self.pktgen.send_ping6(
                    self.ports_info[localPort]["pci"], mac, ipv6
                )
            elif self.ports_info[localPort]["type"].lower() == "trex":
                return "Not implemented yet"
        else:
            return self.send_expect(
                "ping6 -w 5 -c 5 -A %s%%%s"
                % (ipv6, self.ports_info[localPort]["intf"]),
                "# ",
                10,
            )

    def get_port_numa(self, port):
        """
        Return tester local port numa.
        """
        pci = self.ports_info[port]["pci"]
        out = self.send_expect("cat /sys/bus/pci/devices/%s/numa_node" % pci, "#")
        return int(out)

    def check_port_list(self, portList, ftype="normal"):
        """
        Check specified port is IXIA port or normal port.
        """
        dtype = None
        plist = set()
        for txPort, rxPort, _ in portList:
            plist.add(txPort)
            plist.add(rxPort)

        plist = list(plist)
        if len(plist) > 0:
            dtype = self.ports_info[plist[0]]["type"]

        for port in plist[1:]:
            if dtype != self.ports_info[port]["type"]:
                return False

        if ftype == "ixia" and dtype != ftype:
            return False

        return True

    def scapy_append(self, cmd):
        """
        Append command into scapy command list.
        """
        self.scapyCmds.append(cmd)

    def scapy_execute(self, timeout=60):
        """
        Execute scapy command list.
        """
        self.kill_all()

        self.send_expect("scapy", ">>> ")
        if self.bgProcIsRunning:
            self.send_expect(
                'subprocess.call("scapy -c sniff.py &", shell=True)', ">>> "
            )
            self.bgProcIsRunning = False
        sleep(2)

        for cmd in self.scapyCmds:
            self.send_expect(cmd, ">>> ", timeout)

        sleep(2)
        self.scapyCmds = []
        self.send_expect("exit()", "# ", timeout)

    def scapy_background(self):
        """
        Configure scapy running in background mode which mainly purpose is
        that save RESULT into scapyResult.txt.
        """
        self.inBg = True

    def scapy_foreground(self):
        """
        Running background scapy and convert to foreground mode.
        """
        self.send_expect("echo -n '' >  scapyResult.txt", "# ")
        if self.inBg:
            self.scapyCmds.append("f = open('scapyResult.txt','w')")
            self.scapyCmds.append("f.write(RESULT)")
            self.scapyCmds.append("f.close()")
            self.scapyCmds.append("exit()")

            outContents = (
                "import os\n"
                + "conf.color_theme=NoTheme()\n"
                + 'RESULT=""\n'
                + "\n".join(self.scapyCmds)
                + "\n"
            )
            self.create_file(outContents, "sniff.py")

            self.logger.info("SCAPY Receive setup:\n" + outContents)

            self.bgProcIsRunning = True
            self.scapyCmds = []
        self.inBg = False

    def scapy_get_result(self):
        """
        Return RESULT which saved in scapyResult.txt.
        """
        out = self.send_expect("cat scapyResult.txt", "# ")
        self.logger.info("SCAPY Result:\n" + out + "\n\n\n")

        return out

    def parallel_transmit_ptks(self, pkt=None, intf="", send_times=1, interval=0.01):
        """
        Callable function for parallel processes
        """
        print(GREEN("Transmitting and sniffing packets, please wait few minutes..."))
        return pkt.send_pkt_bg_with_pcapfile(
            crb=self, tx_port=intf, count=send_times, loop=0, inter=interval
        )

    def check_random_pkts(
        self,
        portList,
        pktnum=2000,
        interval=0.01,
        allow_miss=True,
        seq_check=False,
        params=None,
    ):
        """
        Send several random packets and check rx packets matched
        """
        tx_pkts = {}
        rx_inst = {}
        # packet type random between tcp/udp/ipv6
        random_type = ["TCP", "UDP", "IPv6_TCP", "IPv6_UDP"]
        for txport, rxport in portList:
            txIntf = self.get_interface(txport)
            rxIntf = self.get_interface(rxport)
            self.logger.info(
                GREEN("Preparing transmit packets, please wait few minutes...")
            )
            pkt = Packet()
            pkt.generate_random_pkts(
                pktnum=pktnum,
                random_type=random_type,
                ip_increase=True,
                random_payload=True,
                options={"layers_config": params},
            )

            tx_pkts[txport] = pkt
            # sniff packets
            inst = start_tcpdump(
                self,
                rxIntf,
                count=pktnum,
                filters=[
                    {"layer": "network", "config": {"srcport": "65535"}},
                    {"layer": "network", "config": {"dstport": "65535"}},
                ],
            )
            rx_inst[rxport] = inst
        bg_sessions = list()
        for txport, _ in portList:
            txIntf = self.get_interface(txport)
            bg_sessions.append(
                self.parallel_transmit_ptks(
                    pkt=tx_pkts[txport], intf=txIntf, send_times=1, interval=interval
                )
            )
        # Verify all packets
        sleep(interval * pktnum + 1)
        timeout = 60
        for i in bg_sessions:
            while timeout:
                try:
                    i.send_expect("", ">>> ", timeout=1)
                except Exception as e:
                    print(e)
                    self.logger.info("wait for the completion of sending pkts...")
                    timeout -= 1
                    continue
                else:
                    break
            else:
                self.logger.info(
                    "exceeded timeout, force to stop background packet sending to avoid dead loop"
                )
                Packet.stop_send_pkt_bg(i)
        prev_id = -1
        for txport, rxport in portList:
            p = stop_and_load_tcpdump_packets(rx_inst[rxport])
            recv_pkts = p.pktgen.pkts
            # only report when received number not matched
            if len(tx_pkts[txport].pktgen.pkts) > len(recv_pkts):
                self.logger.info(
                    (
                        "Pkt number not matched,%d sent and %d received\n"
                        % (len(tx_pkts[txport].pktgen.pkts), len(recv_pkts))
                    )
                )
                if allow_miss is False:
                    return False

            # check each received packet content
            self.logger.info(
                GREEN("Comparing sniffed packets, please wait few minutes...")
            )
            for idx in range(len(recv_pkts)):
                try:
                    l3_type = p.strip_element_layer2("type", p_index=idx)
                    sip = p.strip_element_layer3("dst", p_index=idx)
                except Exception as e:
                    continue
                # ipv4 packet
                if l3_type == 2048:
                    t_idx = convert_ip2int(sip, 4)
                # ipv6 packet
                elif l3_type == 34525:
                    t_idx = convert_ip2int(sip, 6)
                else:
                    continue

                if seq_check:
                    if t_idx <= prev_id:
                        self.logger.info("Packet %d sequence not correct" % t_idx)
                        return False
                    else:
                        prev_id = t_idx

                if (
                    compare_pktload(
                        tx_pkts[txport].pktgen.pkts[idx], recv_pkts[idx], "L4"
                    )
                    is False
                ):
                    self.logger.warning(
                        "Pkt received index %d not match original "
                        "index %d" % (idx, idx)
                    )
                    self.logger.info(
                        "Sent: %s"
                        % strip_pktload(tx_pkts[txport].pktgen.pkts[idx], "L4")
                    )
                    self.logger.info("Recv: %s" % strip_pktload(recv_pkts[idx], "L4"))
                    return False

        return True

    def tcpdump_sniff_packets(self, intf, count=0, filters=None, lldp_forbid=True):
        """
        Wrapper for packet module sniff_packets
        """
        inst = start_tcpdump(
            self, intf=intf, count=count, filters=filters, lldp_forbid=lldp_forbid
        )
        return inst

    def load_tcpdump_sniff_packets(self, index="", timeout=1):
        """
        Wrapper for packet module load_pcapfile
        """
        p = stop_and_load_tcpdump_packets(index, timeout=timeout)
        return p

    def kill_all(self, killall=False):
        """
        Kill all scapy process or DPDK application on tester.
        """
        if not self.has_external_traffic_generator():
            out = self.session.send_command("")
            if ">>>" in out:
                self.session.send_expect("quit()", "# ", timeout=3)
        if killall:
            super(Tester, self).kill_all()

    def close(self):
        """
        Close ssh session and IXIA tcl session.
        """
        if self.it_uses_external_generator():
            if self.is_pktgen and self.pktgen:
                self.pktgen.quit_generator()
                # only restore ports if start trex in dts
                if "start_trex" in list(self.pktgen.conf.keys()):
                    self.restore_trex_interfaces()
                self.pktgen = None

        if self.scapy_sessions_li:
            for i in self.scapy_sessions_li:
                if i.session.isalive():
                    i.session.send_expect("quit()", "#", timeout=2)
                    i.session.close()
            self.scapy_sessions_li.clear()

        if self.alt_session:
            self.alt_session.close()
            self.alt_session = None
        if self.session:
            self.session.close()
            self.session = None

    def crb_exit(self):
        """
        Close all resource before crb exit
        """
        self.close()
        self.logger.logger_exit()

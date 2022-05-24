# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
DPDK Test suite.
Test support dpdk pdump tool features
"""
import os
import random
import re
import signal
import subprocess
import time
import traceback
from pprint import pformat

from scapy.fields import ConditionalField
from scapy.packet import NoPayload
from scapy.packet import Packet as scapyPacket
from scapy.utils import rdpcap

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

# These source code copy from packet.py module before sniff_packets/load_sniff_packets
# refactor. New refactor methods have much more longer time consumption than
# old methods.

# Saved back ground sniff process id
SNIFF_PIDS = {}


def sniff_packets(intf, count=0, timeout=5, pcap=None):
    """
    sniff all packets for certain port in certain seconds.
    """
    param = ""
    direct_param = r"(\s+)\[ -(\w) in\|out\|inout \]"
    tcpdump_help = subprocess.check_output(
        "tcpdump -h; echo 0", stderr=subprocess.STDOUT, shell=True
    )
    for line in tcpdump_help.split("\n"):
        m = re.match(direct_param, line)
        if m:
            param = "-" + m.group(2) + " in"

    if len(param) == 0:
        print("tcpdump not support direction choice!!!")

    sniff_cmd = "tcpdump -i %(INTF)s %(IN_PARAM)s -w %(FILE)s"
    options = {
        "INTF": intf,
        "COUNT": count,
        "IN_PARAM": param,
        "FILE": "/tmp/sniff_%s.pcap" % intf if not pcap else pcap,
    }
    if count:
        sniff_cmd += " -c %(COUNT)d"
        cmd = sniff_cmd % options
    else:
        cmd = sniff_cmd % options

    args = cmd.split()
    pipe = subprocess.Popen(args)
    index = str(time.time())
    SNIFF_PIDS[index] = (pipe, intf, timeout)
    time.sleep(0.5)
    return index


def load_sniff_packets(index=""):
    pkts = []
    child_exit = False
    if index in list(SNIFF_PIDS.keys()):
        pipe, intf, timeout = SNIFF_PIDS[index]
        time_elapse = int(time.time() - float(index))
        while time_elapse < timeout:
            if pipe.poll() is not None:
                child_exit = True
                break

            time.sleep(1)
            time_elapse += 1

        if not child_exit:
            pipe.send_signal(signal.SIGINT)
            pipe.wait()

        # wait pcap file ready
        time.sleep(1)
        try:
            cap_pkts = rdpcap("/tmp/sniff_%s.pcap" % intf)
            for pkt in cap_pkts:
                # packet gen should be scapy
                packet = Packet(tx_port=intf)
                packet.pktgen.assign_pkt(pkt)
                pkts.append(packet)
        except Exception as e:
            pass

    return pkts


class parsePacket(object):
    def __init__(self, filename):
        self.pcapFile = filename
        self.packetLayers = dict()

    def parse_packet_layer(self, pkt_object):
        if pkt_object is None:
            return
        self.packetLayers[pkt_object.name] = dict()
        for curfield in pkt_object.fields_desc:
            if isinstance(curfield, ConditionalField) and not curfield._evalcond(
                pkt_object
            ):
                continue
            field_value = pkt_object.getfieldval(curfield.name)
            if isinstance(field_value, scapyPacket) or (
                curfield.islist and curfield.holds_packets and type(field_value) is list
            ):
                continue
            repr_value = curfield.i2repr(pkt_object, field_value)
            if isinstance(repr_value, str):
                repr_value = repr_value.replace(
                    os.linesep, os.linesep + " " * (len(curfield.name) + 4)
                )
            self.packetLayers[pkt_object.name][curfield.name] = repr_value
        if not isinstance(pkt_object.payload, NoPayload):
            self.parse_packet_layer(pkt_object.payload)

    def get_valid_packet(self, pcap_pkts_origin, number):
        cnt = 0
        for packet in pcap_pkts_origin:
            self.parse_packet_layer(packet)
            if number == cnt:
                break
            cnt += 1
            self.packetLayers.clear()

    def parse_pcap(self, number=0):
        pcap_pkts = []
        try:
            if not os.path.exists(self.pcapFile):
                warning = "{0} is not exist !".format(self.pcapFile)
                return warning
            pcap_pkts = rdpcap(self.pcapFile)
            if len(pcap_pkts) == 0:
                warning = "{0} is empty".format(self.pcapFile)
                return warning
            elif number >= len(pcap_pkts):
                warning = "{0} is missing No.{1} packet".format(self.pcapFile, number)
                return warning
            self.get_valid_packet(pcap_pkts, number)
        except Exception as e:
            print(e)

        return None


class TestPacketCapture(TestCase):
    def is_existed_on_crb(self, check_path, crb="dut"):
        alt_session = self.dut.alt_session if crb == "dut" else self.tester.alt_session
        alt_session.send_expect("ls %s" % check_path, "# ")
        cmd = "echo $?"
        output = alt_session.send_expect(cmd, "# ")
        ret = True if output and output.strip() == "0" else False
        return ret

    @property
    def is_dut_on_tester(self):
        # get dut/tester ip to check if they are in a platform
        tester_ip = self.tester.get_ip_address()
        dut_ip = self.dut.get_ip_address()
        return tester_ip == dut_ip

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = (
            "/root" + self.dut.base_dir[1:]
            if self.dut.base_dir.startswith("~")
            else self.dut.base_dir
        )
        return target_dir

    def get_dut_iface_with_kernel_driver(self):
        # only physical nic support PROMISC
        cmd = "ip link show | grep BROADCAST,MULTICAST | awk {'print $2'}"
        out = self.dut.alt_session.send_expect(cmd, "# ")
        pat = "(.*):"
        ifaces = [intf for intf in re.findall(pat, out, re.M) if intf]
        for link_port in range(len(self.dut_ports)):
            # if they are in a platform, ignore interface used by tester
            if not self.is_dut_on_tester:
                tester_port = self.tester.get_local_port(link_port)
                intf = self.tester.get_interface(tester_port)
                if intf in ifaces:
                    ifaces.remove(intf)
            # ignore interface used by dut
            intf = self.dut.ports_info[link_port]["intf"]
            if intf in ifaces:
                ifaces.remove(intf)

        # set ports up
        tmp_ifaces = ifaces[:]
        for iface in tmp_ifaces:
            # ignore current interface used by system
            cmd = "ifconfig %s | grep 'inet ' " % iface
            if self.dut.alt_session.send_expect(cmd, "# ") != "":
                ifaces.remove(iface)
            self.dut.alt_session.send_expect("ifconfig {0} up".format(iface), "# ")
        time.sleep(10)
        # get ports on link status
        tmp_ifaces = ifaces[:]
        for iface in tmp_ifaces:
            cmd = "ip link show {0} | grep LOWER_UP".format(iface)
            self.dut.alt_session.send_expect(cmd, "# ")
            output = self.dut.alt_session.send_expect(
                "echo $?".format(iface), "# "
            ).strip()
            if output != "0":
                ifaces.remove(iface)

        self.verify(len(ifaces) >= 2, "Insufficient ports for iface testing")
        # set iface port for pdump tool output dump packets
        self.rx_iface = ifaces[0]
        self.tx_iface = ifaces[1]
        self.rxtx_iface = ifaces[0]

    def verify_supported_nic(self):
        supported_drivers = ["i40e", "ixgbe"]
        result = all(
            [
                self.dut.ports_info[index]["port"].default_driver in supported_drivers
                for index in self.dut_ports
            ]
        )
        msg = "current nic is not supported"
        self.verify(result, msg)

    def get_tcpdump_options(self):
        param = ""
        direct_param = r"(\s+)\[ -(\w) in\|out\|inout \]"
        tcpdump_help = self.dut.alt_session.send_expect("tcpdump -h", "# ")
        for line in tcpdump_help.split("\n"):
            m = re.match(direct_param, line)
            if m:
                param = "-" + m.group(2) + " out"
        self.tcpdump = "tcpdump -i {0} " + param + " -w {1} >/dev/null 2>&1 &"

    def check_pcap_lib(self):
        pcap_lib_dir = os.sep.join(
            [self.target_dir, self.target, "lib/librte_pmd_pcap.a"]
        )
        return self.is_existed_on_crb(pcap_lib_dir)

    def get_packet_types(self):
        packet_types = [
            "TCP",
            "UDP",
            "SCTP",
            "TIMESYNC",
            "ARP",
            "LLDP",
            "IP_RAW",
            "IPv6_TCP",
            "IPv6_UDP",
            "IPv6_SCTP",
            "VLAN_UDP",
        ]
        if self.pkt_index is None:  # only initialize once
            self.pkt_index = random.randint(0, len(packet_types) - 1)
        test_packet_types = (
            packet_types if self.full_test else [packet_types[self.pkt_index]]
        )
        return test_packet_types

    def generate_options(self, port_id, pci, intf, types):
        port_types = ["port=%d," % port_id, "device_id=%s," % pci]
        dump_pcap_types = [
            [
                "tx-dev={0},rx-dev={1},".format(self.tx_pcap, self.rx_pcap),
                {"rx": [self.rx_pcap, 1], "tx": [self.tx_pcap, 1]},
            ],
            [
                "rx-dev={0},".format(self.rx_pcap),
                {"rx": [self.rx_pcap, 1], "tx": [None, 0]},
            ],
            [
                "tx-dev={0},".format(self.tx_pcap),
                {"rx": [None, 0], "tx": [self.tx_pcap, 1]},
            ],
        ]
        dump_iface_types = [
            [
                "tx-dev={0},rx-dev={1},".format(self.tx_iface, self.rx_iface),
                {"rx": [self.rx_pcap, 1], "tx": [self.tx_pcap, 1]},
            ],
            [
                "rx-dev={0},".format(self.rx_iface),
                {"rx": [self.rx_pcap, 1], "tx": [None, 0]},
            ],
            [
                "tx-dev={0},".format(self.tx_iface),
                {"rx": [None, 0], "tx": [self.tx_pcap, 1]},
            ],
        ]

        queue_types = ["queue=*,", "queue=0,"]
        # ring size
        maxPower = 27
        minPower = 1
        ring_size_types = [
            "ring-size=%d," % (2**minPower),
            "ring-size=%d," % (2 ** random.randint(minPower + 1, maxPower)),
            "ring-size=%d," % (2**maxPower),
        ]
        # mbuf size
        max_mbuf_size = 50000
        min_mbuf_size = 252
        mbuf_size_types = [
            "mbuf-size=%d," % min_mbuf_size,
            "mbuf-size=%d," % random.randint(min_mbuf_size + 1, max_mbuf_size),
            "mbuf-size=%d," % max_mbuf_size,
        ]
        # total number mbuf
        max_total_num_mbufs = 65535
        min_total_num_mbufs = 1025
        total_num_mbufs_types = [
            "total-num-mbufs=%d," % min_total_num_mbufs,
            "total-num-mbufs=%d,"
            % random.randint(min_total_num_mbufs + 1, max_total_num_mbufs),
            "total-num-mbufs=%d," % max_total_num_mbufs,
        ]

        port_num = len(port_types) if "port" in types else 1

        if "dev-pcap" in types:
            dump_types = dump_pcap_types
        elif "dev-iface" in types:
            dump_types = dump_iface_types
        else:
            dump_types = dump_pcap_types[:1]

        queue_num = len(queue_types) if "queue" in types else 1

        option_exds = [""]
        if "ring_size" in types:
            option_exds = ring_size_types[:]

        if "mbuf_size" in types:
            option_exds = mbuf_size_types[:]

        if "total_num_mbufs" in types:
            option_exds = total_num_mbufs_types[:]

        options = list()
        for port in port_types[:port_num]:
            for queue in queue_types[:queue_num]:
                for dump in dump_types:
                    for option_exd in option_exds:
                        opt = ((port + queue + dump[0]) + option_exd)[:-1]
                        msg = "command line option string should be <= 256"
                        self.verify(len(opt) <= 256, msg)
                        options.append([opt, dump[1]])

        return options

    def compare_pkts(
        self,
        refPkt=None,
        targetPkt=None,
        pkt_type=None,
        refPacketNo=0,
        targetPacketNo=0,
    ):
        """compare two pcap files packet content"""
        warning = None
        refObj = parsePacket(refPkt)
        warning = refObj.parse_pcap(number=refPacketNo)
        if warning:
            return warning
        targetObj = parsePacket(targetPkt)
        warning = targetObj.parse_pcap(number=targetPacketNo)
        if warning:
            return warning
        # remove some fields, which are filled by dpdk automatically
        # if packet is filled with `Padding`, remove this
        if "Padding" in list(targetObj.packetLayers.keys()):
            targetObj.packetLayers.pop("Padding")
        if len(refObj.packetLayers) != len(targetObj.packetLayers):
            refObj_layer = pformat(refObj.packetLayers)
            targetObj_layer = pformat(targetObj.packetLayers)
            self.logger.info(os.linesep + "refObj:    %s" % refObj_layer)
            self.logger.info(os.linesep + "targetObj: %s" % targetObj_layer)
            warning = "packet {0} layers are not as expected".format(targetPkt)
            return warning

        for layer in list(refObj.packetLayers.keys()):
            if layer not in list(targetObj.packetLayers.keys()):
                warning = "{0} has no [{1}] layer".format(targetPkt, layer)
                return warning

            if layer == "Raw":
                continue

            refLayerFields = refObj.packetLayers[layer]
            targetLayerFields = targetObj.packetLayers[layer]
            if len(refLayerFields) != len(targetLayerFields):
                warning = "{0} [{1}] layer has no expected fields".format(
                    targetPkt, layer
                )
                return warning

            for field in list(refLayerFields.keys()):
                if field == "src" or field == "dst":
                    continue
                if field not in list(targetLayerFields.keys()):
                    warning = ("{0} layer [{1}] " "has no [{2}] field").format(
                        targetPkt, layer, field
                    )
                    return warning
                if refLayerFields[field] != targetLayerFields[field]:
                    warning = (
                        "{0} [{1}] layer [{2}] " "field has no expected value"
                    ).format(targetPkt, layer, field)
                    return warning

        return warning

    def clear_ASLR(self):
        cmd = "echo 0 > /proc/sys/kernel/randomize_va_space"
        self.dut.alt_session.send_expect(cmd, "# ", timeout=10)
        time.sleep(2)

    def reset_ASLR(self):
        cmd = "echo 2 > /proc/sys/kernel/randomize_va_space"
        self.dut.alt_session.send_expect(cmd, "# ", timeout=10)
        time.sleep(4)

    def start_testpmd(self):
        self.dut.alt_session.send_expect(
            "rm -fr {0}/*".format(self.pdump_log), "# ", 10
        )
        if not self.is_dut_on_tester:
            self.tester.alt_session.send_expect(
                "rm -fr {0}/*".format(self.pdump_log), "# ", 10
            )
        param_opt = "--port-topology=chained"
        eal_param = "--file-prefix=test"
        self.testpmd.start_testpmd(
            "Default", param=param_opt, fixed_prefix=True, eal_param=eal_param
        )
        self.testpmd.execute_cmd("set fwd io")
        self.testpmd.execute_cmd("start")
        time.sleep(2)

    def stop_testpmd(self):
        self.testpmd.execute_cmd("stop")
        self.testpmd.quit()
        time.sleep(2)

    def start_tcpdump_iface(self, option):
        if (
            option["rx"][0] is not None
            and option["tx"][0] is not None
            and option["rx"][0] == option["tx"][0]
        ):
            if self.is_existed_on_crb(self.rxtx_pcap):
                self.dut.alt_session.send_expect("rm -f %s" % self.rxtx_pcap, "# ")
            cmd = self.tcpdump.format(self.rxtx_iface, self.rxtx_pcap)
            self.session_ex.send_expect(cmd, "# ")
        else:
            if option["rx"][0] is not None:
                if self.is_existed_on_crb(self.rx_pcap):
                    self.dut.alt_session.send_expect("rm -f %s" % self.rx_pcap, "# ")
                cmd = self.tcpdump.format(self.rx_iface, self.rx_pcap)
                self.session_ex.send_expect(cmd, "# ")

            if option["tx"][0] is not None:
                if self.is_existed_on_crb(self.tx_pcap):
                    self.dut.alt_session.send_expect("rm -f %s" % self.tx_pcap, "# ")
                cmd = self.tcpdump.format(self.tx_iface, self.tx_pcap)
                self.session_ex.send_expect(cmd, "# ")
        time.sleep(4)

    def stop_tcpdump_iface(self):
        self.dut.alt_session.send_expect("killall tcpdump", "# ", 5)
        time.sleep(2)

    def start_dpdk_pdump(self, option):
        length_limit = 256
        msg = ("pdump option string length should be less than {}").format(length_limit)
        self.verify(len(option) < length_limit, msg)
        self.dut.alt_session.send_expect(
            "rm -fr {0}/*".format(self.pdump_log), "# ", 20
        )
        if not self.is_dut_on_tester:
            self.tester.alt_session.send_expect(
                "rm -fr {0}/*".format(self.pdump_log), "# ", 20
            )
        cmd = self.dpdk_pdump + " '%s' >/dev/null 2>&1 &" % (option[0])
        self.session_ex.send_expect(cmd, "# ", 15)
        time.sleep(6)

    def check_pdump_ready(self, option):
        rx_dump_pcap = option["rx"][0]
        if rx_dump_pcap:
            self.verify(
                self.is_existed_on_crb(rx_dump_pcap),
                "{1} {0} is not ready".format(rx_dump_pcap, self.tool_name),
            )
        tx_dump_pcap = option["tx"][0]
        if tx_dump_pcap:
            self.verify(
                self.is_existed_on_crb(tx_dump_pcap),
                "{1} {0} is not ready".format(tx_dump_pcap, self.tool_name),
            )

    def stop_dpdk_pdump(self):
        self.dut.alt_session.send_expect("killall %s" % self.tool_name, "# ", 5)
        time.sleep(2)

    def packet_capture_dump_packets(self, pkt_type, number, **kwargs):
        self.logger.info("send <{}> packet".format(pkt_type))
        if pkt_type == "VLAN_UDP":
            self.testpmd.execute_cmd("vlan set filter off 0")
            self.testpmd.execute_cmd("vlan set filter off 1")
            self.testpmd.execute_cmd("start")
        # tester's port 0 and port 1 work under chained mode.
        port_0 = self.dut_ports[self.test_port0_id]
        port_1 = self.dut_ports[self.test_port1_id]
        # check send tx packet by port 0
        # send packet to dut and compare dpdk-pdump dump pcap with
        # scapy pcap file
        intf = self.tester.get_interface(self.tester.get_local_port(port_1))
        # prepare to catch replay packet in out port
        recPkt = os.path.join("/tmp", "sniff_%s.pcap" % intf)
        if os.path.exists(recPkt):
            os.remove(recPkt)
        if pkt_type == "LLDP":
            index = self.tester.tcpdump_sniff_packets(
                intf=intf, count=1, lldp_forbid=False
            )
        else:
            index = self.tester.tcpdump_sniff_packets(intf=intf, count=1)
        filename = "{}sniff_{}.pcap".format(self.tester.tmp_file, intf)
        self.tester.session.copy_file_from(filename, recPkt)
        # index = sniff_packets(intf, count=1, timeout=20, pcap=recPkt)
        pkt = Packet(pkt_type=pkt_type)
        if pkt_type == "VLAN_UDP":
            pkt.config_layer("dot1q", {"vlan": 20})
        src_mac = self.tester.get_mac(self.tester.get_local_port(port_0))
        pkt.config_layer("ether", {"src": src_mac})
        # save send packet in a pcap file
        refPkt = self.send_pcap % (pkt_type, "rx", number)
        if os.path.exists(refPkt):
            os.remove(refPkt)

        pkt.save_pcapfile(filename=refPkt)
        # send out test packet
        tester_port = self.tester.get_local_port(port_0)
        intf = self.tester.get_interface(tester_port)
        pkt.send_pkt(self.tester, tx_port=intf)
        # load pcap file caught by out port
        time.sleep(1)
        pkts = self.tester.load_tcpdump_sniff_packets(index)
        pkts.save_pcapfile(filename=recPkt)
        # load_sniff_packets(index)
        # compare pcap file received by out port with scapy reference
        # packet pcap file
        warning = self.compare_pkts(refPkt, recPkt, pkt_type)
        msg = "tcpdump rx Receive Packet error: {0}".format(warning)
        self.verify(not warning, msg)
        # check send tx packet by port 1
        # send packet to dut and compare dpdk-pdump dump pcap
        # with scapy pcap file
        intf = self.tester.get_interface(self.tester.get_local_port(port_0))
        # prepare to catch replay packet in out port
        recPkt = os.path.join("/tmp", "sniff_%s.pcap" % intf)
        if os.path.exists(recPkt):
            os.remove(recPkt)
        if pkt_type == "LLDP":
            index = self.tester.tcpdump_sniff_packets(
                intf=intf, count=1, lldp_forbid=False
            )
        else:
            index = self.tester.tcpdump_sniff_packets(intf=intf, count=1)
        pkt = Packet(pkt_type=pkt_type)
        if pkt_type == "VLAN_UDP":
            pkt.config_layer("dot1q", {"vlan": 20})
        src_mac = self.tester.get_mac(self.tester.get_local_port(port_1))
        pkt.config_layer("ether", {"src": src_mac})
        # save send packet in a pcap file
        refPkt = self.send_pcap % (pkt_type, "tx", number)
        if os.path.exists(refPkt):
            os.remove(refPkt)
        pkt.save_pcapfile(filename=refPkt)
        # pkt.pktgen.write_pcap(refPkt)
        # send out test packet
        tester_port = self.tester.get_local_port(port_1)
        intf = self.tester.get_interface(tester_port)
        pkt.send_pkt(self.tester, tx_port=intf)
        # load pcap file caught by out port
        time.sleep(1)
        pkts = self.tester.load_tcpdump_sniff_packets(index)
        pkts.save_pcapfile(filename=recPkt)
        # compare pcap file received by out port
        # with scapy reference packet pcap file
        warning = self.compare_pkts(refPkt, recPkt, pkt_type)
        msg = "tcpdump tx Receive Packet error: {0}".format(warning)
        self.verify(not warning, msg)

    def check_pdump_pcaps(self, pkt_type, number, **kwargs):
        rx_dump_pcap = kwargs["rx"][0]
        if rx_dump_pcap:
            self.verify(
                os.path.exists(rx_dump_pcap), "{0} doesn't exist".format(rx_dump_pcap)
            )
            # save send packet in a pcap file
            refPkt = self.send_pcap % (pkt_type, "rx", number)
            self.verify(os.path.exists(refPkt), "{0} doesn't exist".format(refPkt))
            # compare pcap file dumped by dpdk-pdump
            # with scapy reference packet pcap file
            warning = self.compare_pkts(
                refPkt, rx_dump_pcap, pkt_type, targetPacketNo=self.rx_packet_pos
            )
            if kwargs["rx"][1] == 2:
                self.rx_packet_pos += kwargs["rx"][1]
            else:
                self.rx_packet_pos += 1
            self.verify(
                warning is None, "dpdk-pdump rx dump packet error: {0}".format(warning)
            )
            msg = "pdump rx {0} packet content is correct".format(pkt_type)
            self.logger.info(msg)
        tx_dump_pcap = kwargs["tx"][0]
        if tx_dump_pcap:
            self.verify(
                os.path.exists(tx_dump_pcap), "{0} doesn't exist".format(tx_dump_pcap)
            )
            # set send packet
            refPkt = self.send_pcap % (pkt_type, "tx", number)
            self.verify(os.path.exists(refPkt), "{0} doesn't exist".format(refPkt))
            # compare pcap file dumped by dpdk-pdump
            # with scapy reference packet pcap file
            if kwargs["tx"][1] == 2 and self.tx_packet_pos == 0:
                self.tx_packet_pos = 1
            warning = self.compare_pkts(
                refPkt, tx_dump_pcap, pkt_type, targetPacketNo=self.tx_packet_pos
            )
            if kwargs["tx"][1] == 2:
                self.tx_packet_pos += kwargs["tx"][1]
            else:
                self.tx_packet_pos += 1
            msg = "dpdk-pdump tx dump packet error: {0}".format(warning)
            self.verify(warning is None, msg)
            msg = "pdump tx {0} packet content is correct".format(pkt_type)
            self.logger.info(msg)

    def packet_capture_test_packets(self, option):
        self.clear_ASLR()
        self.start_testpmd()
        self.start_dpdk_pdump(option)
        if self.dev_iface_flag:
            self.start_tcpdump_iface(option[1])
        self.check_pdump_ready(option[1])
        for number, packet_type in enumerate(self.get_packet_types()):
            self.packet_capture_dump_packets(packet_type, number, **option[1])
            time.sleep(2)
        if self.dev_iface_flag:
            self.stop_tcpdump_iface()
        if not self.is_dut_on_tester:
            # copy rx pdump data from dut
            if self.is_existed_on_crb(self.rx_pcap):
                if os.path.exists(self.rx_pcap):
                    os.remove(self.rx_pcap)
                self.dut.session.copy_file_from(self.rx_pcap, self.rx_pcap)
            # copy tx pdump data from dut
            if self.is_existed_on_crb(self.tx_pcap):
                if os.path.exists(self.tx_pcap):
                    os.remove(self.tx_pcap)
                self.dut.session.copy_file_from(self.tx_pcap, self.tx_pcap)
        self.stop_dpdk_pdump()
        self.stop_testpmd()
        self.reset_ASLR()

        self.rx_packet_pos = 0
        self.tx_packet_pos = 0
        for number, packet_type in enumerate(self.get_packet_types()):
            self.check_pdump_pcaps(packet_type, number, **option[1])
            time.sleep(2)

    def packet_capture_test_options(self, pdump_options):
        try:
            for option in pdump_options:
                self.packet_capture_test_packets(option)
            self.exit_flag = True
        except Exception as e:
            self.logger.error(traceback.format_exc())
            raise VerifyFailure(e)

    def test_pdump_port(self):
        """
        test different port options::
        *. port=<dut port id>
        *. device_id=<dut pci address>
        """
        port_id = self.test_port0_id
        port_name = self.dut.ports_info[port_id]["intf"]
        port_pci = self.dut.ports_info[port_id]["pci"]
        test_types = ["port"]
        options = self.generate_options(port_id, port_pci, port_name, test_types)
        self.packet_capture_test_options(options)

    def test_pdump_dev_pcap(self):
        """
        test different dump options with pcap files as output::
        *. tx-dev=/xxx/pdump-tx.pcap,rx-dev=/xxx/pdump-rx.pcap
        *. rx-dev=/xxx/pdump-rx.pcap
        *. tx-dev=/xxx/pdump-tx.pcap
        """
        port_id = self.test_port0_id
        port_name = self.dut.ports_info[port_id]["intf"]
        port_pci = self.dut.ports_info[port_id]["pci"]
        test_types = ["dev-pcap"]
        options = self.generate_options(port_id, port_pci, port_name, test_types)
        self.packet_capture_test_options(options)

    def test_pdump_dev_iface(self):
        """
        test different dump options with interfaces as output::
        *. tx-dev=<dut tx port name>,rx-dev=<dut rx port name>
        *. rx-dev=<dut rx port name>
        *. tx-dev=<dut tx port name>
        """
        self.get_dut_iface_with_kernel_driver()
        port_id = self.test_port0_id
        port_name = self.dut.ports_info[port_id]["intf"]
        port_pci = self.dut.ports_info[port_id]["pci"]
        test_types = ["dev-iface"]
        self.dev_iface_flag = True
        options = self.generate_options(port_id, port_pci, port_name, test_types)
        self.packet_capture_test_options(options)

    def test_pdump_queue(self):
        """
        test different queue options::
        *. first queue:
          queue=0
        *. all:
          queue=*
        """
        port_id = self.test_port0_id
        port_name = self.dut.ports_info[port_id]["intf"]
        port_pci = self.dut.ports_info[port_id]["pci"]
        test_types = ["queue"]
        options = self.generate_options(port_id, port_pci, port_name, test_types)
        self.packet_capture_test_options(options)

    def test_pdump_ring_size(self):
        """
        test ring size option, set value within 2^[1~27]
        """
        port_id = self.test_port0_id
        port_name = self.dut.ports_info[port_id]["intf"]
        port_pci = self.dut.ports_info[port_id]["pci"]
        test_types = ["ring_size"]
        options = self.generate_options(port_id, port_pci, port_name, test_types)
        self.packet_capture_test_options(options)

    def test_pdump_mbuf_size(self):
        """
        test mbuf size option, set value within [252~50000].
        min value is decided by single packet size,
        max value is decided by test platform memory size.
        """
        port_id = self.test_port0_id
        port_name = self.dut.ports_info[port_id]["intf"]
        port_pci = self.dut.ports_info[port_id]["pci"]
        test_types = ["mbuf_size"]

        options = self.generate_options(port_id, port_pci, port_name, test_types)
        self.packet_capture_test_options(options)

    def test_pdump_total_num_mbufs(self):
        """
        test total-num-mbufs option, set value within [1025~65535]
        """
        port_id = self.test_port0_id
        port_name = self.dut.ports_info[port_id]["intf"]
        port_pci = self.dut.ports_info[port_id]["pci"]
        test_types = ["total_num_mbufs"]
        options = self.generate_options(port_id, port_pci, port_name, test_types)
        self.packet_capture_test_options(options)

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(
            self.target == "x86_64-native-linuxapp-gcc",
            "only support x86_64-native-linuxapp-gcc",
        )
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) == 2, "Insufficient ports for testing")
        self.verify_supported_nic()
        self.test_port0_id = 0
        self.test_port1_id = 1
        # used for save log
        self.pdump_log = os.sep.join(["/tmp", "pdumpLog"])
        if not self.is_existed_on_crb(self.pdump_log):
            cmd = "mkdir -p {0}".format(self.pdump_log)
            self.dut.alt_session.send_expect(cmd, "# ")
        if not self.is_dut_on_tester and not self.is_existed_on_crb(
            self.pdump_log, crb="tester"
        ):
            cmd = "mkdir -p {0}".format(self.pdump_log)
            self.tester.alt_session.send_expect(cmd, "# ")
        # secondary process (dpdk-pdump)
        self.dut_dpdk_pdump_dir = self.dut.apps_name["pdump"]
        self.tool_name = self.dut_dpdk_pdump_dir.split("/")[-1]
        self.session_ex = self.dut.new_session(self.tool_name)
        self.dpdk_pdump = self.dut_dpdk_pdump_dir + " -v --file-prefix=test -- --pdump "
        self.send_pcap = os.sep.join([self.pdump_log, "scapy_%s_%s_%d.pcap"])
        self.rx_pcap = os.sep.join([self.pdump_log, "pdump-rx.pcap"])
        self.tx_pcap = os.sep.join([self.pdump_log, "pdump-tx.pcap"])
        self.rxtx_pcap = os.sep.join([self.pdump_log, "pdump-rxtx.pcap"])
        self.rx_iface = None
        self.tx_iface = None
        self.rxtx_iface = None
        self.rx_packet_pos = 0
        self.tx_packet_pos = 0
        self.dev_iface_flag = False
        # primary process
        self.testpmd = PmdOutput(self.dut)
        # False: reduce test items for regression testing,
        #        shut off base test environment checking
        # True: make a full range testing
        self.full_test = True
        # used on daily testing to avoid long time running
        self.pkt_index = None
        # get tcpdump options
        self.get_tcpdump_options()

    def set_up(self):
        """
        Run before each test case.
        """
        self.exit_flag = False

    def tear_down(self):
        """
        Run after each test case.
        """
        if not self.exit_flag:
            self.stop_dpdk_pdump()
            self.dut.alt_session.send_expect("killall testpmd", "# ")
            self.tester.alt_session.send_expect("killall tcpdump", "# ")
            self.reset_ASLR()
        if self.dev_iface_flag:
            self.stop_tcpdump_iface()
            self.dev_iface_flag = False

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if hasattr(self, "session_ex") and self.session_ex:
            self.reset_ASLR()
            self.session_ex.close()
            self.session_ex = None
        self.dut.kill_all()

# BSD LICENSE
#
# Copyright(c) 2010-2015 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Generic packet create, transmit and analyze module
Base on scapy(python program for packet manipulation)
"""

from socket import AF_INET6
from importlib import import_module
from scapy.all import *
# load extension layers
exec_file = os.path.realpath(__file__)
DTS_PATH = exec_file.replace('/framework/packet.py', '')
# exec_file might be .pyc file, if so, remove 'c'.
TMP_PATH = DTS_PATH[:-1] + '/output/tmp/pcap/' if exec_file.endswith('.pyc') else DTS_PATH + '/output/tmp/pcap/'
if not os.path.exists(TMP_PATH):
    os.system('mkdir -p %s' % TMP_PATH)

DEP_FOLDER = DTS_PATH + '/dep'
sys.path.append(DEP_FOLDER)
sys.path.append(DEP_FOLDER + '/scapy_modules')

from utils import convert_ip2int
from utils import convert_int2ip

scapy_modules_required = {'gtp': ['GTP_U_Header', 'GTPPDUSessionContainer'],
                          'lldp': ['LLDPDU', 'LLDPDUManagementAddress'], 'Dot1BR': ['Dot1BR'], 'pfcp': ['PFCP'],
                          'nsh': ['NSH'], 'igmp': ['IGMP'], 'mpls': ['MPLS'], 'sctp': ['SCTP', 'SCTPChunkData']}
local_modules = [m[:-3] for m in os.listdir(DEP_FOLDER + '/scapy_modules') if (m.endswith('.py') and not m.startswith('__'))]

for m in scapy_modules_required:
    try:
        if m in local_modules:
            module = import_module(m)
            for clazz in scapy_modules_required[m]:
                locals().update({clazz: getattr(module, clazz)})
        else:
            if m == 'sctp':
                module = import_module(f'scapy.layers.{m}')
                for clazz in scapy_modules_required[m]:
                    locals().update({clazz: getattr(module, clazz)})
            else:
                module = import_module(f'scapy.contrib.{m}')
                for clazz in scapy_modules_required[m]:
                    locals().update({clazz: getattr(module, clazz)})
    except Exception as e:
        print(e)

def get_scapy_module_impcmd():
    cmd_li = list()
    for m in scapy_modules_required:
        if m in local_modules:
            cmd_li.append(f'from {m} import {",".join(scapy_modules_required[m])}')
        else:
            cmd_li.append(f'from scapy.contrib.{m} import {",".join(scapy_modules_required[m])}')
    return ';'.join(cmd_li)

SCAPY_IMP_CMD = get_scapy_module_impcmd()

# packet generator type should be configured later
PACKETGEN = "scapy"

LayersTypes = {
    "L2": ['ether', 'vlan', 'etag', '1588', 'arp', 'lldp', 'mpls', 'nsh'],
    # ipv4_ext_unknown, ipv6_ext_unknown
    "L3": ['ipv4', 'ipv4ihl', 'ipv6', 'ipv4_ext', 'ipv6_ext', 'ipv6_ext2', 'ipv6_frag'],
    "L4": ['tcp', 'udp', 'frag', 'sctp', 'icmp', 'nofrag'],
    # The NVGRE pkt format is
    # <'ether type'=0x0800 'version'=4, 'protocol'=47 'protocol type'=0x6558>
    # or
    # <'ether type'=0x86DD 'version'=6, 'next header'=47 'protocol type'=0x6558'>
    # The GRE pkt format is
    # <'ether type'=0x0800 'version'=4, 'protocol'=17 'destination port'=4789>
    # or
    # <'ether type'=0x86DD 'version'=6, 'next header'=17 'destination port'=4789>
    "TUNNEL": ['ip', 'gre', 'vxlan', 'nvgre', 'geneve', 'grenat'],
    "INNER L2": ['inner_mac', 'inner_vlan'],
    # inner_ipv4_unknown, inner_ipv6_unknown
    "INNER L3": ['inner_ipv4', 'inner_ipv4_ext', 'inner_ipv6', 'inner_ipv6_ext'],
    "INNER L4": ['inner_tcp', 'inner_udp', 'inner_frag', 'inner_sctp', 'inner_icmp', 'inner_nofrag'],
    "PAYLOAD": ['raw']
}

# Saved background sniff process id
SNIFF_PIDS = {}

# Saved packet generator process id
# used in pktgen or tgen
PKTGEN_PIDS = {}

# default filter for LLDP packet
LLDP_FILTER = {'layer': 'ether', 'config': {'type': 'not lldp'}}


class scapy(object):
    SCAPY_LAYERS = {
        'ether': Ether(dst="ff:ff:ff:ff:ff:ff"),
        'vlan': Dot1Q(),
        'etag': Dot1BR(),
        '1588': Ether(type=0x88f7),
        'arp': ARP(),
        'ipv4': IP(),
        'ipv4ihl': IP(ihl=10),
        'ipv4_ext': IP(frag=5),
        'ipv6': IPv6(src="::1"),
        'ipv6_ext': IPv6(src="::1", nh=43) / IPv6ExtHdrRouting(),
        'ipv6_ext2': IPv6() / IPv6ExtHdrRouting(),
        'udp': UDP(),
        'tcp': TCP(),
        'sctp': SCTP(),
        'icmp': ICMP(),
        'gre': GRE(),
        'raw': Raw(),
        'vxlan': VXLAN(),
        'nsh': NSH(),
        'mpls': MPLS(),

        'inner_mac': Ether(),
        'inner_vlan': Dot1Q(),
        'inner_ipv4': IP(),
        'inner_ipv4_ext': IP(),
        'inner_ipv6': IPv6(src="::1"),
        'inner_ipv6_ext': IPv6(src="::1"),

        'inner_tcp': TCP(),
        'inner_udp': UDP(),
        'inner_sctp': SCTP(),
        'inner_icmp': ICMP(),

        'lldp': LLDPDU() / LLDPDUManagementAddress(_length=6, _management_address_string_length=6,management_address=':12') / IP(),
        'ip_frag': IP(frag=5),
        'ipv6_frag': IPv6(src="::1") / IPv6ExtHdrFragment(),
        'ip_in_ip': IP() / IP(),
        'ip_in_ip_frag': IP() / IP(frag=5),
        'ipv6_in_ip': IP() / IPv6(src="::1"),
        'ipv6_frag_in_ip': IP() / IPv6(src="::1", nh=44) / IPv6ExtHdrFragment(),
        'nvgre': GRE(key_present=1,proto=0x6558,key=0x00000100),
        'geneve': "Not Implement",
    }

    def __init__(self):
        self.pkt = None
        self.pkts = list()

    def append_pkts(self):
        self.pkts.append(self.pkt)

    def update_pkts(self):
        if not self.pkts:  # update pkt to a null pkt list.
            self.pkts.append(self.pkt)
        else:
            self.pkts[-1] = self.pkt

    def assign_pkt(self, pkt):
        self.pkt = pkt

    def add_layers(self, layers):
        self.pkt = None
        for layer in layers:
            if self.pkt is not None:
                self.pkt = self.pkt / self.SCAPY_LAYERS[layer]
            else:
                self.pkt = self.SCAPY_LAYERS[layer]

    def ether(self, pkt_layer, dst="ff:ff:ff:ff:ff:ff", src="00:00:20:00:00:00", type=None):
        if pkt_layer.name != "Ethernet":
            return
        pkt_layer.dst = dst
        pkt_layer.src = src
        if type is not None:
            pkt_layer.type = type

    def vlan(self, pkt_layer, vlan, prio=0, type=None):
        if pkt_layer.name != "802.1Q":
            return
        pkt_layer.vlan = int(vlan)
        pkt_layer.prio = prio
        if type is not None:
            pkt_layer.type = type

    def strip_vlan(self, element, p_index=0):
        value = None

        if self.pkts[p_index].haslayer('Dot1Q') is 0:
            return None

        if element == 'vlan':
            value = int(str(self.pkts[p_index][Dot1Q].vlan))
        return value

    def etag(self, pkt_layer, ECIDbase=0, prio=0, type=None):
        if pkt_layer.name != "802.1BR":
            return
        pkt_layer.ECIDbase = int(ECIDbase)
        pkt_layer.prio = prio
        if type is not None:
            pkt_layer.type = type

    def strip_etag(self, element, p_index=0):
        value = None

        if self.pkts[p_index].haslayer('Dot1BR') is 0:
            return None

        if element == 'ECIDbase':
            value = int(str(self.pkts[p_index][Dot1BR].ECIDbase))
        return value

    def strip_layer2(self, element, p_index=0):
        value = None
        layer = self.pkts[p_index].getlayer(0)
        if layer is None:
            return None

        if element == 'src':
            value = layer.src
        elif element == 'dst':
            value = layer.dst
        elif element == 'type':
            value = layer.type

        return value

    def strip_layer3(self, element, p_index=0):
        value = None
        layer = self.pkts[p_index].getlayer(1)
        if layer is None:
            return None

        if element == 'src':
            value = layer.src
        elif element == 'dst':
            value = layer.dst
        else:
            value = layer.getfieldval(element)

        return value

    def strip_layer4(self, element, p_index=0):
        value = None
        layer = self.pkts[p_index].getlayer(2)
        if layer is None:
            return None

        if element == 'src':
            value = layer.sport
        elif element == 'dst':
            value = layer.dport
        else:
            value = layer.getfieldval(element)

        return value

    def ipv4(self, pkt_layer, frag=0, src="127.0.0.1", proto=None, tos=0, dst="127.0.0.1", chksum=None, len=None,
             version=4, flags=None, ihl=None, ttl=64, id=1, options=None):
        pkt_layer.frag = frag
        pkt_layer.src = src
        if proto is not None:
            pkt_layer.proto = proto
        pkt_layer.tos = tos
        pkt_layer.dst = dst
        if chksum is not None:
            pkt_layer.chksum = chksum
        if len is not None:
            pkt_layer.len = len
        pkt_layer.version = version
        if flags is not None:
            pkt_layer.flags = flags
        if ihl is not None:
            pkt_layer.ihl = ihl
        pkt_layer.ttl = ttl
        pkt_layer.id = id
        if options is not None:
            pkt_layer.options = options

    def ipv6(self, pkt_layer, version=6, tc=0, fl=0, plen=0, nh=0, hlim=64, src="::1", dst="::1"):
        """
        Configure IPv6 protocol.
        """
        pkt_layer.version = version
        pkt_layer.tc = tc
        pkt_layer.fl = fl
        if plen:
            pkt_layer.plen = plen
        if nh:
            pkt_layer.nh = nh
        pkt_layer.src = src
        pkt_layer.dst = dst
        pkt_layer.hlim = hlim

    def tcp(self, pkt_layer, src=53, dst=53, flags=0, len=None, chksum=None):
        pkt_layer.sport = src
        pkt_layer.dport = dst
        if flags is not None:
            pkt_layer.flags = flags
        if len is not None:
            pkt_layer.len = len
        if chksum is not None:
            pkt_layer.chksum = chksum

    def udp(self, pkt_layer, src=53, dst=53, len=None, chksum=None):
        pkt_layer.sport = src
        pkt_layer.dport = dst
        if len is not None:
            pkt_layer.len = len
        if chksum is not None:
            pkt_layer.chksum = chksum

    def sctp(self, pkt_layer, src=53, dst=53, tag=None, len=None, chksum=None):
        pkt_layer.sport = src
        pkt_layer.dport = dst
        if tag is not None:
            pkt_layer.tag = tag
        if len is not None:
            pkt_layer.len = len
        if chksum is not None:
            pkt_layer.chksum = chksum

    def raw(self, pkt_layer, payload=None):
        if payload is not None:
            pkt_layer.load = ''
            for hex1, hex2 in payload:
                pkt_layer.load += struct.pack("=B", int('%s%s' % (hex1, hex2), 16))

    def gre(self, pkt_layer, proto=None):
        if proto is not None:
            pkt_layer.proto = proto

    def vxlan(self, pkt_layer, vni=0):
        pkt_layer.vni = vni

    def nsh(self, pkt_layer, ver=0, oam=0, critical=0, reserved=0, len=0, mdtype=1, nextproto=3,
            nsp=0x0, nsi=1, npc=0x0, nsc=0x0, spc=0x0, ssc=0x0):
        pkt_layer.Ver = ver
        pkt_layer.OAM = oam
        pkt_layer.Critical = critical
        pkt_layer.Reserved = reserved
        if len != 0:
            pkt_layer.Len = len
        pkt_layer.MDType = mdtype
        pkt_layer.NextProto = nextproto
        pkt_layer.NSP = nsp
        pkt_layer.NSI = nsi
        if mdtype == 1:
            pkt_layer.NPC = npc
            pkt_layer.NSC = nsc
            pkt_layer.SPC = spc
            pkt_layer.SSC = ssc

    def mpls(self, pkt_layer, label=0, cos=0, s=0, ttl=64):
        pkt_layer.label = label
        pkt_layer.cos = cos
        pkt_layer.s = s
        pkt_layer.ttl = ttl


class Packet(object):
    """
    Module for config/create packet
    Based on scapy module
    Usage: assign_layers([layers list])
           config_layer('layername', {layer config})
           ...
    """
    def_packet = {
        'TIMESYNC': {'layers': ['ether', 'raw'], 'cfgload': False},
        'ARP': {'layers': ['ether', 'arp'], 'cfgload': False},
        'LLDP': {'layers': ['ether', 'lldp'], 'cfgload': False},
        'IP_RAW': {'layers': ['ether', 'ipv4', 'raw'], 'cfgload': True},
        'TCP': {'layers': ['ether', 'ipv4', 'tcp', 'raw'], 'cfgload': True},
        'UDP': {'layers': ['ether', 'ipv4', 'udp', 'raw'], 'cfgload': True},
        'VLAN_UDP': {'layers': ['ether', 'vlan', 'ipv4', 'udp', 'raw'], 'cfgload': True},
        'ETAG_UDP': {'layers': ['ether', 'etag', 'ipv4', 'udp', 'raw'], 'cfgload': True},
        'SCTP': {'layers': ['ether', 'ipv4', 'sctp', 'raw'], 'cfgload': True},
        'IPv6_TCP': {'layers': ['ether', 'ipv6', 'tcp', 'raw'], 'cfgload': True},
        'IPv6_UDP': {'layers': ['ether', 'ipv6', 'udp', 'raw'], 'cfgload': True},
        'IPv6_SCTP': {'layers': ['ether', 'ipv6', 'sctp', 'raw'], 'cfgload': True},
    }

    def __init__(self, pkt_str=None, **options):
        """
        pkt_type: description of packet type
                  defined in def_packet
        args: specify a packet with a string explicitly, will ignore options
        options: special option for Packet module
                 pkt_len: length of network packet
                 ran_payload: whether payload of packet is random
                 pkt_file:
                 pkt_gen: packet generator type
                          now only support scapy
        """
        self.pkt_opts = options
        self.pkt_layers = []

        if 'pkt_gen' in list(self.pkt_opts.keys()):
            if self.pkt_opts['pkt_gen'] == 'scapy':
                self.pktgen = scapy()
            else:
                print("Not support other pktgen yet!!!")
        else:
            self.pktgen = scapy()

        if pkt_str is not None and type(pkt_str) == str:
            self._scapy_str_to_pkt(pkt_str)
        elif len(options) != 0:
            self._add_pkt(self.pkt_opts)
        if self.pktgen.pkt is not None:
            self.pktgen.append_pkts()

    def __len__(self):
        return len(self.pktgen.pkts)

    def __getitem__(self, item):
        return self.pktgen.pkts[item]

    def _add_pkt(self, options):
        """
        :param options: packt configuration, dictionary type
        :return:
        """
        self.pkt_len = 64
        self.pkt_type = "UDP"
        if 'pkt_type' in list(options.keys()):
            self.pkt_type = options['pkt_type']

        if self.pkt_type in list(self.def_packet.keys()):
            self.pkt_layers = self.def_packet[self.pkt_type]['layers']
            self.pkt_cfgload = self.def_packet[self.pkt_type]['cfgload']
            if "IPv6" in self.pkt_type:
                self.pkt_len = 128
        else:
            self._load_pkt_layers()

        if 'pkt_len' in list(options.keys()):
            self.pkt_len = options['pkt_len']

        self._load_assign_layers()

    def _load_assign_layers(self):
        # assign layer
        self.assign_layers()

        # config special layer
        self.config_def_layers()

        # handle packet options
        payload_len = self.pkt_len - len(self.pktgen.pkt) - 4

        # if raw data has not been configured and payload should configured
        if hasattr(self, 'configured_layer_raw') is False and self.pkt_cfgload is True:
            payload = []
            raw_confs = {}
            if 'ran_payload' in list(self.pkt_opts.keys()):
                for loop in range(payload_len):
                    payload.append("%02x" % random.randrange(0, 255))
            else:
                for loop in range(payload_len):
                    payload.append('58')  # 'X'

            raw_confs['payload'] = payload
            self.config_layer('raw', raw_confs)

    def _scapy_str_to_pkt(self, scapy_str):
        """

        :param scapy_str: packet str, eg. 'Ether()/IP()/UDP()'
        :return: None
        """
        layer_li = [re.sub('\(.*?\)', '', i) for i in scapy_str.split('/')]
        self.pkt_type = '_'.join(layer_li)
        self._load_pkt_layers()
        self.pktgen.assign_pkt(scapy_str)

    def append_pkt(self, args=None, **kwargs):
        """
        :param args: take str type as pkt to append
        :param kwargs: take dictory type as pkt to append
        :return: None
        """
        if isinstance(args, str):
            self._scapy_str_to_pkt(args)
        elif isinstance(kwargs, dict):
            self.pkt_opts = kwargs
            if hasattr(self, 'configured_layer_raw'):
                delattr(self, 'configured_layer_raw')
            self._add_pkt(kwargs)
        self.pktgen.append_pkts()

    def update_pkt_str(self, pkt):
        self._scapy_str_to_pkt(pkt)
        self.pktgen.append_pkts()

    def update_pkt_dict(self, pkt):
        self.pkt_opts = pkt
        if hasattr(self, 'configured_layer_raw'):
            delattr(self, 'configured_layer_raw')
        self._add_pkt(pkt)
        self.pktgen.append_pkts()

    def update_pkt(self, pkts):
        """
        update pkts to packet object
        :param pkts: pkts to update
        :type str|dict|list
        :return: None
        """
        self.pktgen = scapy()
        self.pkt_layers = []
        if isinstance(pkts, str):
            self.update_pkt_str(pkts)
        elif isinstance(pkts, dict):
            self.update_pkt_dict(pkts)
        elif isinstance(pkts, list):
            for i in pkts:
                if isinstance(i, str):
                    try:
                        self.update_pkt_str(i)
                    except:
                        print(("warning: packet %s update failed" % i))
                elif isinstance(i, dict):
                    try:
                        self.update_pkt_dict(i)
                    except:
                        print(("warning: packet %s update failed" % i))
                else:
                    print(("packet {} is not acceptable".format(i)))

    def generate_random_pkts(self, dstmac=None, pktnum=100, random_type=None, ip_increase=True, random_payload=False,
                             options=None):
        """
        # generate random packets
        :param dstmac: specify the dst mac
        :param pktnum: packet number to generate
        :param random_type: specify random packet type
        :param ip_increase: auto increase ip value
        :param random_payload: if True, generate random packets with random payload
        :param options: packet layer configuration
        :return: None
        """

        random_type = ['TCP', 'UDP', 'IPv6_TCP', 'IPv6_UDP'] if random_type is None else random_type
        options = {'ip': {'src': '192.168.0.1', 'dst': '192.168.1.1'},
                   'layers_config': []} if options is None else options
        # give a default value to ip
        try:
            src_ip_num = convert_ip2int(options['ip']['src'])
        except:
            src_ip_num = 0
        try:
            dst_ip_num = convert_ip2int(options['ip']['dst'])
        except:
            dst_ip_num = 0

        for i in range(pktnum):
            # random the packet type
            self.pkt_type = random.choice(random_type)
            self.pkt_layers = self.def_packet[self.pkt_type]['layers']
            self.check_layer_config()
            self.pktgen.add_layers(self.pkt_layers)
            # hardcode src/dst port for some protocol may cause issue
            if "TCP" in self.pkt_type:
                self.config_layer('tcp', {'src': 65535, 'dst': 65535})
            if "UDP" in self.pkt_type:
                self.config_layer('udp', {'src': 65535, 'dst': 65535})
            if 'layers_config' in options:
                self.config_layers(options['layers_config'])
            if dstmac:
                self.config_layer('ether', {'dst': '%s' % dstmac})
            # generate auto increase dst ip packet
            if ip_increase:
                if 'v6' in self.pkt_type:
                    dstip = convert_int2ip(dst_ip_num, ip_type=6)
                    srcip = convert_int2ip(src_ip_num, ip_type=6)
                    self.config_layer('ipv6', config={'dst': '%s' % (dstip), 'src': '%s' % srcip})
                else:
                    dstip = convert_int2ip(dst_ip_num, ip_type=4)
                    srcip = convert_int2ip(src_ip_num, ip_type=4)
                    self.config_layer('ipv4', config={'dst': '%s' % (dstip), 'src': '%s' % srcip})
                dst_ip_num += 1
            # generate random payload of packet
            if random_payload and self.def_packet[self.pkt_type]['cfgload']:
                # TCP packet has a default flags S, packet should not load data, so set it to A if has payload
                if 'TCP' in self.pkt_type:
                    self.config_layer('tcp', {'src': 65535, 'dst': 65535, 'flags': 'A'})

                payload_len = random.randint(64, 100)
                payload = []
                for _ in range(payload_len):
                    payload.append("%02x" % random.randrange(0, 255))
                self.config_layer('raw', config={'payload': payload})
            self.pktgen.append_pkts()

    def save_pcapfile(self, crb=None, filename='saved_pkts.pcap'):
        """

        :param crb: session or crb object
        :param filename: location and name for packets to be saved
        :return: None
        """
        # save pkts to pcap file to local path, then copy to remote tester tmp directory,
        if crb:
            trans_path = crb.tmp_file
            file_name = filename
            if os.path.isabs(filename):  # check if the given filename with a abs path
                file_dir = os.path.dirname(filename)
                out = crb.send_expect('ls -d %s' % file_dir, '# ', verify=True)
                if not isinstance(out, str):
                    raise Exception('%s may not existed on %s' % (file_dir, crb.name))
                wrpcap(filename, self.pktgen.pkts)
                trans_path = os.path.abspath(filename)
                file_name = filename.split(os.path.sep)[-1]
            # write packets to local tmp path $dts/ouput/tmp/pcap/
            wrpcap(TMP_PATH + file_name, self.pktgen.pkts)
            # copy to remote tester tmp path /tmp/tester
            crb.session.copy_file_to(TMP_PATH + file_name, trans_path)
        else:
            wrpcap(filename, self.pktgen.pkts)

    def read_pcapfile(self, filename, crb=None):
        """

        :param filename: packet to be read from
        :param crb: session or crb object
        :return: scapy type packet
        """
        # read pcap file from local or remote, then append to pkts list
        # if crb, read pakcet from remote server, else read from local location
        if crb:
            out = crb.send_expect('ls -d %s' % filename, '# ', verify=True)
            if not isinstance(out, str):
                raise Exception('%s may not existed on %s' % (filename, crb.name))
            crb.session.copy_file_from(filename, TMP_PATH)
            p = rdpcap(TMP_PATH + filename.split(os.path.sep)[-1])
        else:
            p = rdpcap(filename)
        if len(p) == 0:
            return None
        self.pktgen.assign_pkt(p[-1])
        for i in p:
            self.pktgen.pkts.append(i)
        return p

    def send_pkt_bg_with_pcapfile(self, crb, tx_port='', count=1, loop=0, inter=0):
        """
        send packet background with a pcap file, got an advantage in sending a large number of packets
        :param crb: session or crb object
        :param tx_port: ether to send packet
        :param count: send times
        :param loop: send packet in a loop
        :param inter: interval time per packet
        :return: send session
        """
        if crb.name != 'tester':
            raise Exception('crb should be tester')
        wrpcap('_', self.pktgen.pkts)
        file_path = '/tmp/%s.pcap' % tx_port
        scapy_session_bg = crb.prepare_scapy_env()
        scapy_session_bg.copy_file_to('_', file_path)
        scapy_session_bg.send_expect('pkts = rdpcap("%s")' % file_path, '>>> ')
        scapy_session_bg.send_command('sendp(pkts, iface="%s",count=%s,loop=%s,inter=%s)' % (tx_port, count, loop, inter))
        return scapy_session_bg

    def _recompose_pkts_str(self, pkts_str):
        method_pattern = re.compile('<.+?>')
        method_li = method_pattern.findall(pkts_str)
        for i in method_li:
            pkts_str = method_pattern.sub(i.strip('<>')+'()', pkts_str, count=1)
        return pkts_str

    # use the GRE to configure the nvgre package
    # the field key last Byte configure the reserved1 of NVGRE, first 3 Bytes configure the TNI value of NVGRE
    def transform_nvgre_layer(self, pkt_str):
        tni = re.search('TNI\s*=\s*(0x)*(\d*)', pkt_str)
        if tni is None:
            nvgre = 'GRE(key_present=1,proto=0x6558,key=0x00000100)'
        else:
            tni = int(tni.group(2))
            tni = tni<<8
            nvgre = 'GRE(key_present=1,proto=0x6558,key=%d)' % tni
        pkt_str = re.sub(r'NVGRE\(\)|NVGRE\(TNI=\s*(0x)*\d*\)', nvgre, pkt_str)
        return pkt_str

    def gernerator_pkt_str(self):
        pkt_str_list = []
        for p in self.pktgen.pkts:
            if not isinstance(p, str):
                p_str = p.command()
            else:
                p_str = p
            # process the NVGRE
            if 'NVGRE' in p_str:
                p_str = self.transform_nvgre_layer(p_str)
            pkt_str_list.append(p_str)
        return '[' + ','.join(pkt_str_list) + ']'

    def send_pkt(self, crb, tx_port='', count=1, interval=0, timeout=120):
        p_str = self.gernerator_pkt_str()
        pkts_str = self._recompose_pkts_str(pkts_str=p_str)
        cmd = 'sendp(' + pkts_str + f',iface="{tx_port}",count={count},inter={interval},verbose=False)'
        if crb.name == 'tester':
            crb.scapy_session.send_expect(cmd, '>>> ', timeout=timeout)
        elif crb.name.startswith("tester_scapy"):
            crb.send_expect(cmd, '>>> ', timeout=timeout)
        else:
            raise Exception("crb should be tester\'s session and initialized")

    def send_pkt_bg(self, crb, tx_port='', count=-1, interval=0, loop=1):
        if crb.name != 'tester':
            raise Exception('crb should be tester')
        scapy_session_bg = crb.prepare_scapy_env()
        p_str = self.gernerator_pkt_str()
        pkts_str = self._recompose_pkts_str(pkts_str=p_str)
        cmd = 'sendp(' + pkts_str + f',iface="{tx_port}",count={count},inter={interval},loop={loop},verbose=False)'
        scapy_session_bg.send_command(cmd)
        return scapy_session_bg

    @staticmethod
    def stop_send_pkt_bg(session):
        # stop sending action
        session.send_expect('^C', '>>> ')

    def check_layer_config(self):
        """
        check the format of layer configuration
        every layer should has different check function
        """
        for layer in self.pkt_layers:
            found = False
            l_type = layer.lower()

            for types in list(LayersTypes.values()):
                if l_type in types:
                    found = True
                    break

            if found is False:
                self.pkt_layers.remove(l_type)
                print("INVAILD LAYER TYPE [%s]" % l_type.upper())

    def assign_layers(self, layers=None):
        """
        assign layer for this packet
        maybe need add check layer function
        """
        if layers is not None:
            self.pkt_layers = layers

        for layer in self.pkt_layers:
            found = False
            l_type = layer.lower()

            for types in list(LayersTypes.values()):
                if l_type in types:
                    found = True
                    break

            if found is False:
                self.pkt_layers.remove(l_type)
                print("INVAILD LAYER TYPE [%s]" % l_type.upper())

        self.pktgen.add_layers(self.pkt_layers)
        if layers:
            self.pktgen.update_pkts()

    def _load_pkt_layers(self):
        name2type = {
            'MAC': 'ether',
            'VLAN': 'vlan',
            'ETAG': 'etag',
            'IP': 'ipv4',
            'IPv4-TUNNEL': 'inner_ipv4',
            'IPihl': 'ipv4ihl',
            'IPFRAG': 'ipv4_ext',
            'IPv6': 'ipv6',
            'IPv6-TUNNEL': 'inner_ipv6',
            'IPv6FRAG': 'ipv6_frag',
            'IPv6EXT': 'ipv6_ext',
            'IPv6EXT2': 'ipv6_ext2',
            'TCP': 'tcp',
            'UDP': 'udp',
            'SCTP': 'sctp',
            'ICMP': 'icmp',
            'NVGRE': 'nvgre',
            'GRE': 'gre',
            'VXLAN': 'vxlan',
            'PKT': 'raw',
            'MPLS': 'mpls',
            'NSH': 'nsh',
        }

        layers = self.pkt_type.split('_')
        self.pkt_layers = []
        self.pkt_cfgload = True
        for layer in layers:
            if layer in list(name2type.keys()):
                self.pkt_layers.append(name2type[layer])

    def config_def_layers(self):
        """
        Handel config packet layers by default
        """
        if self.pkt_type == "TIMESYNC":
            self.config_layer('ether', {'dst': 'FF:FF:FF:FF:FF:FF',
                                        'type': 0x88f7})
            self.config_layer('raw', {'payload': ['00', '02']})

        if self.pkt_type == "ARP":
            self.config_layer('ether', {'dst': 'FF:FF:FF:FF:FF:FF'})

        if self.pkt_type == "IPv6_SCTP":
            self.config_layer('ipv6', {'nh': 132})

        if "IPv6_NVGRE" in self.pkt_type:
            self.config_layer('ipv6', {'nh': 47})
            if "IPv6_SCTP" in self.pkt_type:
                self.config_layer('inner_ipv6', {'nh': 132})
            if "IPv6_ICMP" in self.pkt_type:
                self.config_layer('inner_ipv6', {'nh': 58})
            if "IPFRAG" in self.pkt_type:
                self.config_layer('raw', {'payload': ['00'] * 40})
            else:
                self.config_layer('raw', {'payload': ['00'] * 18})

        if "MAC_IP_IPv6" in self.pkt_type or \
                "MAC_IP_NVGRE" in self.pkt_type or \
                "MAC_IP_UDP_VXLAN" in self.pkt_type:
            if "IPv6_SCTP" in self.pkt_type:
                self.config_layer('ipv6', {'nh': 132})
            if "IPv6_ICMP" in self.pkt_type:
                self.config_layer('ipv6', {'nh': 58})
            if "IPFRAG" in self.pkt_type:
                self.config_layer('raw', {'payload': ['00'] * 40})
            else:
                self.config_layer('raw', {'payload': ['00'] * 18})
        if 'TCP' in self.pkt_type:
            self.config_layer('tcp', {'flags': 0})

    def config_layer(self, layer, config={}):
        """
        Configure packet assigned layer
        return the status of configure result
        """
        try:
            idx = self.pkt_layers.index(layer)
        except Exception as e:
            print("INVALID LAYER ID %s" % layer)
            return False

        if self.check_layer_config() is False:
            return False

        if 'inner' in layer:
            layer = layer[6:]
        if isinstance(self.pktgen.pkt, str):
            raise Exception('string type packet not support config layer')
        pkt_layer = self.pktgen.pkt.getlayer(idx)
        layer_conf = getattr(self.pktgen, layer)
        setattr(self, 'configured_layer_%s' % layer, True)

        layer_conf(pkt_layer, **config)

    def config_layers(self, layers=None):
        """
        Configure packet with multi configurations
        """
        layers = [] if layers is None else layers  # None object is not Iterable
        for layer in layers:
            name, config = layer
            if name not in self.pkt_layers:
                print("[%s] is missing in packet!!!" % name)
                raise
            if self.config_layer(name, config) is False:
                print("[%s] failed to configure!!!" % name)
                raise

    def strip_layer_element(self, layer, element, p_index=0):
        """
        Strip packet layer elements
        return the status of configure result
        """
        strip_element = getattr(self, "strip_element_%s" % layer)
        return strip_element(element, p_index)

    def strip_element_layer2(self, element, p_index=0):
        return self.pktgen.strip_layer2(element, p_index)

    def strip_element_layer3(self, element, p_index=0):
        return self.pktgen.strip_layer3(element, p_index)

    def strip_element_vlan(self, element, p_index=0):
        return self.pktgen.strip_vlan(element, p_index)

    def strip_element_etag(self, element, p_index=0):
        return self.pktgen.strip_etag(element, p_index)

    def strip_element_layer4(self, element, p_index=0):
        return self.pktgen.strip_layer4(element, p_index)


def IncreaseIP(addr):
    """
    Returns the IP address from a given one, like
    192.168.1.1 ->192.168.1.2
    If disable ip hw chksum, csum routine will increase ip
    """
    ip2int = lambda ipstr: struct.unpack('!I', socket.inet_aton(ipstr))[0]
    x = ip2int(addr)
    int2ip = lambda n: socket.inet_ntoa(struct.pack('!I', n))
    return int2ip(x + 1)


def IncreaseIPv6(addr):
    """
    Returns the IP address from a given one, like
    FE80:0:0:0:0:0:0:0 -> FE80::1
    csum routine will increase ip
    """
    ipv6addr = struct.unpack('!8H', socket.inet_pton(AF_INET6, addr))
    addr = list(ipv6addr)
    addr[7] += 1
    ipv6 = socket.inet_ntop(AF_INET6, struct.pack(
        '!8H', addr[0], addr[1], addr[2], addr[3], addr[4], addr[5], addr[6], addr[7]))
    return ipv6


def get_ether_type(eth_type=""):
    # need add more types later
    if eth_type.lower() == "lldp":
        return '0x88cc'
    elif eth_type.lower() == "ip":
        return '0x0800'
    elif eth_type.lower() == "ipv6":
        return '0x86dd'

    return 'not support'


def get_filter_cmd(filters=[]):
    """
    Return bpf formated filter string, only support ether layer now
    """
    filter_sep = " and "
    filter_cmds = ""
    for pktfilter in filters:
        filter_cmd = ""
        if pktfilter['layer'] == 'ether':
            if list(pktfilter['config'].keys())[0] == 'dst':
                dmac = pktfilter['config']['dst']
                filter_cmd = "ether dst %s" % dmac
            elif list(pktfilter['config'].keys())[0] == 'src':
                smac = pktfilter['config']['src']
                filter_cmd = "ether src %s" % smac
            elif list(pktfilter['config'].keys())[0] == 'type':
                eth_type = pktfilter['config']['type']
                eth_format = r"(\w+) (\w+)"
                m = re.match(eth_format, eth_type)
                if m:
                    type_hex = get_ether_type(m.group(2))
                    if type_hex == 'not support':
                        continue
                    if m.group(1) == 'is':
                        filter_cmd = 'ether[12:2] = %s' % type_hex
                    elif m.group(1) == 'not':
                        filter_cmd = 'ether[12:2] != %s' % type_hex
        elif pktfilter['layer'] == 'network':
            if list(pktfilter['config'].keys())[0] == 'srcport':
                sport = pktfilter['config']['srcport']
                filter_cmd = "src port %s" % sport
            elif list(pktfilter['config'].keys())[0] == 'dstport':
                dport = pktfilter['config']['dstport']
                filter_cmd = "dst port %s" % dport
        elif pktfilter['layer'] == 'userdefined':
            if list(pktfilter['config'].keys())[0] == 'pcap-filter':
                filter_cmd = pktfilter['config']['pcap-filter']

        if len(filter_cmds):
            if len(filter_cmd):
                filter_cmds += filter_sep
                filter_cmds += filter_cmd
        else:
            filter_cmds = filter_cmd

    if len(filter_cmds):
        return ' \'' + filter_cmds + '\' '
    else:
        return ""


def start_tcpdump(crb, intf, count=0, filters=None, lldp_forbid=True):
    """
    sniff all packets from certain port
    """
    filters = [] if filters is None else filters
    out = crb.send_expect("ls -d %s" % crb.tmp_file, "# ", verify=True)
    if out == 2:
        crb.send_expect("mkdir -p %s" % crb.tmp_file, "# ")
    filename = '{}sniff_{}.pcap'.format(crb.tmp_file, intf)
    # delete old pcap file
    crb.send_expect('rm -rf %s' % filename, '# ')

    param = ""
    direct_param = r"(\s+)\[ (\S+) in\|out\|inout \]"
    tcpdump_session = crb.create_session('tcpdump_session' + str(time.time()))
    setattr(tcpdump_session, 'tmp_file', crb.tmp_file)
    tcpdump_help = tcpdump_session.send_command('tcpdump -h')

    for line in tcpdump_help.split('\n'):
        m = re.match(direct_param, line)
        if m:
            opt = re.search("-Q", m.group(2))
            if opt:
                param = "-Q" + " in"
            else:
                opt = re.search("-P", m.group(2))
                if opt:
                    param = "-P" + " in"

    if len(param) == 0:
        print("tcpdump not support direction choice!!!")

    if lldp_forbid and (LLDP_FILTER not in filters):
        filters.append(LLDP_FILTER)

    filter_cmd = get_filter_cmd(filters)

    sniff_cmd = 'tcpdump -i %(INTF)s %(FILTER)s %(IN_PARAM)s -w %(FILE)s'
    options = {'INTF': intf, 'COUNT': count, 'IN_PARAM': param,
               'FILE': filename,
               'FILTER': filter_cmd}
    if count:
        sniff_cmd += ' -c %(COUNT)d'
        cmd = sniff_cmd % options
    else:
        cmd = sniff_cmd % options

    tcpdump_session.send_command(cmd)

    index = str(time.time())
    SNIFF_PIDS[index] = (tcpdump_session, intf, filename)
    time.sleep(1)
    return index


def stop_and_load_tcpdump_packets(index='', timeout=1):
    """
    Stop sniffer and return packet object
    """
    if index in list(SNIFF_PIDS.keys()):
        pipe, intf, filename = SNIFF_PIDS.pop(index)
        pipe.get_session_before(timeout)
        pipe.send_command('^C')
        pipe.copy_file_from(filename, TMP_PATH)
        p = Packet()
        p.read_pcapfile(TMP_PATH + filename.split(os.sep)[-1])
        pipe.close()
        return p


def compare_pktload(pkt1=None, pkt2=None, layer="L2"):
    l_idx = 0
    if layer == "L2":
        l_idx = 0
    elif layer == "L3":
        l_idx = 1
    elif layer == "L4":
        l_idx = 2
    try:
        load1 = hexstr(str(pkt1.getlayer(l_idx)))
        load2 = hexstr(str(pkt2.getlayer(l_idx)))
    except:
        # return pass when scapy failed to extract packet
        return True

    if load1 == load2:
        return True
    else:
        return False


def strip_pktload(pkt=None, layer="L2", p_index=0):
    if layer == "L2":
        l_idx = 0
    elif layer == "L3":
        l_idx = 1
    elif layer == "L4":
        l_idx = 2
    else:
        l_idx = 0
    try:
        load = hexstr(str(pkt.pktgen.pkts[p_index].getlayer(l_idx)), onlyhex=1)
    except:
        # return pass when scapy failed to extract packet
        load = ""

    return load


###############################################################################
###############################################################################
if __name__ == "__main__":
    pkt = Packet('Ether(type=0x894f)/NSH(Len=0x6,NextProto=0x0,NSP=0x000002,NSI=0xff)')
    sendp(pkt, iface='lo')
    pkt.append_pkt(pkt_type='IPv6_TCP', pkt_len=100)
    pkt.append_pkt(pkt_type='TCP', pkt_len=100)
    pkt.config_layer('tcp', config={'flags': 'A'})
    pkt.append_pkt("Ether(dst='11:22:33:44:55:11')/IP(dst='192.168.5.2')/TCP(flags=0)/Raw(load='bbbb')")
    pkt.generate_random_pkts('11:22:33:44:55:55', random_type=['TCP', 'IPv6_TCP'], random_payload=True, pktnum=10)
    sendp(pkt, iface='lo')

    pkt = Packet(pkt_type='UDP', pkt_len=1500, ran_payload=True)
    sendp(pkt, iface='lo')
    pkt = Packet(pkt_type='IPv6_SCTP')
    sendp(pkt, iface='lo')
    pkt = Packet(pkt_type='VLAN_UDP')
    pkt.config_layer('vlan', {'vlan': 2})
    sendp(pkt, iface='lo')

    pkt.assign_layers(['ether', 'vlan', 'ipv4', 'udp',
                       'vxlan', 'inner_mac', 'inner_ipv4', 'inner_udp', 'raw'])
    pkt.config_layer('ether', {'dst': '00:11:22:33:44:55'})
    pkt.config_layer('vlan', {'vlan': 2})
    pkt.config_layer('ipv4', {'dst': '1.1.1.1'})
    pkt.config_layer('udp', {'src': 4789, 'dst': 4789, 'chksum': 0x1111})
    pkt.config_layer('vxlan', {'vni': 2})
    pkt.config_layer('raw', {'payload': ['58'] * 18})
    sendp(pkt, iface='lo')

    pkt.assign_layers(['ether', 'vlan', 'ipv4', 'udp',
                       'vxlan', 'inner_mac', 'inner_ipv4', 'inner_udp', 'raw'])
    # config packet
    pkt.config_layers([('ether', {'dst': '00:11:22:33:44:55'}), ('ipv4', {'dst': '1.1.1.1'}),
                       ('vxlan', {'vni': 2}), ('raw', {'payload': ['01'] * 18})])

    sendp(pkt, iface='lo')

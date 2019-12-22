# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
Folders for framework running environment.
"""
import os
import sys
import re
import socket

FOLDERS = {
    'Framework': 'framework',
    'Testscripts': 'tests',
    'Configuration': 'conf',
    'Depends': 'dep',
    'Output': 'output',
    'NicDriver': 'nics',
}

"""
Nics and its identifiers supported by the framework.
"""
NICS = {
    'kawela': '8086:10e8',
    'kawela_2': '8086:10c9',
    'kawela_4': '8086:1526',
    'bartonhills': '8086:150e',
    'powerville': '8086:1521',
    'powerville_vf': '8086:1520',
    'ophir': '8086:105e',
    'niantic': '8086:10fb',
    'niantic_vf': '8086:10ed',
    'ironpond': '8086:151c',
    'twinpond': '8086:1528',
    'twinville': '8086:1512',
    'sageville': '8086:1563',
    'sageville_vf': '8086:1565',
    'sagepond': '8086:15ad',
    'sagepond_vf': '8086:15a8',
    'magnolia_park': '8086:15ce',
    'hartwell': '8086:10d3',
    '82545EM': '8086:100f',
    '82540EM': '8086:100e',
    'springville': '8086:1533',
    'springfountain': '8086:154a',
    'virtio': '1af4:1000',
    'avoton': '8086:1f41',
    'avoton2c5': '8086:1f45',
    'I217V': '8086:153b',
    'I217LM': '8086:153a',
    'I218V': '8086:1559',
    'I218LM': '8086:155a',
    'fortville_eagle': '8086:1572',
    'fortville_spirit': '8086:1583',
    'fortville_spirit_single': '8086:1584',
    'redrockcanyou': '8086:15a4',
    'fortpark': '8086:374c',
    'fortpark_1g': '8086:37d1',
    'fortpark_TLV': '8086:37d0',
    'fortpark_TLV_vf': '8086:37cd',
    'fvl10g_vf': '8086:154c',
    'atwood': '8086:15d5',
    'ConnectX3_MT4103': '15b3:1007',
    'ConnectX4_MT4115': '15b3:1013',
    'ConnectX4_LX_MT4117': '15b3:1015',
    'ConnectX5_MT4119': '15b3:1017',
    'ConnectX5_MT4121': '15b3:1019',
    'boulderrapid': '8086:15d0',
    'fortville_25g': '8086:158b',
    'cavium_a034': '177d:a034',
    'cavium_0011': '177d:0011',
    'hi1822': '19e5:1822',
    'fortvile_bdw_de': '8086:15ac',
    'cavium_a063': '177d:a063',
    'cavium_a064': '177d:a064',
    'columbiaville_100g': '8086:1592',
    'columbiaville_25g': '8086:1593',
    'fastlinq_ql45000': '1077:1656',
    'fastlinq_ql45000_vf': '1077:1664',
    'fastlinq_ql41000': '1077:8070',
    'fastlinq_ql41000_vf': '1077:8090',
    'carlsville': '8086:15ff',
    'hi1822': '19e5:1822',
}

DRIVERS = {
    'kawela': 'igb',
    'kawela_2': 'igb',
    'kawela_4': 'igb',
    'bartonhills': 'igb',
    'powerville': 'igb',
    'powerville_vf': 'igbvf',
    'ophir': 'igb',
    'niantic': 'ixgbe',
    'niantic_vf': 'ixgbevf',
    'ironpond': 'ixgbe',
    'twinpond': 'ixgbe',
    'twinville': 'ixgbe',
    'sageville': 'ixgbe',
    'sageville_vf': 'ixgbevf',
    'sagepond': 'ixgbe',
    'sagepond_vf': 'ixgbevf',
    'magnolia_park' : 'ixgbe',
    'hartwell': 'igb',
    '82545EM': 'igb',
    '82540EM': 'igb',
    'springville': 'igb',
    'springfountain': 'ixgbe',
    'virtio': 'virtio-pci',
    'avoton': 'igb',
    'avoton2c5': 'igb',
    'I217V': 'igb',
    'I217LM': 'igb',
    'I218V': 'igb',
    'I218LM': 'igb',
    'fortville_eagle': 'i40e',
    'fortville_spirit': 'i40e',
    'fortville_spirit_single': 'i40e',
    'redrockcanyou': 'fm10k',
    'fortpark': 'i40e',
    'fortpark_1g': 'i40e',
    'fortpark_TLV': 'i40e',
    'fortpark_TLV_vf': 'i40evf',
    'fvl10g_vf': 'i40evf',
    'atwood': 'fm10k',
    'ConnectX3_MT4103': 'mlx4_core',
    'ConnectX4_MT4115': 'mlx5_core',
    'ConnectX4_LX_MT4117': 'mlx5_core',
    'ConnectX5_MT4119': 'mlx5_core',
    'ConnectX5_MT4121': 'mlx5_core',
    'boulderrapid': 'fm10k',
    'fortville_25g': 'i40e',
    'cavium_a034': 'thunder-nicvf',
    'cavium_0011': 'thunder-nicvf',
    'hi1822': 'hinic',
    'fortvile_bdw_de': 'ixgbe',
    'cavium_a063': 'octeontx2-nicpf',
    'cavium_a064': 'octeontx2-nicvf',
    'columbiaville_100g': 'ice',
    'columbiaville_25g': 'ice',
    'fastlinq_ql45000': 'qede',
    'fastlinq_ql41000': 'qede',
    'fastlinq_ql45000_vf': 'qede',
    'fastlinq_ql41000_vf': 'qede',
    'carlsville': 'i40e',
    'hi1822': 'hinic',
}

"""
List used to translate scapy packets into Ixia TCL commands.
"""
SCAPY2IXIA = [
    'Ether',
    'Dot1Q',
    'IP',
    'IPv6',
    'TCP',
    'UDP',
    'SCTP'
]

USERNAME = 'root'


"""
Helpful header sizes.
"""
HEADER_SIZE = {
    'eth': 18,
    'ip': 20,
    'ipv6': 40,
    'udp': 8,
    'tcp': 20,
    'vxlan': 8,
}
"""
dpdk send protocol packet size.
"""
PROTOCOL_PACKET_SIZE = {
    'lldp': [110, 100],
}

"""
Default session timeout.
"""
TIMEOUT = 15


"""
Global macro for dts.
"""
IXIA = "ixia"
PKTGEN = "pktgen"
PKTGEN_DPDK = "dpdk"
PKTGEN_TREX = "trex"
PKTGEN_IXIA = "ixia"
PKTGEN_GRP = frozenset([PKTGEN_DPDK, PKTGEN_TREX, PKTGEN_IXIA])
"""
The log name seperater.
"""
LOG_NAME_SEP = '.'

"""
Section name for suite level configuration
"""
SUITE_SECTION_NAME = "suite"

"""
DTS global environment variable
"""
DTS_ENV_PAT = r"DTS_*"
PERF_SETTING = "DTS_PERF_ONLY"
FUNC_SETTING = "DTS_FUNC_ONLY"
HOST_DRIVER_SETTING = "DTS_HOST_DRIVER"
HOST_DRIVER_MODE_SETTING = "DTS_HOST_DRIVER_MODE"
HOST_NIC_SETTING = "DTS_HOST_NIC"
DEBUG_SETTING = "DTS_DEBUG_ENABLE"
DEBUG_CASE_SETTING = "DTS_DEBUGCASE_ENABLE"
DPDK_RXMODE_SETTING = "DTS_DPDK_RXMODE"
DTS_ERROR_ENV = "DTS_RUNNING_ERROR"
DTS_CFG_FOLDER = "DTS_CFG_FOLDER"
DTS_PARALLEL_SETTING = "DTS_PARALLEL_ENABLE"
UPDATE_EXPECTED = "DTS_UPDATE_EXPECTED_ENABLE"


"""
DTS global error table
"""
DTS_ERR_TBL = {
    "GENERIC_ERR": 1,
    "DPDK_BUILD_ERR" : 2,
    "DUT_SETUP_ERR" : 3,
    "TESTER_SETUP_ERR" : 4,
    "SUITE_SETUP_ERR": 5,
    "SUITE_EXECUTE_ERR": 6,
    "PARALLEL_EXECUTE_ERR": 7
}

def get_nic_name(type):
    """
    strip nic code name by nic type
    """
    for name, nic_type in NICS.items():
        if nic_type == type:
            return name
    return 'Unknown'


def get_nic_driver(pci_id):
    """
    Return linux driver for specified pci device
    """
    driverlist = dict(zip(NICS.values(), DRIVERS.keys()))
    try:
        driver = DRIVERS[driverlist[pci_id]]
    except Exception as e:
        driver = None
    return driver


def get_netdev(crb, pci):
    for port in crb.ports_info:
        if pci == port['pci']:
            return port['port']
        if 'vfs_port' in port.keys():
            for vf in port['vfs_port']:
                if pci == vf.pci:
                    return vf

    return None


def get_host_ip(address):
    ip_reg = r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}'
    m = re.match(ip_reg, address)
    if m:
        return address
    else:
        try:
            result = socket.gethostbyaddr(address)
            return result[2][0]
        except:
            print "couldn't look up %s" % address
            return ''


def save_global_setting(key, value):
    """
    Save DTS global setting
    """
    if re.match(DTS_ENV_PAT, key):
        env_key = key
    else:
        env_key = "DTS_" + key

    os.environ[env_key] = value


def load_global_setting(key):
    """
    Load DTS global setting
    """
    if re.match(DTS_ENV_PAT, key):
        env_key = key
    else:
        env_key = "DTS_" + key

    if env_key in os.environ.keys():
        return os.environ[env_key]
    else:
        return ''


def report_error(error):
    """
    Report error when error occurred
    """
    if error in DTS_ERR_TBL.keys():
        os.environ[DTS_ERROR_ENV] = error
    else:
        os.environ[DTS_ERROR_ENV] = "GENERIC_ERR"


def exit_error():
    """
    Set system exit value when error occurred
    """
    if DTS_ERROR_ENV in os.environ.keys():
        ret_val = DTS_ERR_TBL[os.environ[DTS_ERROR_ENV]]
        sys.exit(ret_val)
    else:
        sys.exit(0)


def accepted_nic(pci_id):
    """
    Return True if the pci_id is a known NIC card in the settings file and if
    it is selected in the execution file, otherwise it returns False.
    """
    nic = load_global_setting(HOST_NIC_SETTING)
    if pci_id not in NICS.values():
        return False

    if nic is 'any':
        return True

    else:
        if pci_id == NICS[nic]:
            return True

    return False

"""
The root path of framework configs.
"""
dts_cfg_folder = load_global_setting(DTS_CFG_FOLDER)
if dts_cfg_folder != '':
    CONFIG_ROOT_PATH = dts_cfg_folder
else:
    CONFIG_ROOT_PATH = "./conf"

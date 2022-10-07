# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

"""
Folders for framework running environment.
"""
import os
import re
import socket
import sys

FOLDERS = {
    "Framework": "framework",
    "Testscripts": "tests",
    "Configuration": "conf",
    "Depends": "dep",
    "Output": "output",
    "NicDriver": "nics",
}

"""
Nics and its identifiers supported by the framework.
"""
NICS = {
    "IGB_1G-82576_QUAD_COPPER": "8086:10e8",
    "IGB_1G-82576": "8086:10c9",
    "IGB_1G-82576_QUAD_COPPER_ET2": "8086:1526",
    "IGB_1G-82580_COPPER": "8086:150e",
    "IGB_1G-I350_COPPER": "8086:1521",
    "IGB-I350_VF": "8086:1520",
    "IGB_1G-82571EB_COPPER": "8086:105e",
    "IXGBE_10G-82599_SFP": "8086:10fb",
    "IXGBE_10G-82599_VF": "8086:10ed",
    "IXGBE_10G-82599_T3_LOM": "8086:151c",
    "IXGBE_10G-X540T": "8086:1528",
    "IXGBE_10G-X540_VF": "8086:1515",
    "IXGBE_10G-X550T": "8086:1563",
    "IXGBE_10G-X550_VF": "8086:1565",
    "IXGBE_10G-X550EM_X_10G_T": "8086:15ad",
    "IXGBE_10G-X550EM_X_VF": "8086:15a8",
    "IXGBE_10G-X550EM_A_SFP": "8086:15ce",
    "IGB_1G-82574L": "8086:10d3",
    "IGB_1G-82545EM_COPPER": "8086:100f",
    "IGB_1G-82540EM": "8086:100e",
    "IGB_1G-I210_COPPER": "8086:1533",
    "IXGBE_10G-82599_SFP_SF_QP": "8086:154a",
    "virtio": "1af4:1000",
    "IGB_1G-I354_SGMII": "8086:1f41",
    "IGB_2.5G-I354_BACKPLANE_2_5GBPS": "8086:1f45",
    "IGB_1G-PCH_LPT_I217_V": "8086:153b",
    "IGB_1G-PCH_LPT_I217_LM": "8086:153a",
    "IGB_1G-PCH_LPTLP_I218_V": "8086:1559",
    "IGB_1G-PCH_LPTLP_I218_LM": "8086:155a",
    "I40E_10G-SFP_XL710": "8086:1572",
    "I40E_40G-QSFP_A": "8086:1583",
    "I40E_40G-QSFP_B": "8086:1584",
    "I40E_10G-X722_A0": "8086:374c",
    "I40E_1G-1G_BASE_T_X722": "8086:37d1",
    "I40E_10G-SFP_X722": "8086:37d0",
    "I40E_10G-10G_BASE_T_X722": "8086:37d2",
    "IAVF_10G-X722_VF": "8086:37cd",
    "IAVF-VF": "8086:154c",
    "ConnectX3_MT4103": "15b3:1007",
    "ConnectX4_MT4115": "15b3:1013",
    "ConnectX4_LX_MT4117": "15b3:1015",
    "ConnectX5_MT4119": "15b3:1017",
    "ConnectX5_MT4121": "15b3:1019",
    "I40E_25G-25G_SFP28": "8086:158b",
    "cavium_a034": "177d:a034",
    "cavium_0011": "177d:0011",
    "IXGBE_10G-X550EM_X_SFP": "8086:15ac",
    "cavium_a063": "177d:a063",
    "cavium_a064": "177d:a064",
    "ICE_100G-E810C_QSFP": "8086:1592",
    "ICE_25G-E810C_SFP": "8086:1593",
    "ICE_25G-E810_XXV_SFP": "8086:159b",
    "IAVF-ADAPTIVE_VF": "8086:1889",
    "fastlinq_ql45000": "1077:1656",
    "fastlinq_ql45000_vf": "1077:1664",
    "fastlinq_ql41000": "1077:8070",
    "fastlinq_ql41000_vf": "1077:8090",
    "I40E_10G-10G_BASE_T_BC": "8086:15ff",
    "hi1822": "19e5:1822",
    "IGC-I225_LM": "8086:15f2",
    "IGC-I226_LM": "8086:125b",
    "brcm_57414": "14e4:16d7",
    "brcm_P2100G": "14e4:1750",
}

ETH_700_SERIES = (
    "I40E_10G-SFP_XL710",
    "I40E_40G-QSFP_A",
    "I40E_40G-QSFP_B",
    "I40E_25G-25G_SFP28",
)

ETH_800_SERIES = (
    "ICE_100G-E810C_QSFP",
    "ICE_25G-E810C_SFP",
    "ICE_25G-E810_XXV_SFP",
    "IAVF-ADAPTIVE_VF",
)

DRIVERS = {
    "IGB_1G-82576_QUAD_COPPER": "igb",
    "IGB_1G-82576": "igb",
    "IGB_1G-82576_QUAD_COPPER_ET2": "igb",
    "IGB_1G-82580_COPPER": "igb",
    "IGB_1G-I350_COPPER": "igb",
    "IGB-I350_VF": "igbvf",
    "IGB_1G-82571EB_COPPER": "igb",
    "IXGBE_10G-82599_SFP": "ixgbe",
    "IXGBE_10G-82599_VF": "ixgbevf",
    "IXGBE_10G-82599_T3_LOM": "ixgbe",
    "IXGBE_10G-X540T": "ixgbe",
    "IXGBE_10G-X540_VF": "ixgbevf",
    "IXGBE_10G-X550T": "ixgbe",
    "IXGBE_10G-X550_VF": "ixgbevf",
    "IXGBE_10G-X550EM_X_10G_T": "ixgbe",
    "IXGBE_10G-X550EM_X_VF": "ixgbevf",
    "IXGBE_10G-X550EM_A_SFP": "ixgbe",
    "IGB_1G-82574L": "igb",
    "IGB_1G-82545EM_COPPER": "igb",
    "IGB_1G-82540EM": "igb",
    "IGB_1G-I210_COPPER": "igb",
    "IXGBE_10G-82599_SFP_SF_QP": "ixgbe",
    "virtio": "virtio-pci",
    "IGB_1G-I354_SGMII": "igb",
    "IGB_2.5G-I354_BACKPLANE_2_5GBPS": "igb",
    "IGB_1G-PCH_LPT_I217_V": "igb",
    "IGB_1G-PCH_LPT_I217_LM": "igb",
    "IGB_1G-PCH_LPTLP_I218_V": "igb",
    "IGB_1G-PCH_LPTLP_I218_LM": "igb",
    "I40E_10G-SFP_XL710": "i40e",
    "I40E_40G-QSFP_A": "i40e",
    "I40E_40G-QSFP_B": "i40e",
    "I40E_10G-X722_A0": "i40e",
    "I40E_1G-1G_BASE_T_X722": "i40e",
    "I40E_10G-SFP_X722": "i40e",
    "I40E_10G-10G_BASE_T_X722": "i40e",
    "IAVF_10G-X722_VF": "iavf",
    "IAVF-VF": "iavf",
    "ConnectX3_MT4103": "mlx4_core",
    "ConnectX4_MT4115": "mlx5_core",
    "ConnectX4_LX_MT4117": "mlx5_core",
    "ConnectX5_MT4119": "mlx5_core",
    "ConnectX5_MT4121": "mlx5_core",
    "I40E_25G-25G_SFP28": "i40e",
    "cavium_a034": "thunder-nicvf",
    "cavium_0011": "thunder-nicvf",
    "IXGBE_10G-X550EM_X_SFP": "ixgbe",
    "cavium_a063": "octeontx2-nicpf",
    "cavium_a064": "octeontx2-nicvf",
    "ICE_100G-E810C_QSFP": "ice",
    "ICE_25G-E810C_SFP": "ice",
    "ICE_25G-E810_XXV_SFP": "ice",
    "IAVF-ADAPTIVE_VF": "iavf",
    "fastlinq_ql45000": "qede",
    "fastlinq_ql41000": "qede",
    "fastlinq_ql45000_vf": "qede",
    "fastlinq_ql41000_vf": "qede",
    "I40E_10G-10G_BASE_T_BC": "i40e",
    "hi1822": "hinic",
    "IGC-I225_LM": "igc",
    "IGC-I226_LM": "igc",
    "brcm_57414": "bnxt_en",
    "brcm_P2100G": "bnxt_en",
}

"""
List used to translate scapy packets into Ixia TCL commands.
"""
SCAPY2IXIA = ["Ether", "Dot1Q", "IP", "IPv6", "TCP", "UDP", "SCTP"]

USERNAME = "root"

# A user used to test functionality for a non-root user
UNPRIVILEGED_USERNAME = "dtsunprivilegedtester"

"""
Helpful header sizes.
"""
HEADER_SIZE = {
    "eth": 18,
    "ip": 20,
    "ipv6": 40,
    "udp": 8,
    "tcp": 20,
    "vxlan": 8,
}
"""
dpdk send protocol packet size.
"""
PROTOCOL_PACKET_SIZE = {
    "lldp": [110, 100],
}

"""
Default session timeout.
"""
TIMEOUT = 15


"""
Global macro for dts.
"""
PKTGEN = "pktgen"
PKTGEN_DPDK = "dpdk"
PKTGEN_TREX = "trex"
PKTGEN_IXIA = "ixia"
PKTGEN_IXIA_NETWORK = "ixia_network"
PKTGEN_GRP = frozenset([PKTGEN_DPDK, PKTGEN_TREX, PKTGEN_IXIA, PKTGEN_IXIA_NETWORK])
"""
The log name seperater.
"""
LOG_NAME_SEP = "."

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
HOST_SHARED_LIB_SETTING = "DTS_HOST_SHARED_LIB"
HOST_SHARED_LIB_PATH = "DTS_HOST_SHARED_LIB_PATH"
DEBUG_SETTING = "DTS_DEBUG_ENABLE"
DEBUG_CASE_SETTING = "DTS_DEBUGCASE_ENABLE"
DPDK_RXMODE_SETTING = "DTS_DPDK_RXMODE"
DPDK_DCFMODE_SETTING = "DTS_DPDK_DCFMODE"
DTS_ERROR_ENV = "DTS_RUNNING_ERROR"
DTS_CFG_FOLDER = "DTS_CFG_FOLDER"
DTS_PARALLEL_SETTING = "DTS_PARALLEL_ENABLE"
UPDATE_EXPECTED = "DTS_UPDATE_EXPECTED_ENABLE"


"""
DTS global error table
"""
DTS_ERR_TBL = {
    "GENERIC_ERR": 1,
    "DPDK_BUILD_ERR": 2,
    "DUT_SETUP_ERR": 3,
    "TESTER_SETUP_ERR": 4,
    "SUITE_SETUP_ERR": 5,
    "SUITE_EXECUTE_ERR": 6,
    "PARALLEL_EXECUTE_ERR": 7,
}


def get_nic_name(type):
    """
    strip nic code name by nic type
    """
    for name, nic_type in list(NICS.items()):
        if nic_type == type:
            return name
    return "Unknown"


def get_nic_driver(pci_id):
    """
    Return linux driver for specified pci device
    """
    try:
        driver = DRIVERS[{NICS[key]: key for key in NICS}[pci_id]]
    except Exception as e:
        driver = None
    return driver


def get_netdev(crb, pci):
    for port in crb.ports_info:
        if pci == port["pci"]:
            return port["port"]
        if "vfs_port" in list(port.keys()):
            for vf in port["vfs_port"]:
                if pci == vf.pci:
                    return vf

    return None


def get_host_ip(address):
    ip_reg = r"\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}"
    m = re.match(ip_reg, address)
    if m:
        return address
    else:
        try:
            result = socket.gethostbyaddr(address)
            return result[2][0]
        except:
            print("couldn't look up %s" % address)
            return ""


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

    if env_key in list(os.environ.keys()):
        return os.environ[env_key]
    else:
        return ""


def report_error(error):
    """
    Report error when error occurred
    """
    if error in list(DTS_ERR_TBL.keys()):
        os.environ[DTS_ERROR_ENV] = error
    else:
        os.environ[DTS_ERROR_ENV] = "GENERIC_ERR"


def exit_error():
    """
    Set system exit value when error occurred
    """
    if DTS_ERROR_ENV in list(os.environ.keys()):
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
    if pci_id not in list(NICS.values()):
        return False

    if nic == "any":
        return True

    else:
        if pci_id == NICS[nic]:
            return True

    return False


"""
The root path of framework configs.
"""
dts_cfg_folder = load_global_setting(DTS_CFG_FOLDER)
if dts_cfg_folder != "":
    CONFIG_ROOT_PATH = dts_cfg_folder
else:
    CONFIG_ROOT_PATH = "./conf"

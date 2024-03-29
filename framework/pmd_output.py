# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import os
import re
from time import sleep

from .settings import PROTOCOL_PACKET_SIZE, TIMEOUT, get_nic_driver
from .utils import create_mask


class PmdOutput:

    """
    Module for get all statics value by port in testpmd
    """

    def __init__(self, dut, session=None):
        self.dut = dut
        if session is None:
            session = dut
        self.session = session
        self.dut.testpmd = self
        self.rx_pkts_prefix = "RX-packets:"
        self.rx_missed_prefix = "RX-missed:"
        self.rx_bytes_prefix = "RX-bytes:"
        self.rx_badcrc_prefix = "RX-badcrc:"
        self.rx_badlen_prefix = "RX-badlen:"
        self.rx_error_prefix = "RX-errors:"
        self.rx_nombuf_prefix = "RX-nombuf:"
        self.tx_pkts_prefix = "TX-packets:"
        self.tx_error_prefix = "TX-errors:"
        self.tx_bytes_prefix = "TX-bytes:"
        self.bad_ipcsum_prefix = "Bad-ipcsum:"
        self.bad_l4csum_prefix = "Bad-l4csum:"
        self.set_default_corelist()

    def get_pmd_value(self, prefix, out):
        pattern = re.compile(prefix + "(\s+)([0-9]+)")
        m = pattern.search(out)
        if m is None:
            return None
        else:
            return int(m.group(2))

    def set_default_corelist(self):
        """
        set default cores for start testpmd
        """
        core_number = len(self.dut.cores)
        if core_number < 2:
            raise ValueError(f"Not enough cores on DUT {self.dut}")
        else:
            self.default_cores = "1S/2C/1T"

    def get_pmd_stats(self, portid):
        stats = {}
        out = self.session.send_expect("show port stats %d" % portid, "testpmd> ")
        stats["RX-packets"] = self.get_pmd_value(self.rx_pkts_prefix, out)
        stats["RX-missed"] = self.get_pmd_value(self.rx_missed_prefix, out)
        stats["RX-bytes"] = self.get_pmd_value(self.rx_bytes_prefix, out)

        stats["RX-badcrc"] = self.get_pmd_value(self.rx_badcrc_prefix, out)
        stats["RX-badlen"] = self.get_pmd_value(self.rx_badlen_prefix, out)
        stats["RX-errors"] = self.get_pmd_value(self.rx_error_prefix, out)
        stats["RX-nombuf"] = self.get_pmd_value(self.rx_nombuf_prefix, out)
        stats["TX-packets"] = self.get_pmd_value(self.tx_pkts_prefix, out)
        stats["TX-errors"] = self.get_pmd_value(self.tx_error_prefix, out)
        stats["TX-bytes"] = self.get_pmd_value(self.tx_bytes_prefix, out)

        # display when testpmd config forward engine to csum
        stats["Bad-ipcsum"] = self.get_pmd_value(self.bad_ipcsum_prefix, out)
        stats["Bad-l4csum"] = self.get_pmd_value(self.bad_l4csum_prefix, out)
        return stats

    def get_pmd_cmd(self):
        return self.command

    def start_testpmd(
        self,
        cores="default",
        param="",
        eal_param="",
        socket=0,
        fixed_prefix=False,
        expected="testpmd> ",
        timeout=120,
        **config,
    ):
        """
        start testpmd with input parameters.
        :param cores: eg:
                cores='default'
                cores='1S/4C/1T'
        :param param: dpdk application (testpmd) parameters
        :param eal_param: user defined DPDK eal parameters, eg:
                eal_param='-a af:00.0 -a af:00.1,proto_xtr=vlan',
                eal_param='-b af:00.0 --file-prefix=vf0',
                eal_param='--no-pci',
        :param socket: physical CPU socket index
        :param fixed_prefix: use fixed file-prefix or not, when it is true,
               the file-prefix will not be added a timestamp
        :param config: kwargs user defined eal parameters, eg:
                set PCI allow list: ports=[0,1], port_options={0: "proto_xtr=vlan"},
                set PCI block list: b_ports=['0000:1a:00.0'],
                disable PCI: no_pci=True,
                add virtual device: vdevs=['net_vhost0,iface=vhost-net,queues=1']
        :return: output of launching testpmd
        """
        eal_param = " " + eal_param + " "
        eal_param = eal_param.replace(" -w ", " -a ")
        re_file_prefix = "--file-prefix[\s*=]\S+\s"
        file_prefix_str = re.findall(re_file_prefix, eal_param)
        if file_prefix_str:
            tmp = re.split("(=|\s+)", file_prefix_str[-1].strip())
            file_prefix = tmp[-1].strip()
            config["prefix"] = file_prefix
        eal_param = re.sub(re_file_prefix, "", eal_param)
        config["other_eal_param"] = eal_param

        config["cores"] = cores
        if (
            " -w " not in eal_param
            and " -a " not in eal_param
            and " -b " not in eal_param
            and "ports" not in config
            and "b_ports" not in config
            and " --no-pci " not in eal_param
            and (
                "no_pci" not in config
                or ("no_pci" in config and config["no_pci"] != True)
            )
        ):
            config["ports"] = [
                self.dut.ports_info[i]["pci"] for i in range(len(self.dut.ports_info))
            ]
        all_eal_param = self.dut.create_eal_parameters(
            fixed_prefix=fixed_prefix, socket=socket, **config
        )

        app_name = self.dut.apps_name["test-pmd"]
        command = app_name + " %s -- -i %s" % (all_eal_param, param)
        command = command.replace("  ", " ")
        if self.session != self.dut:
            self.session.send_expect("cd %s" % self.dut.base_dir, "# ")
        out = self.session.send_expect(command, expected, timeout)
        self.command = command
        # wait 10s to ensure links getting up before test start.
        sleep(10)
        return out

    def execute_cmd(
        self, pmd_cmd, expected="testpmd> ", timeout=TIMEOUT, alt_session=False
    ):
        if "dut" in str(self.session):
            return self.session.send_expect(
                "%s" % pmd_cmd, expected, timeout=timeout, alt_session=alt_session
            )
        else:
            return self.session.send_expect("%s" % pmd_cmd, expected, timeout=timeout)

    def get_output(self, timeout=1):
        if "dut" in str(self.session):
            return self.session.get_session_output(timeout=timeout)
        else:
            return self.session.get_session_before(timeout=timeout)

    def get_value_from_string(self, key_str, regx_str, string):
        """
        Get some values from the given string by the regular expression.
        """
        pattern = r"(?<=%s)%s" % (key_str, regx_str)
        s = re.compile(pattern)
        res = s.search(string)
        if type(res).__name__ == "NoneType":
            return " "
        else:
            return res.group(0)

    def get_all_value_from_string(self, key_str, regx_str, string):
        """
        Get some values from the given string by the regular expression.
        """
        pattern = r"(?<=%s)%s" % (key_str, regx_str)
        s = re.compile(pattern)
        res = s.findall(string)
        if type(res).__name__ == "NoneType":
            return " "
        else:
            return res

    def get_detail_from_port_info(self, key_str, regx_str, port):
        """
        Get the detail info from the output of pmd cmd 'show port info <port num>'.
        """
        out = self.session.send_expect("show port info %d" % port, "testpmd> ")
        find_value = self.get_value_from_string(key_str, regx_str, out)
        return find_value

    def get_port_mac(self, port_id):
        """
        Get the specified port MAC.
        """
        return self.get_detail_from_port_info(
            "MAC address: ", "([0-9A-F]{2}:){5}[0-9A-F]{2}", port_id
        )

    def get_firmware_version(self, port_id):
        """
        Get the firmware version.
        """
        return self.get_detail_from_port_info("Firmware-version: ", "\S.*", port_id)

    def get_port_connect_socket(self, port_id):
        """
        Get the socket id which the specified port is connecting with.
        """
        return self.get_detail_from_port_info("Connect to socket: ", "\d+", port_id)

    def get_port_memory_socket(self, port_id):
        """
        Get the socket id which the specified port memory is allocated on.
        """
        return self.get_detail_from_port_info(
            "memory allocation on the socket: ", "\d+", port_id
        )

    def get_port_link_status(self, port_id):
        """
        Get the specified port link status now.
        """
        return self.get_detail_from_port_info("Link status: ", "\S+", port_id)

    def get_port_link_speed(self, port_id):
        """
        Get the specified port link speed now.
        """
        return self.get_detail_from_port_info("Link speed: ", "\d+", port_id)

    def get_port_link_duplex(self, port_id):
        """
        Get the specified port link mode, duplex or simplex.
        """
        return self.get_detail_from_port_info("Link duplex: ", "\S+", port_id)

    def get_port_promiscuous_mode(self, port_id):
        """
        Get the promiscuous mode of port.
        """
        return self.get_detail_from_port_info("Promiscuous mode: ", "\S+", port_id)

    def get_port_allmulticast_mode(self, port_id):
        """
        Get the allmulticast mode of port.
        """
        return self.get_detail_from_port_info("Allmulticast mode: ", "\S+", port_id)

    def check_tx_bytes(self, tx_bytes, exp_bytes=0):
        """
        Intel® Ethernet 700 Series nic will send lldp packet when nic setup with testpmd.
        so should used (tx_bytes - exp_bytes) % PROTOCOL_PACKET_SIZE['lldp']
        for check tx_bytes count right
        """
        # error_flag is true means tx_bytes different with expect bytes
        error_flag = 1
        for size in PROTOCOL_PACKET_SIZE["lldp"]:
            error_flag = error_flag and (tx_bytes - exp_bytes) % size

        return not error_flag

    def get_port_vlan_offload(self, port_id):
        """
        Function: get the port vlan setting info.
        return value:
            'strip':'on'
            'filter':'on'
            'qinq':'off'
        """
        vlan_info = {}
        vlan_info["strip"] = self.get_detail_from_port_info("strip ", "\S+", port_id)
        vlan_info["filter"] = self.get_detail_from_port_info("filter", "\S+", port_id)
        vlan_info["qinq"] = self.get_detail_from_port_info(
            "qinq\(extend\) ", "\S+", port_id
        )
        return vlan_info

    def quit(self):
        self.session.send_expect("quit", "# ")

    def wait_link_status_up(self, port_id, timeout=10):
        """
        check the link status is up
        if not, loop wait
        """
        for i in range(timeout):
            out = self.session.send_expect(
                "show port info %s" % str(port_id), "testpmd> "
            )
            status = self.get_all_value_from_string("Link status: ", "\S+", out)
            if "down" not in status:
                break
            sleep(1)
        return "down" not in status

    def get_max_rule_number(self, obj, out):
        res = re.search(
            r"fd_fltr_guar\s+=\s+(\d+).*fd_fltr_best_effort\s+=\s+(\d+)\.", out
        )
        obj.verify(res, "'fd_fltr_guar' and 'fd_fltr_best_effort not found'")
        fltr_guar, fltr_best = res.group(1), res.group(2)
        max_rule = int(fltr_guar) + int(fltr_best)
        obj.logger.info(f"this Card max rule number is :{max_rule}")
        return max_rule

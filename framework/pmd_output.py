# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

import os
import re
from time import sleep
from settings import TIMEOUT, PROTOCOL_PACKET_SIZE, get_nic_driver
from utils import create_mask


class PmdOutput():

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
            raise
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

    def split_eal_param(self, eal_param):
        """
        split eal param from test suite
        :param eal_param:
        :return:
        """
        re_w_pci_str = '\s?-w\\s+.+?:.+?:.+?\\..+?[,.*=\d+]?\s|\s?-w\\s+.+?:.+?\\..+?[,.*=\d+]?\s'
        re_file_prefix_str = '--file-prefix[\s*=]\S+\s'
        re_b_pci_str = '\s?-b\\s+.+?:.+?:.+?\\..+?[,.*=\d+]?\s|\s?-b\\s+.+?:.+?\\..+?[,.*=\d+]?\s'
        eal_param = eal_param + ' '
        # pci_str_list eg: ['-w   0000:1a:00.0 ', '-w 0000:1a:00.1,queue-num-per-vf=4 ', '-w 0000:aa:bb.1,queue-num-per-vf=4 ']
        w_pci_str_list = re.findall(re_w_pci_str, eal_param)
        # file_prefix_str eg: ['--file-prefix=dpdk ']
        file_prefix_str = re.findall(re_file_prefix_str, eal_param)
        b_pci_str_list = re.findall(re_b_pci_str, eal_param)
        has_pci_option = {}
        pci_list = []
        if w_pci_str_list:
            for pci_str in w_pci_str_list:
                # has pci options
                if ',' in pci_str:
                    pci_option = pci_str.split(',')
                    pci = pci_option[0].split(' ')[-1]
                    has_pci_option[pci] = pci_option[1].strip()
                    pci_list.append(pci)
                else:
                    pci_list.append(pci_str.split('-w')[-1].strip())

        b_pci_list = []
        if b_pci_str_list:
            for b_pci in b_pci_str_list:
                tmp = b_pci.split('-b')[1].strip()
                b_pci_list.append(tmp)

        file_prefix = ''
        if file_prefix_str:
            tmp = re.split('(=|\s+)', file_prefix_str[-1].strip())
            file_prefix = tmp[-1].strip()

        other_eal_str = re.sub(re_w_pci_str, '', eal_param)
        other_eal_str = re.sub(re_b_pci_str, '', other_eal_str)
        other_eal_str = re.sub(re_file_prefix_str, '', other_eal_str)

        no_pci = False
        if '--no-pci' in other_eal_str:
            no_pci = True
            other_eal_str = other_eal_str.replace('--no-pci','')

        return pci_list, has_pci_option, b_pci_list, file_prefix, no_pci, other_eal_str

    def start_testpmd(self, cores='default', param='', eal_param='', socket=0, fixed_prefix=False, **config):
        config['cores'] = cores
        if eal_param == '':
            # use configured ports if not set
            if 'ports' not in list(config.keys()):
                config['ports'] = [self.dut.ports_info[i]['pci'] for i in range(len(self.dut.ports_info))]
            all_eal_param = self.dut.create_eal_parameters(fixed_prefix=fixed_prefix, socket=socket, **config)
        else:
            w_pci_list, port_options, b_pci_list, file_prefix, no_pci, other_eal_str = self.split_eal_param(eal_param)
            if no_pci:
                config['no_pci'] = no_pci
            if w_pci_list:
                config['ports'] = w_pci_list
            if port_options:
                config['port_options'] = port_options
            if b_pci_list:
                config['b_ports'] = b_pci_list
            if file_prefix:
                config['prefix'] = file_prefix

            if not w_pci_list and not b_pci_list and 'ports' not in list(config.keys()):
                config['ports'] = [self.dut.ports_info[i]['pci'] for i in range(len(self.dut.ports_info))]
            part_eal_param = self.dut.create_eal_parameters(fixed_prefix=fixed_prefix, socket=socket, **config)
            all_eal_param = part_eal_param + ' ' + other_eal_str

        command = "./%s/app/testpmd %s -- -i %s" % (self.dut.target, all_eal_param, param)
        out = self.session.send_expect(command, "testpmd> ", 120)
        self.command = command
        # wait 10s to ensure links getting up before test start.
        sleep(10)
        return out

    def execute_cmd(self, pmd_cmd, expected='testpmd> ', timeout=TIMEOUT,
                    alt_session=False):
        if 'dut' in str(self.session):
            return self.session.send_expect('%s' % pmd_cmd, expected, timeout=timeout,
                                    alt_session=alt_session)
        else:
            return self.session.send_expect('%s' % pmd_cmd, expected, timeout=timeout)

    def get_output(self, timeout=1):
        if 'dut' in str(self.session):
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
        if type(res).__name__ == 'NoneType':
            return ' '
        else:
            return res.group(0)

    def get_all_value_from_string(self, key_str, regx_str, string):
        """
        Get some values from the given string by the regular expression.
        """
        pattern = r"(?<=%s)%s" % (key_str, regx_str)
        s = re.compile(pattern)
        res = s.findall(string)
        if type(res).__name__ == 'NoneType':
            return ' '
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
        return self.get_detail_from_port_info("MAC address: ", "([0-9A-F]{2}:){5}[0-9A-F]{2}", port_id)

    def get_port_connect_socket(self, port_id):
        """
        Get the socket id which the specified port is connecting with.
        """
        return self.get_detail_from_port_info("Connect to socket: ", "\d+", port_id)

    def get_port_memory_socket(self, port_id):
        """
        Get the socket id which the specified port memory is allocated on.
        """
        return self.get_detail_from_port_info("memory allocation on the socket: ", "\d+", port_id)

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

    def check_tx_bytes(self, tx_bytes, exp_bytes = 0):
        """
        fortville nic will send lldp packet when nic setup with testpmd.
        so should used (tx_bytes - exp_bytes) % PROTOCOL_PACKET_SIZE['lldp']
        for check tx_bytes count right
        """
        # error_flag is true means tx_bytes different with expect bytes
        error_flag = 1
        for size in  PROTOCOL_PACKET_SIZE['lldp']:
            error_flag = error_flag and  (tx_bytes - exp_bytes) % size

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
        vlan_info['strip'] = self.get_detail_from_port_info(
            "strip ", '\S+', port_id)
        vlan_info['filter'] = self.get_detail_from_port_info(
            'filter', '\S+', port_id)
        vlan_info['qinq'] = self.get_detail_from_port_info(
            'qinq\(extend\) ', '\S+', port_id)
        return vlan_info

    def quit(self):
        self.session.send_expect("quit", "# ")

    def wait_link_status_up(self, port_id, timeout=10):
        """
        check the link status is up
        if not, loop wait
        """
        for i in range(timeout):
            out = self.session.send_expect("show port info %s" % str(port_id), "testpmd> ")
            status = self.get_all_value_from_string("Link status: ", "\S+", out)
            if 'down' not in status:
                break
            sleep(1)
        return 'down' not in status

# BSD LICENSE
#
# Copyright(c) 2010-2020 Intel Corporation. All rights reserved.
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
DPDK Test suite dcf life cycle.

The DCF is a device configuration function (DCF - driver) bound to
one of the device's VFs which can act as a sole controlling entity
to exercise advance functionality (such as switch, ACL) for rest of
the VNFs (virtual network functions) under a DPDK based NFV deployment.

The DCF can act as a special VF talking to the kernel PF over the same
virtchannel mailbox to configure the underlying device (port) for the VFs.

The test suite covers the lifecycle of DCF context in Kernel PF, such as
launch, and exit, switch rules handling, resetting, and exception exit.
"""

import re
import time
import traceback
from contextlib import contextmanager
from pprint import pformat
from functools import partial


from settings import HEADER_SIZE
from test_case import TestCase
from exception import VerifyFailure
from packet import Packet
from pmd_output import PmdOutput
import utils


class TestDcfLifeCycle(TestCase):

    @property
    def target_dir(self):
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    def d_con(self, cmd):
        _cmd = [cmd, '# ', 15] if isinstance(cmd, str) else cmd
        return self.dut.send_expect(*_cmd)

    def d_a_con(self, cmds):
        if isinstance(cmds, str):
            _cmd = [cmds, '# ', 15]
            return self.dut.alt_session.send_expect(*_cmd)
        else:
            return [self.dut.alt_session.send_expect(_cmd, '# ', 10) for _cmd in cmds]

    def vf_pmd2_con(self, cmd):
        _cmd = [cmd, '# ', 15] if isinstance(cmd, str) else cmd
        return self.vf_pmd2_session.session.send_expect(*_cmd)

    def get_ip_layer(self):
        layer = {'ipv4': {
            'src': '192.168.0.2',
            'dst': '192.168.0.3',
        }, }
        return layer

    def get_mac_layer(self, dut_port_id=0, vf_id=0):
        dmac = self.vf_ports_info[dut_port_id]['vfs_mac'][vf_id] \
            if vf_id is not None else self.dut.ports_info[dut_port_id]['mac']
        layer = {'ether': {'dst': dmac, }, }
        return layer

    def get_pkt_len(self):
        headers_size = sum([HEADER_SIZE[x] for x in ['eth', 'ip']])
        pktlen = 64 - headers_size
        return pktlen

    def config_stream(self, dut_port_id=0, vf_id=None):
        pkt_layers = {'raw': {'payload': ['58'] * self.get_pkt_len()}}
        pkt_layers.update(self.get_ip_layer())
        pkt_layers.update(self.get_mac_layer(dut_port_id, vf_id))
        pkt = Packet(pkt_type='IP_RAW')
        for layer in list(pkt_layers.keys()):
            pkt.config_layer(layer, pkt_layers[layer])
        self.logger.info(pkt.pktgen.pkt.command())
        return pkt

    def send_packet_by_scapy(self, pkt, dut_port_id=0, count=1):
        tester_port_id = self.tester.get_local_port(dut_port_id)
        tx_iface = self.tester.get_interface(tester_port_id)
        pkt.send_pkt(crb=self.tester, tx_port=tx_iface, count=count)

    def init_adq(self):
        cmds = [
            "modprobe sch_mqprio",
            "modprobe act_mirred",
            "modprobe cls_flower",
        ]
        self.d_a_con(cmds)

    def set_adq_on_pf(self, dut_port_id=0):
        '''
        Set ADQ on PF
        '''
        msg = "Set ADQ on PF"
        self.logger.info(msg)
        intf = self.dut.ports_info[dut_port_id]['port'].intf_name
        cmds = [
            f"ethtool -K {intf} hw-tc-offload on",
            f"tc qdisc add dev {intf} ingress",
            f"tc qdisc show dev {intf}",
            f"tc qdisc add dev {intf} root mqprio num_tc 4 map 0 0 0 0 1 1 1 1 2 2 2 2 3 3 3 3 queues 4@0 4@4 8@8 8@16 hw 1 mode channel",
            f"tc filter add dev {intf} protocol ip parent ffff: prio 1 flower dst_ip 192.168.1.10 ip_proto tcp action gact pass",
            f"tc filter show dev {intf} parent ffff:",
        ]
        output = self.d_a_con(cmds)
        self.is_adq_set = True
        return output

    def remove_adq_on_pf(self, dut_port_id=0):
        '''
        Remove ADQ on PF
        '''
        if not self.is_adq_set:
            return
        msg = "Remove ADQ on PF"
        self.logger.info(msg)
        intf = self.dut.ports_info[dut_port_id]['port'].intf_name
        cmds = [
            f"tc filter del dev {intf} parent ffff: pref 1 protocol ip",
            f"tc filter show dev {intf} parent ffff:",
            f"tc qdisc del dev {intf} root mqprio",
            f"tc qdisc del dev {intf} ingress",
            f"tc qdisc show dev {intf}",
            f"ethtool -K {intf} hw-tc-offload off",
        ]
        self.d_a_con(cmds)
        self.is_adq_set = False

    def set_adq_mac_vlan(self, dut_port_id=0):
        '''
         change the ADQ commands to MAC-VLAN
        '''
        msg = "change the ADQ commands to MAC-VLAN"
        self.logger.info(msg)
        intf = self.dut.ports_info[dut_port_id]['port'].intf_name
        cmds = [
            f"ethtool -K {intf} l2-fwd-offload on",
            f"ip link add link macvlan0 link {intf} type macvlan",
            f"ip ad",
            f"ifconfig macvlan0 up",
        ]
        output = self.d_a_con(cmds)
        self.is_adq_set = True
        return output

    def remove_adq_mac_vlan(self, dut_port_id=0):
        '''
        Remove MAC-VLAN commands
        '''
        if not self.is_adq_set:
            return
        msg = "Remove MAC-VLAN commands"
        self.logger.info(msg)
        intf = self.dut.ports_info[dut_port_id]['port'].intf_name
        cmds = [
            "ip link del macvlan0",
            f"ethtool -K {intf} l2-fwd-offload off",
        ]
        self.d_a_con(cmds)
        self.is_adq_set = False

    def clear_dmesg(self):
        cmd = 'dmesg -C'
        self.d_a_con(cmd)

    def get_dmesg(self):
        cmd = 'dmesg --color=never'
        return self.d_a_con(cmd) or ''

    def vf_init(self):
        self.vf_ports_info = {}
        self.dut.setup_modules(self.target, 'vfio-pci', '')

    def vf_create(self):
        max_vfs = 4
        for index, port_id in enumerate(self.dut_ports):
            port_obj = self.dut.ports_info[port_id]['port']
            pf_driver = port_obj.default_driver
            self.dut.generate_sriov_vfs_by_port(
                port_id, max_vfs, driver=pf_driver)
            pf_pci = port_obj.pci
            sriov_vfs_port = self.dut.ports_info[port_id].get('vfs_port')
            if not sriov_vfs_port:
                msg = f"failed to create vf on dut port {pf_pci}"
                self.logger.error(msg)
                continue
            for port in sriov_vfs_port:
                port.bind_driver(driver='vfio-pci')
            vfs_mac = [
                "00:12:34:56:{1}:{0}".format(
                    str(vf_index).zfill(2), str(index + 1).zfill(2))
                for vf_index in range(max_vfs)]
            self.vf_ports_info[port_id] = {
                'pf_pci': pf_pci,
                'vfs_pci': port_obj.get_sriov_vfs_pci(),
                'vfs_mac': vfs_mac,
                'src_mac': "02:00:00:00:00:0%d" % index, }
        self.logger.debug(pformat(self.vf_ports_info))

    def vf_destroy(self):
        if not self.vf_ports_info:
            return
        for port_id, _ in self.vf_ports_info.items():
            self.dut.destroy_sriov_vfs_by_port(port_id)
            port_obj = self.dut.ports_info[port_id]['port']
            port_obj.bind_driver(self.drivername)
        self.vf_ports_info = None

    def vf_whitelist(self):
        pf1_vf0 = self.vf_ports_info[0].get('vfs_pci')[0]
        pf1_vf1 = self.vf_ports_info[0].get('vfs_pci')[1]
        pf1_vf2 = self.vf_ports_info[0].get('vfs_pci')[2]
        pf2_vf0 = self.vf_ports_info[1].get('vfs_pci')[0] \
            if len(self.vf_ports_info) == 2 else ''
        whitelist = {
            'pf1_vf0_dcf': f"-w {pf1_vf0},cap=dcf",
            'pf1_vf1_dcf': f"-w {pf1_vf1},cap=dcf",
            'pf1_vf0_pf2_vf0_dcf': f"-w {pf1_vf0},cap=dcf -w {pf2_vf0},cap=dcf",
            'pf1_vf1_vf2': f"-w {pf1_vf1} -w {pf1_vf2}",
            'pf1_vf1': f"-w {pf1_vf1}",
            'pf2_vf0_dcf': f"-w {pf2_vf0},cap=dcf",
        }
        return whitelist

    def vf_set_mac_addr(self, dut_port_id=0, vf_id=1):
        intf = self.dut.ports_info[dut_port_id]['port'].intf_name
        cmd = f"ip link set {intf} vf 1 mac 00:01:02:03:04:05"
        self.d_a_con(cmd)
        self.vf_testpmd2_reset_port()

    def vf_set_trust(self, dut_port_id=0, vf_id=0, flag='on'):
        '''
        Set a VF as trust
        '''
        intf = self.dut.ports_info[dut_port_id]['port'].intf_name
        cmd = f"ip link set {intf} vf {vf_id} trust {flag}"
        self.d_a_con(cmd)

    def vf_set_trust_off(self):
        '''
        Turn off VF trust mode
        '''
        self.vf_set_trust(flag='off')

    def testpmd_set_flow_rule(self, dut_port_id=0, con_name='vf_dcf'):
        '''
        Set switch rule to VF from DCF
        '''
        cmd = (
            'flow create '
            '{port} '
            'priority 0 '
            'ingress pattern eth / ipv4 src is {ip_src} dst is {ip_dst} / end '
            'actions vf id {vf_id} / end'
        ).format(**{
            'port': dut_port_id,
            'vf_id': 1,
            'ip_src': self.get_ip_layer()['ipv4']['src'],
            'ip_dst': self.get_ip_layer()['ipv4']['dst'],
        })

        con = self.d_con if con_name == 'vf_dcf' else self.vf_pmd2_con
        output = con([cmd, "testpmd> ", 15])
        return output

    def init_vf_dcf_testpmd(self):
        self.vf_dcf_testpmd = "{}/{}/app/testpmd".format(
            self.target_dir, self.dut.target)

    def start_vf_dcf_testpmd(self, pmd_opiton):
        whitelist_name, prefix = pmd_opiton
        cores = self.corelist[:5]
        core_mask = utils.create_mask(cores)
        whitelist = self.vf_whitelist().get(whitelist_name)
        cmd = (
            "{bin} "
            "-v "
            "-c {core_mask} "
            "-n {mem_channel} "
            "{whitelist} "
            "--file-prefix={prefix} "
            "-- -i ").format(**{
                'bin': self.vf_dcf_testpmd,
                'core_mask': core_mask,
                'mem_channel': self.dut.get_memory_channels(),
                'whitelist': whitelist,
                'prefix': prefix, })
        self.vf_dcf_pmd_start_output = self.d_con([cmd, "testpmd> ", 120])
        self.is_vf_dcf_pmd_on = True
        time.sleep(1)

    def close_vf_dcf_testpmd(self):
        if not self.is_vf_dcf_pmd_on:
            return
        try:
            self.d_con(['quit', '# ', 15])
        except Exception as e:
            self.logger.error(traceback.format_exc())
        self.is_vf_dcf_pmd_on = False

    def kill_vf_dcf_process(self):
        '''
        Kill DCF process
        '''
        cmd = "ps aux | grep testpmd"
        self.d_a_con(cmd)
        cmd = r"kill -9 `ps -ef | grep testpmd | grep -v grep | grep -v testpmd_vf | awk '{print $2}'`"
        self.d_a_con(cmd)
        self.is_vf_dcf_pmd_on = False
        time.sleep(2)
        cmd = "ps aux | grep testpmd"
        self.d_a_con(cmd)

    def vf_dcf_testpmd_set_flow_rule(self, dut_port_id=0):
        return self.testpmd_set_flow_rule(dut_port_id)

    def get_vf_dcf_testpmd_start_output(self):
        output = self.vf_dcf_pmd_start_output
        msg = "vf dcf testpmd boot up output is empty"
        self.verify(output, msg)
        return output

    def create_vf_testpmd2(self):
        self.vf_testpmd2 = "{}/{}/app/testpmd_vf".format(
            self.target_dir, self.dut.target)
        cmd = 'rm -f {vf_pmd2};cp {vf_dcf_pmd} {vf_pmd2}'.format(
            **{'vf_dcf_pmd': self.vf_dcf_testpmd, 'vf_pmd2': self.vf_testpmd2})
        self.d_a_con(cmd)

    def init_vf_testpmd2(self):
        self.create_vf_testpmd2()
        self.vf_pmd2_session_name = 'vf_testpmd2'
        self.vf_pmd2_session = self.dut.create_session(
            self.vf_pmd2_session_name)

    def start_vf_testpmd2(self, pmd_opiton):
        whitelist_name, prefix = pmd_opiton
        cores = self.corelist[5:]
        core_mask = utils.create_mask(cores)
        whitelist = self.vf_whitelist().get(whitelist_name)
        cmd = (
            "{bin} "
            "-v "
            "-c {core_mask} "
            "-n {mem_channel} "
            "{whitelist} "
            "--file-prefix={prefix} "
            "-- -i ").format(**{
                'bin': self.vf_testpmd2,
                'core_mask': core_mask,
                'mem_channel': self.dut.get_memory_channels(),
                'whitelist': whitelist,
                'prefix': prefix, })
        self.vf_pmd2_start_output = self.vf_pmd2_con([cmd, "testpmd> ", 120])
        self.is_vf_pmd2_on = True
        cmds = [
            'set verbose 1',
            'set fwd mac',
            'start'] if prefix == 'vf' else ['start']
        [self.vf_pmd2_con([cmd, "testpmd> ", 15]) for cmd in cmds]
        time.sleep(1)

    def close_vf_testpmd2(self):
        if not self.is_vf_pmd2_on:
            return
        try:
            self.vf_pmd2_con(['quit', '# ', 15])
        except Exception as e:
            self.logger.error(traceback.format_exc())
        self.is_vf_pmd2_on = False

    def vf_testpmd2_reset_port(self):
        if not self.is_vf_pmd2_on:
            return
        cmds = [
            'stop',
            'port stop all',
            'port reset all',
            'port start all',
            'start',
        ]
        [self.vf_pmd2_con([cmd, "testpmd> ", 15]) for cmd in cmds]

    def vf_testpmd2_set_flow_rule(self, dut_port_id=0):
        self.testpmd_set_flow_rule(dut_port_id, con_name='vf2')

    def vf_pmd2_clear_port_stats(self):
        cmd = 'clear port stats all'
        self.vf_pmd2_con([cmd, "testpmd> ", 15])

    def check_vf_pmd2_stats(self, traffic, portid=0, is_traffic_valid=True):
        pmd = PmdOutput(self.dut, session=self.vf_pmd2_session)
        info = pmd.get_pmd_stats(portid) or {}
        ori_pkt = info.get('RX-packets') or 0
        traffic()
        info = pmd.get_pmd_stats(portid) or {}
        rx_pkt = info.get('RX-packets') or 0
        check_pkt = rx_pkt - ori_pkt
        if is_traffic_valid:
            msg = f"port {portid} should receive packets, but no traffic happen"
            self.verify(check_pkt and check_pkt > 0, msg)
        else:
            msg = f"port {portid} should not receive packets"
            self.verify(not check_pkt, msg)
        return rx_pkt

    def get_vf_testpmd2_start_output(self):
        output = self.vf_pmd2_start_output
        msg = "vf testpmd2 boot up output is empty"
        self.verify(output, msg)
        return output

    def check_vf_pmd2_traffic(self, func_name, topo=None, flag=False):
        dut_port_id, vf_id = topo if topo else [0, 1]
        pkt = self.config_stream(dut_port_id, vf_id)
        traffic = partial(self.send_packet_by_scapy, pkt, dut_port_id, 1)
        self.vf_pmd2_clear_port_stats()
        self.check_vf_pmd2_stats(traffic)
        status_change_func = getattr(self, func_name)
        status_change_func()
        self.check_vf_pmd2_stats(traffic, is_traffic_valid=flag)

    def run_test_pre(self, pmd_opitons):
        pri_pmd_option = pmd_opitons[0]
        self.start_vf_dcf_testpmd(pri_pmd_option)
        if len(pmd_opitons) == 1:  # if only one pmd
            return
        slave_pmd_option = pmd_opitons[1]
        self.start_vf_testpmd2(slave_pmd_option)

    def run_test_post(self):
        # close all binary processes
        self.close_vf_testpmd2()
        self.close_vf_dcf_testpmd()
        time.sleep(5)

    def check_support_dcf_mode_01_result(self):
        dcf_output = self.get_vf_dcf_testpmd_start_output()
        pf1_vf0 = self.vf_ports_info[0].get('vfs_pci')[0]
        expected_strs = [
            f"Probe PCI driver: net_ice_dcf ({self.dcf_dev_id}) device: {pf1_vf0} (socket {self.socket})",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in dcf_output, msg)

    def verify_support_dcf_mode_01(self):
        '''
        Generate 1 trust VF on 1 PF, and request 1 DCF on the trust VF.
        PF should grant DCF mode to it.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'vf']]
            self.run_test_pre(pmd_opts)
            self.check_support_dcf_mode_01_result()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def check_support_dcf_mode_02_result(self):
        dcf_output = self.get_vf_dcf_testpmd_start_output()
        vf2_output = self.get_vf_testpmd2_start_output()
        # vf 1 testpmd
        pf1_vf0 = self.vf_ports_info[0].get('vfs_pci')[0]
        expected_strs = [
            f"Probe PCI driver: net_ice_dcf ({self.dcf_dev_id}) device: {pf1_vf0} (socket {self.socket})",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in dcf_output, msg)
        # vf 2 testpmd
        pf2_vf0 = self.vf_ports_info[1].get('vfs_pci')[0]
        expected_strs = [
            f"Probe PCI driver: net_ice_dcf ({self.dcf_dev_id}) device: {pf2_vf0} (socket {self.socket})",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in vf2_output, msg)

    def verify_support_dcf_mode_02(self):
        '''
        Generate 2 trust VFs on 2 PFs, each trust VF request DCF.
        Each PF should grant DCF mode to them.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            self.vf_set_trust(dut_port_id=1)
            pmd_opts = [['pf1_vf0_dcf', 'dcf1'], ['pf2_vf0_dcf', 'dcf2']]
            self.run_test_pre(pmd_opts)
            self.check_support_dcf_mode_02_result()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def check_support_dcf_mode_03_result(self):
        dcf_output = self.get_vf_dcf_testpmd_start_output()
        dmesg_output = self.get_dmesg()
        # vf testpmd
        pf1_vf1 = self.vf_ports_info[0].get('vfs_pci')[1]
        expected_strs = [
            f"Probe PCI driver: net_ice_dcf ({self.dcf_dev_id}) device: {pf1_vf1} (socket {self.socket})",
            "ice_dcf_get_vf_resource(): Failed to get response of OP_GET_VF_RESOURCE",
            "ice_dcf_init_hw(): Failed to get VF resource",
            "ice_dcf_dev_init(): Failed to init DCF hardware",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in dcf_output, msg)
        # dmesg content
        pf1 = self.vf_ports_info[0].get('pf_pci')
        expected_strs = [
            f"ice {pf1}: VF 1 requested DCF capability, but only VF 0 is allowed to request DCF capability",
            f"ice {pf1}: VF 1 failed opcode 3, retval: -5",
        ]
        msg = 'no dmesg output'
        self.verify(dmesg_output, msg)
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in dmesg_output, msg)

    def verify_support_dcf_mode_03(self):
        except_content = None
        try:
            self.vf_set_trust(vf_id=1)
            self.clear_dmesg()
            pmd_opts = [['pf1_vf1_dcf', 'vf']]
            self.run_test_pre(pmd_opts)
            self.check_support_dcf_mode_03_result()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
            self.vf_set_trust(vf_id=1, flag='off')
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def check_support_dcf_mode_04_result(self):
        dcf_output = self.get_vf_dcf_testpmd_start_output()
        dmesg_output = self.get_dmesg()
        # vf testpmd
        pf1_vf0 = self.vf_ports_info[0].get('vfs_pci')[0]
        expected_strs = [
            "ice_dcf_get_vf_resource(): Failed to get response of OP_GET_VF_RESOURCE",
            "ice_dcf_init_hw(): Failed to get VF resource",
            "ice_dcf_dev_init(): Failed to init DCF hardware",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in dcf_output, msg)
        # dmesg content
        pf1 = self.vf_ports_info[0].get('pf_pci')
        expected_strs = [
            f"ice {pf1}: VF needs to be trusted to configure DCF capability",
            f"ice {pf1}: VF 0 failed opcode 3, retval: -5",
        ]
        msg = 'no dmesg output'
        self.verify(dmesg_output, msg)
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in dmesg_output, msg)

    def verify_support_dcf_mode_04(self):
        except_content = None
        try:
            self.vf_set_trust_off()
            self.clear_dmesg()
            pmd_opts = [['pf1_vf0_dcf', 'vf']]
            self.run_test_pre(pmd_opts)
            self.check_support_dcf_mode_04_result()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_support_dcf_mode_05(self):
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf'], ['pf1_vf1', 'vf']]
            self.run_test_pre(pmd_opts)
            self.vf_dcf_testpmd_set_flow_rule()
            self.check_vf_pmd2_traffic('close_vf_dcf_testpmd')
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_handle_switch_filter_01(self):
        '''
        If turn trust mode off, when DCF launched. The DCF rules should be removed.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf'], ['pf1_vf1', 'vf']]
            self.run_test_pre(pmd_opts)
            self.vf_dcf_testpmd_set_flow_rule()
            self.check_vf_pmd2_traffic('vf_set_trust_off')
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_handle_switch_filter_02(self):
        '''
        If kill DCF process, when DCF launched. The DCF rules should be removed.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf'], ['pf1_vf1', 'vf']]
            self.run_test_pre(pmd_opts)
            self.vf_dcf_testpmd_set_flow_rule()
            self.check_vf_pmd2_traffic('kill_vf_dcf_process', flag=True)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def check_pmd2_create_dcf_failed(self, vf_id=0):
        vf2_output = self.get_vf_testpmd2_start_output()
        pf1_vf = self.vf_ports_info[0].get('vfs_pci')[vf_id]
        expected_strs = [
            f"Probe PCI driver: net_ice_dcf ({self.dcf_dev_id}) device: {pf1_vf} (socket {self.socket})",
        ]
        for expected_str in expected_strs:
            msg = "Expect: the second testpmd can't be launched"
            self.verify(expected_str not in vf2_output, msg)
        expected_strs = [
            f"EAL: Requested device {pf1_vf} cannot be used"
        ]
        for expected_str in expected_strs:
            msg = "Expect: the second testpmd can't be launched"
            self.verify(expected_str in vf2_output, msg)

    def verify_handle_switch_filter_03(self):
        '''
        Launch 2nd DCF process on the same VF, PF shall reject the request.
        DPDK does not support to open 2nd DCF PMD driver on same VF.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf'], ['pf1_vf0_dcf', 'dcf2']]
            self.run_test_pre(pmd_opts)
            self.check_pmd2_create_dcf_failed()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_handle_switch_filter_04(self):
        '''
        If DCF enabled, one of VF reset. DCF shall clean up all the rules of this VF.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf'], ['pf1_vf1', 'vf']]
            self.run_test_pre(pmd_opts)
            self.vf_dcf_testpmd_set_flow_rule()
            self.check_vf_pmd2_traffic('vf_set_mac_addr', flag=True)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def check_dcf_pmd_create_dcf_failed(self, vf_id=0):
        dcf_output = self.get_vf_dcf_testpmd_start_output()
        pf1_vf0 = self.vf_ports_info[0].get('vfs_pci')[vf_id]
        expected_strs = [
            f"Probe PCI driver: net_ice_dcf ({self.dcf_dev_id}) device: {pf1_vf0} (socket {self.socket})",
            "ice_dcf_get_vf_resource(): Failed to get response of OP_GET_VF_RESOURCE",
            "ice_dcf_init_hw(): Failed to get VF resource",
            "ice_dcf_dev_init(): Failed to init DCF hardware",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display, PF should reject DCF mode.".format(expected_str)
            self.verify(expected_str in dcf_output, msg)

    def check_dcf_pmd_create_dcf_success(self):
        output = self.get_vf_dcf_testpmd_start_output()
        pf1_vf0 = self.vf_ports_info[0].get('vfs_pci')[0]
        expected_strs = [
            f"Probe PCI driver: net_ice_dcf ({self.dcf_dev_id}) device: {pf1_vf0} (socket {self.socket})",
            "ice_load_pkg_type(): Active package is",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display, DCF mode should be grant".format(expected_str)
            self.verify(expected_str in output, msg)

    def verify_dcf_with_adq_01(self):
        '''
        When ADQ set on PF, PF should reject the DCF mode. Remove the ADQ setting,
        PF shall accept DCF mode.

        Host kernel version is required 4.19+, and MACVLAN offload should be set off
        '''
        except_content = None
        try:
            self.vf_set_trust()
            self.set_adq_on_pf()
            pmd_opts = [['pf1_vf0_dcf', 'dcf']]
            # Expect: testpmd can't be launched. PF should reject DCF mode.
            self.run_test_pre(pmd_opts)
            self.check_dcf_pmd_create_dcf_failed()
            self.run_test_post()
            # Expect: testpmd can launch successfully. DCF mode can be grant
            self.remove_adq_on_pf()
            self.run_test_pre(pmd_opts)
            self.check_dcf_pmd_create_dcf_success()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.remove_adq_on_pf()
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def check_dcf_with_adq_failed_result(self, output):
        expected_strs = [
            "Exclusivity flag on",
            "RTNETLINK answers: Operation not supported", ]
        for _output in output:
            if any(expected_str in output for expected_str in expected_strs):
                msg = "exclusive action occurs correctly"
                self.logger.info(msg)
                break
        else:
            msg = "Expect: ADQ command can't be success"
            self.verify(False, msg)

    def check_dcf_with_adq_result1(self, output):
        check_strs = [
            "Exclusivity flag on",
            "RTNETLINK answers: Device or resource busy", ]
        for _output in output:
            status = all(check_str not in _output for check_str in check_strs)
            msg = "ADQ setting on PF shall be successful, but failed"
            self.verify(status, msg)

    def verify_dcf_with_adq_02(self):
        '''
        When DCF mode enabled, ADQ setting on PF shall fail.
        Exit DCF mode, ADQ setting on PF shall be successful.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf']]
            self.run_test_pre(pmd_opts)
            # Expect: ADQ command can't be success
            output = self.set_adq_on_pf()
            self.remove_adq_on_pf()
            self.run_test_post()
            self.check_dcf_with_adq_failed_result(output)
            # Expect: ADQ can be set.
            output = self.set_adq_on_pf()
            self.check_dcf_with_adq_result1(output)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.remove_adq_on_pf()
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_dcf_with_adq_03(self):
        '''
        Configure the DCF on 1 PF port and configure ADQ on the other PF port.
        Then turn off DCF, other PF's should not be impact.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf']]
            self.run_test_pre(pmd_opts)
            # run PF1 DCF mode, ADQ can be set.
            output = self.set_adq_on_pf(1)
            self.remove_adq_on_pf(1)
            self.run_test_post()
            self.check_dcf_with_adq_result1(output)
            # quit PF1 DCF mode, ADQ can be set.
            output = self.set_adq_on_pf(1)
            self.check_dcf_with_adq_result1(output)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.remove_adq_on_pf(1)
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_dcf_with_l2fwd_01(self):
        '''
        When L2 forwarding set, PF should reject the DCF mode.
        Remove L2 forwarding set, PF shall accept the DCF mode.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            self.set_adq_mac_vlan()
            pmd_opts = [['pf1_vf0_dcf', 'dcf']]
            # Expect: testpmd can't be launched. PF should reject DCF mode.
            self.run_test_pre(pmd_opts)
            self.check_dcf_pmd_create_dcf_failed()
            self.run_test_post()
            # Expect: testpmd can launch successfully. DCF mode can be grant
            self.remove_adq_mac_vlan()
            self.run_test_pre(pmd_opts)
            self.check_dcf_pmd_create_dcf_success()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.remove_adq_mac_vlan()
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def check_dcf_with_l2fwd_adp_failed_result(self, output):
        expected_str = "Could not change any device features"
        status = any(expected_str in _output for _output in output)
        msg = "When DCF mode enabled, PF should set L2 forwarding failed."
        self.verify(status, msg)

    def check_dcf_with_l2fwd_adp_result(self, output):
        check_strs = [
            "Exclusivity flag on",
            "RTNETLINK answers: Device or resource busy", ]
        for _output in output:
            status = all(check_str not in _output for check_str in check_strs)
            msg = "PF should set L2 forwarding successful, but failed"
            self.verify(status, msg)

    def verify_dcf_with_l2fwd_02(self):
        '''
        When DCF mode enabled, PF can't set L2 forwarding.
        Exit DCF mode, PF can set L2 forwarding.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf']]
            self.run_test_pre(pmd_opts)
            # When DCF mode enabled, PF can't set L2 forwarding.
            output = self.set_adq_mac_vlan()
            self.remove_adq_mac_vlan()
            self.run_test_post()
            self.check_dcf_with_l2fwd_adp_failed_result(output)
            # Exit DCF mode, PF can set L2 forwarding.
            output = self.set_adq_mac_vlan()
            self.check_dcf_with_l2fwd_adp_result(output)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.remove_adq_mac_vlan()
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_dcf_with_l2fwd_03(self):
        '''
        Configure the DCF on 1 PF port and configure MAC-VLAN on the other PF port.
        Then turn off DCF, other PF's MAC-VLAN filter should not be impact.
        '''
        except_content = None
        try:
            self.vf_set_trust()
            pmd_opts = [['pf1_vf0_dcf', 'dcf']]
            self.run_test_pre(pmd_opts)
            # run PF1 DCF mode, PF2 can set L2 forwarding.
            output = self.set_adq_mac_vlan(1)
            self.remove_adq_mac_vlan(1)
            self.run_test_post()
            self.check_dcf_with_l2fwd_adp_result(output)
            # Exit PF1 DCF mode, PF2 can set L2 forwarding.
            output = self.set_adq_mac_vlan(1)
            self.check_dcf_with_l2fwd_adp_result(output)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.remove_adq_mac_vlan(1)
            self.run_test_post()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_supported_nic(self):
        supported_drivers = ['ice']
        result = all([self.dut.ports_info[index]['port'].default_driver in
                      supported_drivers
                      for index in self.dut_ports])
        msg = "current nic <{0}> is not supported".format(self.nic)
        self.verify(result, msg)

    def preset_pmd_res(self):
        self.dcf_dev_id = '8086:1889'
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.corelist = self.dut.get_core_list(
            "1S/14C/1T", socket=self.socket)[4:]

    def clear_flags(self):
        self.is_vf_dcf_pmd_on = self.is_vf_pmd2_on = False
        self.vf_dcf_pmd_start_output = self.vf_pmd2_start_output = None

    def init_suite(self):
        self.is_vf_dcf_pmd_on = self.is_vf_pmd2_on = self.is_adq_set = \
            self.vf_pmd2_session = None
        self.vf_dcf_pmd_start_output = self.vf_pmd2_start_output = None
        self.vf_init()

    def preset_test_environment(self):
        cmds = [
            "uname -a",
            "modinfo ice | grep version:", ]
        self.d_a_con(cmds)
        self.init_adq()
        self.init_vf_dcf_testpmd()
        self.init_vf_testpmd2()
        self.preset_pmd_res()
        self.vf_create()

    def destroy_resource(self):
        try:
            self.vf_destroy()
        finally:
            msg = "close vf devices"
            self.logger.info(msg)
        if self.vf_pmd2_session:
            self.dut.close_session(self.vf_pmd2_session)
            self.vf_pmd2_session = None
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.init_suite()
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Not enough ports")
        self.verify_supported_nic()
        # prepare testing environment
        self.preset_test_environment()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.destroy_resource()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        self.clear_flags()

    def test_support_dcf_mode_01(self):
        '''
        DCF on 1 trust VF on 1 PF
        '''
        msg = "begin : DCF on 1 trust VF on 1 PF"
        self.logger.info(msg)
        self.verify_support_dcf_mode_01()

    def test_support_dcf_mode_02(self):
        '''
        DCF on 2 PFs, 1 trust VF on each PF
        '''
        self.verify(len(self.dut_ports) >= 2, "2 ports at least")
        msg = "begin : DCF on 2 PFs, 1 trust VF on each PF"
        self.logger.info(msg)
        self.verify_support_dcf_mode_02()

    def test_support_dcf_mode_03(self):
        '''
        Check only VF zero can get DCF mode
        '''
        msg = "begin : Check only VF zero can get DCF mode"
        self.logger.info(msg)
        self.verify_support_dcf_mode_03()

    def test_support_dcf_mode_04(self):
        '''
        Check only trusted VF can get DCF mode
        '''
        msg = "begin : Check only trusted VF can get DCF mode"
        self.logger.info(msg)
        self.verify_support_dcf_mode_04()

    def test_support_dcf_mode_05(self):
        '''
        DCF graceful exit
        '''
        msg = "begin : DCF graceful exit"
        self.logger.info(msg)
        self.verify_support_dcf_mode_05()

    def test_handle_switch_filter_01(self):
        '''
        Turn trust mode off, when DCF launched
        '''
        msg = "begin : Turn trust mode off, when DCF launched"
        self.logger.info(msg)
        self.verify_handle_switch_filter_01()

    def test_handle_switch_filter_02(self):
        '''
        Kill DCF process
        '''
        msg = "begin : Kill DCF process"
        self.logger.info(msg)
        self.verify_handle_switch_filter_02()

    def test_handle_switch_filter_03(self):
        '''
        Launch 2nd DCF process on the same VF
        '''
        msg = "begin : Launch 2nd DCF process on the same VF"
        self.logger.info(msg)
        self.verify_handle_switch_filter_03()

    def test_handle_switch_filter_04(self):
        '''
        DCF enabled, one of VF reset
        '''
        msg = "begin : DCF enabled, one of VF reset"
        self.logger.info(msg)
        self.verify_handle_switch_filter_04()

    def test_dcf_with_adq_01(self):
        '''
        When ADQ set on PF, PF should reject the DCF mode
        '''
        msg = "begin : When ADQ set on PF, PF should reject the DCF mode"
        self.logger.info(msg)
        self.verify_dcf_with_adq_01()

    def test_dcf_with_adq_02(self):
        '''
        When DCF mode enabled, ADQ setting on PF shall fail
        '''
        msg = "begin : When DCF mode enabled, ADQ setting on PF shall fail"
        self.logger.info(msg)
        self.verify_dcf_with_adq_02()

    def test_dcf_with_adq_03(self):
        '''
        DCF and ADQ can be enabled on different PF
        '''
        self.verify(len(self.dut_ports) >= 2, "2 ports at least")
        msg = "begin : DCF and ADQ can be enabled on different PF"
        self.logger.info(msg)
        self.verify_dcf_with_adq_03()

    def test_dcf_with_l2fwd_01(self):
        '''
        When L2 forwarding set, PF should reject the DCF mode
        '''
        msg = "begin : When L2 forwarding set, PF should reject the DCF mode"
        self.logger.info(msg)
        self.verify_dcf_with_l2fwd_01()

    def test_dcf_with_l2fwd_02(self):
        '''
        When DCF mode enabled, PF can't set L2 forwarding
        '''
        msg = "begin : When DCF mode enabled, PF can't set L2 forwarding"
        self.logger.info(msg)
        self.verify_dcf_with_l2fwd_02()

    def test_dcf_with_l2fwd_03(self):
        '''
        DCF and L2 forwarding can be enabled on different PF
        '''
        self.verify(len(self.dut_ports) >= 2, "2 ports at least")
        msg = "begin : DCF and L2 forwarding can be enabled on different PF"
        self.logger.info(msg)
        self.verify_dcf_with_l2fwd_03()

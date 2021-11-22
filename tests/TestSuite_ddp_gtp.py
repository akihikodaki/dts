# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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

import random
import re
import sys
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.qemu_kvm import QEMUKvm
from framework.settings import get_nic_name
from framework.test_case import TestCase

VM_CORES_MASK = 'all'


class TestDdpGtp(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):
        self.verify('fortville' in self.nic,
                    'ddp gtp can not support %s nic' % self.nic)
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.vm0 = None
        self.env_done = False
        profile_file = 'dep/gtp.pkgo'
        profile_dst = "/tmp/"
        self.dut.session.copy_file_to(profile_file, profile_dst)
        self.PF_Q_strip = 'RTE_LIBRTE_I40E_QUEUE_NUM_PER_PF'
        # commit ee653bd8, queue number of per vf default value is defined
        # in drivers/net/i40e/i40e_ethdev.c, named as RTE_LIBRTE_I40E_QUEUE_NUM_PER_VF
        self.VF_Q_strip = 'RTE_LIBRTE_I40E_QUEUE_NUM_PER_VF'
        self.PF_QUEUE = self.search_queue_number(self.PF_Q_strip)
        self.VF_QUEUE = self.search_queue_number(self.VF_Q_strip)

        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')

    def insmod_modprobe(self,modename=''):
        """
        Insmod modProbe before run test case
        """
        if modename == "igb_uio":
            self.dut.send_expect("modprobe uio", "#", 10)
            out = self.dut.send_expect("lsmod | grep igb_uio", "#")
            if "igb_uio" in out:
                self.dut.send_expect("rmmod -f igb_uio", "#", 10)
            self.dut.send_expect("insmod ./" + self.target + "/kmod/igb_uio.ko", "#", 10)

            out = self.dut.send_expect("lsmod | grep igb_uio", "#")
            assert ("igb_uio" in out), "Failed to insmod igb_uio"

    def set_up(self):
        self.dut_testpmd = PmdOutput(self.dut)
        self.used_dut_port = self.dut_ports[0]
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        if "vf" in self._suite_result.test_case:
            self.insmod_modprobe("igb_uio")
            self.bind_nic_driver(self.dut_ports,"igb_uio")
            self.setup_vm_env()
            self.load_profile()
            self.vm0_testpmd.start_testpmd(
                VM_CORES_MASK, "--port-topology=chained --txq=%s --rxq=%s"
                               % (self.VF_QUEUE, self.VF_QUEUE))
            self.vm0_testpmd.execute_cmd('set fwd rxonly')
            self.vm0_testpmd.execute_cmd('set verbose 1')
            self.vm0_testpmd.execute_cmd('start')
        else:
            self.load_profile()

    def search_queue_number(self, Q_strip):
        """
        Search max queue number from configuration.
        """
        if Q_strip is self.PF_Q_strip:
            out = self.dut.send_expect("cat config/rte_config.h", "]# ", 10)
            pattern = "define (%s) (\d*)" % Q_strip
        else:
            out = self.dut.send_expect("cat drivers/net/i40e/i40e_ethdev.c", "]# ", 10)
            pattern = "#define %s\s*(\d*)" % Q_strip
        s = re.compile(pattern)
        res = s.search(out)
        if res is None:
            print((utils.RED('Search no queue number.')))
            return None
        else:
            if Q_strip is self.VF_Q_strip:
                queue = res.group(1)
            else:
                queue = res.group(2)
            return int(queue)

    def setup_vm_env(self, driver='igb_uio'):
        """
        Create testing environment with VF generated from 1PF
        """
        if self.env_done is False:
            self.dut.generate_sriov_vfs_by_port(
                self.used_dut_port, 1, driver=driver)
            self.sriov_vfs_port = self.dut.ports_info[
                self.used_dut_port]['vfs_port']
            for port in self.sriov_vfs_port:
                    port.bind_driver(self.vf_driver)
            time.sleep(1)
            vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
            # set up VM0 ENV
            self.vm0 = QEMUKvm(self.dut, 'vm0', 'ddp_gtp')
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            try:
                self.vm0_dut = self.vm0.start()
                if self.vm0_dut is None:
                    raise Exception("Set up VM0 ENV failed!")
            except Exception as e:
                self.destroy_vm_env()
                raise Exception(e)
            self.vm0_dut_ports = self.vm0_dut.get_ports('any')
            self.vm0_testpmd = PmdOutput(self.vm0_dut)
            self.env_done = True

    def destroy_vm_env(self):

        if getattr(self, 'vm0', None):
            self.vm0_dut.kill_all()
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, 'used_dut_port', None):
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]['port']
            self.used_dut_port = None

        self.env_done = False

    def load_profile(self):
        """
        Load profile to update FVL configuration tables, profile will be
        stored in binary file and need to be passed to AQ to program FVL
        during initialization stage.
        """
        self.dut_testpmd.start_testpmd(
            "Default", "--pkt-filter-mode=perfect --port-topology=chained \
            --txq=%s --rxq=%s"
            % (self.PF_QUEUE, self.PF_QUEUE))

        self.dut_testpmd.execute_cmd('port stop all')
        time.sleep(1)
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.dut_testpmd.execute_cmd('ddp add 0 /tmp/gtp.pkgo,/tmp/gtp.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("Profile number is: 1" in out,
                    "Failed to load ddp profile!!!")
        self.dut_testpmd.execute_cmd('port start all')
        time.sleep(1)
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd('start')
        time.sleep(2)

    def gtp_packets(
            self, type='fdir', tunnel_pkt='gtpu', inner_L3='ipv4',
            match_opt='matched', chk='', teid=0xF):
        """
        Generate different GTP types according to different parameters.
        Input:
        filter type: includes flow director and cloud filter
        tunnel packet: includes GTPC and GTPU
        inner_L3: GTPC has no inner L3. GTPU has no, IPV4 and IPV6 inner L3.
        match_opt: PF or VSIs receive match packets to configured queue, but
                   receive not match packets to queue 0. Flow director
                   directs different TEIDs, inner L3 GTP packets to different
                   queues. Cloud filter directs different TEIDs GTP packets
                   to different queues.
        chk: checksum
        teid: GTP teid
        """
        pkts = []
        pkts_gtpc_pay = {'IPV4/GTPC': 'Ether()/IP()/UDP(%sdport=2123)/GTP_U_Header(teid=%s)/Raw("X"*20)' % (chk, teid),
                         'IPV6/GTPC': 'Ether()/IPv6()/UDP(%sdport=2123)/GTP_U_Header(teid=%s)/Raw("X"*20)' % (chk, teid)}

        pkts_gtpu_pay = {'IPV4/GTPU': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/Raw("X"*20)' % (chk, teid),
                         'IPV6/GTPU': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/Raw("X"*20)' % (chk, teid)}

        pkts_gtpu_ipv4 = {'IPV4/GTPU/IPV4': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV4/FRAG': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP(frag=5)/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV4/UDP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/UDP()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV4/TCP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/TCP()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV4/SCTP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/SCTP()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV4/ICMP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/ICMP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV4': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV4/FRAG': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP(frag=5)/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV4/UDP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/UDP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV4/TCP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/TCP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV4/SCTP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/SCTP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV4/ICMP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IP()/ICMP()/Raw("X"*20)' % (chk, teid)}

        pkts_gtpu_ipv6 = {'IPV4/GTPU/IPV6/FRAG': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/IPv6ExtHdrFragment()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV6': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV6/UDP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/UDP()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV6/TCP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/TCP()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV6/SCTP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/SCTP()/Raw("X"*20)' % (chk, teid),
                          'IPV4/GTPU/IPV6/ICMP': 'Ether()/IP()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6(nh=58)/ICMP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV6/FRAG': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/IPv6ExtHdrFragment()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV6': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV6/UDP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/UDP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV6/TCP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/TCP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV6/SCTP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6()/SCTP()/Raw("X"*20)' % (chk, teid),
                          'IPV6/GTPU/IPV6/ICMP': 'Ether()/IPv6()/UDP(%sdport=2152)/GTP_U_Header(teid=%s)/IPv6(nh=58)/ICMP()/Raw("X"*20)' % (chk, teid)}

        if match_opt == 'matched':
            if tunnel_pkt is 'gtpc' and inner_L3 is None:
                pkts = pkts_gtpc_pay
            if tunnel_pkt is 'gtpu' and inner_L3 is None:
                pkts = pkts_gtpu_pay
            if tunnel_pkt is 'gtpu' and inner_L3 is 'ipv4':
                pkts = pkts_gtpu_ipv4
            if tunnel_pkt is 'gtpu' and inner_L3 is 'ipv6':
                pkts = pkts_gtpu_ipv6

        if match_opt == 'not matched':
            if type is 'fdir':
                if tunnel_pkt is 'gtpc' and inner_L3 is None:
                    pkts = dict(
                        list(pkts_gtpu_pay.items()) +
                        list(pkts_gtpu_ipv4.items()) +
                        list(pkts_gtpu_ipv6.items()))
                if tunnel_pkt is 'gtpu' and inner_L3 is None:
                    pkts = dict(
                        list(pkts_gtpc_pay.items()) +
                        list(pkts_gtpu_ipv4.items()) +
                        list(pkts_gtpu_ipv6.items()))
                if tunnel_pkt is 'gtpu' and inner_L3 is 'ipv4':
                    pkts = dict(
                        list(pkts_gtpc_pay.items()) +
                        list(pkts_gtpu_pay.items()) +
                        list(pkts_gtpu_ipv6.items()))
                if tunnel_pkt is 'gtpu' and inner_L3 is 'ipv6':
                    pkts = dict(
                        list(pkts_gtpc_pay.items()) +
                        list(pkts_gtpu_pay.items()) +
                        list(pkts_gtpu_ipv4.items()))
            if type is 'clfter':
                if tunnel_pkt is 'gtpc':
                    pkts = dict(
                        list(pkts_gtpu_pay.items()) +
                        list(pkts_gtpu_ipv4.items()) +
                        list(pkts_gtpu_ipv6.items()))
                if tunnel_pkt is 'gtpu':
                    pkts = pkts_gtpc_pay
        return pkts

    def gtp_test(
            self, type='fdir', port='pf', tunnel_pkt='gtpu', inner_L3='ipv4'):
        """
        Send GTP packet to dut, receive packet from configured queue.
        Input: filter type, port type, packet type, inner L3 type
        """
        queue = random.randint(1, self.PF_QUEUE - 1)
        if port != 'pf':
            queue = random.randint(1, self.VF_QUEUE - 1)
        random_teid = random.randint(0x0, 0xFFFFFFFF)
        correct_teid = hex(random_teid)
        wrong_teid = hex((random_teid + 2) % int(0xFFFFFFFF))
        if type is 'fdir':
            if inner_L3 is None:
                self.dut_testpmd.execute_cmd(
                    'flow create 0 ingress pattern eth / ipv4 / udp / \
                    %s teid is %s / end actions queue index %d / end'
                    % (tunnel_pkt, correct_teid, queue))
            else:
                self.dut_testpmd.execute_cmd(
                    'flow create 0 ingress pattern eth / ipv4 / udp / \
                    %s teid is %s / %s / end actions queue index %d / end'
                    % (tunnel_pkt, correct_teid, inner_L3, queue))
        if type is 'clfter':
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 / udp / \
                %s teid is %s / end actions %s / queue index %d / end'
                % (tunnel_pkt, correct_teid, port, queue))
        count = 0
        for match_opt in ['matched', 'not matched']:
            teid = correct_teid
            pkts = []
            for teid_opt in ['correct teid', 'wrong teid']:
                chk = ''
                for chksum_opt in ['good chksum', 'bad chksum']:
                    pkts = self.gtp_packets(
                        type, tunnel_pkt, inner_L3, match_opt, chk, teid)
                    for packet_type in list(pkts.keys()):
                        count = count + 1
                        self.tester.scapy_append(
                            'sendp([%s], iface="%s")'
                            % (pkts[packet_type], self.tester_intf))
                    self.tester.scapy_execute()
                    if port is 'pf':
                        out = self.dut.get_session_output(timeout=5)
                    else:
                        out = self.vm0_dut.get_session_output(timeout=5)
                    self.verify(
                        count == out.count('port 0/queue %d' % queue),
                        "Failed to receive packet in this queue!!!")
                    if port is 'pf':
                        layerparams = ['L3_', 'TUNNEL_',
                                       'INNER_L3_', 'INNER_L4_']
                        ptypes = packet_type.split('/')
                        other_ptypes = ptypes[1:]
                        if 'IPV6' in ptypes:
                            other_ptypes.insert(0,'IPV4')
                        else:
                            other_ptypes.insert(0,'IPV6')
                        endparams = ['_EXT_UNKNOWN', '',
                                     '_EXT_UNKNOWN', '']
                        for layerparam, ptype, endparam in zip(
                                layerparams, ptypes, endparams):
                            layer_type = layerparam + ptype + endparam
                            self.verify(
                                layer_type in out,
                                "Failed to output ptype information!")
                        for layerparam, ptype, endparam in zip(
                                layerparams, other_ptypes, endparams):
                            layer_type = layerparam + ptype + endparam
                            self.verify(
                                layer_type in out,
                                "Failed to output ptype information!!!")
                    if queue != 0 and type is 'fdir':
                        self.verify(count == out.count("RTE_MBUF_F_RX_FDIR"),
                                    "Failed to test flow director!!!")
                    count = 0
                    if teid == wrong_teid or match_opt == 'not matched':
                        break
                    chk = 'chksum=0x1234,'
                if match_opt == 'not matched':
                    break
                queue = 0
                teid = wrong_teid

    def test_fdir_gtpc_pf(self):
        """
        GTP is supported by NVM with profile updated. Select flow director to
        do classification, send gtpc packet to PF, check PF could receive
        packet using configured queue, checksum is good.
        """
        self.gtp_test(
            type='fdir', port='pf', tunnel_pkt='gtpc', inner_L3=None)

    def test_fdir_gtpu_pf(self):
        """
        GTP is supported by NVM with profile updated. Select flow director to
        do classification, send gtpu packet to PF, check PF could receive
        packet using configured queue, checksum is good.
        """
        self.gtp_test(
            type='fdir', port='pf', tunnel_pkt='gtpu', inner_L3=None)
        self.gtp_test(
            type='fdir', port='pf', tunnel_pkt='gtpu', inner_L3='ipv4')
        self.gtp_test(
            type='fdir', port='pf', tunnel_pkt='gtpu', inner_L3='ipv6')

    def test_clfter_gtpc_pf(self):
        """
        GTP is supported by NVM with profile updated. Select cloud filter,
        send gtpc packet to PF, check PF could receive packet using
        configured queue, checksum is good.
        """
        self.gtp_test(
            type='clfter', port='pf', tunnel_pkt='gtpc', inner_L3=None)

    def test_clfter_gtpu_pf(self):
        """
        GTP is supported by NVM with profile updated. Select cloud filter,
        send gtpu packet to PF, check PF could receive packet using configured
        queue, checksum is good.
        """
        self.gtp_test(
            type='clfter', port='pf', tunnel_pkt='gtpu', inner_L3=None)
        self.gtp_test(
            type='clfter', port='pf', tunnel_pkt='gtpu', inner_L3='ipv4')
        self.gtp_test(
            type='clfter', port='pf', tunnel_pkt='gtpu', inner_L3='ipv6')

    def test_clfter_gtpc_vf(self):
        """
        GTP is supported by NVM with profile updated. Select cloud filter,
        send gtpc packet to VF, check PF could receive packet using configured
        queue, checksum is good.
        """
        self.gtp_test(
            type='clfter', port='vf id 0', tunnel_pkt='gtpc', inner_L3=None)

    def test_clfter_gtpu_vf(self):
        """
        GTP is supported by NVM with profile updated. Select cloud filter,
        send gtpu packet to VF, check PF could receive packet using configured
        queue, checksum is good.
        """
        self.gtp_test(
            type='clfter', port='vf id 0', tunnel_pkt='gtpu', inner_L3=None)
        self.gtp_test(
            type='clfter', port='vf id 0', tunnel_pkt='gtpu', inner_L3='ipv4')
        self.gtp_test(
            type='clfter', port='vf id 0', tunnel_pkt='gtpu', inner_L3='ipv6')

    def tear_down(self):
        if "vf" in self._suite_result.test_case:
            self.destroy_vm_env()
        self.dut_testpmd.execute_cmd('stop')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        if "Profile number is: 0" not in out:
            self.dut_testpmd.execute_cmd('port stop all')
            time.sleep(1)
            self.dut_testpmd.execute_cmd('ddp del 0 /tmp/gtp.bak')
            out = self.dut_testpmd.execute_cmd('ddp get list 0')
            self.verify("Profile number is: 0" in out,
                        "Failed to delete ddp profile!!!")
            self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.quit()


    def tear_down_all(self):
        if self.env_done:
            self.destroy_vm_env()


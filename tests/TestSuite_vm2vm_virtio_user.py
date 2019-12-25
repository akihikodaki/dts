# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation.
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
DPDK Test suite.

Test cases for vm2vm virtio-user
This suite include split virtqueue vm2vm in-order mergeable, in-order non-mergeable,
mergeable, non-mergeable, vector_rx path test
and packed virtqueue vm2vm in-order mergeable, in-order non-mergeable,
mergeable, non-mergeable path test
"""
import re
import time
import utils
from test_case import TestCase
from packet import Packet
from pmd_output import PmdOutput


class TestVM2VMVirtioUser(TestCase):
    def set_up_all(self):
        self.memory_channel = self.dut.get_memory_channels()
        self.dump_virtio_pcap = "/tmp/pdump-virtio-rx.pcap"
        self.dump_vhost_pcap = "/tmp/pdump-vhost-rx.pcap"
        self.vhost_prefix = 'vhost'
        self.virtio_prefix = 'virtio'
        socket_num = len(set([int(core['socket']) for core in self.dut.cores]))
        self.socket_mem = ','.join(['1024']*socket_num)
        self.get_core_list()
        self.rebuild_flag = False
        self.config_value = 'CONFIG_RTE_LIBRTE_PMD_PCAP'
        self.enable_pcap_lib_in_dpdk(self.dut)

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("rm -rf %s" % self.dump_virtio_pcap, "#")
        self.dut.send_expect("rm -rf %s" % self.dump_vhost_pcap, "#")

    def get_core_list(self):
        """
        create core mask
        """
        self.core_config = "1S/6C/1T"
        self.cores_list = self.dut.get_core_list(self.core_config)
        self.verify(len(self.cores_list) >= 6, 'There no enough cores to run this suite')
        self.core_list_vhost = self.cores_list[0:2]
        self.core_list_virtio0 = self.cores_list[2:4]
        self.core_list_virtio1 = self.cores_list[4:6]

        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.pdump_session = self.dut.new_session(suite="pdump")
        self.pmd_vhost = PmdOutput(self.dut, self.vhost_user)
        self.pmd_virtio0 = PmdOutput(self.dut, self.virtio_user0)
        self.pmd_virtio1 = PmdOutput(self.dut, self.virtio_user1)

    def enable_pcap_lib_in_dpdk(self, client_dut):
        """
        enable pcap lib in dpdk code and recompile
        """
        out = self.dut.send_command('cat config/common_base', timeout=3)
        pcap = re.search('%s=(\S*)' % self.config_value, out)
        self.verify(pcap is not None, 'The config:%s can not find in common_base' % self.config_value)
        default_value = pcap.group(1)
        if str.lower(default_value) != 'y':
            client_dut.send_expect("sed -i 's/%s=n$/%s=y/' config/common_base" % (
                    self.config_value, self.config_value), '# ')
            client_dut.build_install_dpdk(self.target)
            self.rebuild_flag = True

    def disable_pcap_lib_in_dpdk(self, client_dut):
        """
        reset pcap lib in dpdk and recompile
        """
        if self.rebuild_flag is True:
            client_dut.send_expect("sed -i 's/%s=y$/%s=n/' config/common_base" %
                        (self.config_value, self.config_value), "#")
            client_dut.build_install_dpdk(self.target)

    def launch_vhost_testpmd(self, vdev_num, fixed_prefix=False, fwd_mode='io'):
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_vhost,
                    no_pci=True, prefix=self.vhost_prefix, fixed_prefix=fixed_prefix)
        vdev_params = ''
        for i in range(vdev_num):
            vdev_params += "--vdev 'net_vhost%d,iface=./vhost-net%d,queues=1' " % (i, i)

        self.command_line = self.dut.target + '/app/testpmd %s ' + \
            '--socket-mem %s %s -- -i --nb-cores=1 --no-flush-rx'

        self.command_line = self.command_line % (
                            eal_params, self.socket_mem, vdev_params)
        self.pmd_vhost.execute_cmd(self.command_line, timeout=30)
        self.pmd_vhost.execute_cmd('set fwd %s' % fwd_mode)

    def start_virtio_testpmd_with_vhost_net1(self, path_mode, extern_params=''):
        """
        launch the testpmd as virtio with vhost_net1
        """
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_virtio1,
                no_pci=True, prefix=self.virtio_prefix, fixed_prefix=True)
        vdev_params = '--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,%s ' % path_mode
        command_line = self.dut.target + "/app/testpmd %s " + \
            "--socket-mem %s %s -- -i --nb-cores=1 --txd=256 --rxd=256 %s"
        command_line = command_line % (eal_params, self.socket_mem,
                                    vdev_params, extern_params)
        self.pmd_virtio1.execute_cmd(command_line, timeout=30)
        self.pmd_virtio1.execute_cmd('set fwd rxonly')
        self.pmd_virtio1.execute_cmd('start')

    def start_virtio_testpmd_with_vhost_net0(self, path_mode, extern_params=''):
        """
        launch the testpmd as virtio with vhost_net0
        and start to send 251 small packets with diff burst
        """
        eal_params = self.dut.create_eal_parameters(cores=self.core_list_virtio0,
                no_pci=True, prefix='virtio0')
        vdev_params = '--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=1,%s ' % path_mode
        command_line = self.dut.target + '/app/testpmd %s ' + \
            '--socket-mem %s %s -- -i --nb-cores=1 --txd=256 --rxd=256 %s'
        command_line = command_line % (eal_params, self.socket_mem,
                                vdev_params, extern_params)

        self.pmd_virtio0.execute_cmd(command_line, timeout=30)
        self.pmd_virtio0.execute_cmd('set burst 1')
        self.pmd_virtio0.execute_cmd('start tx_first 27')
        self.pmd_virtio0.execute_cmd('stop')
        self.pmd_virtio0.execute_cmd('set burst 32')
        self.pmd_virtio0.execute_cmd('start tx_first 7')

    def resend_32_large_pkt_from_virtio0(self):
        self.pmd_virtio0.execute_cmd('stop')
        self.pmd_virtio0.execute_cmd('set burst 32')
        self.pmd_virtio0.execute_cmd('set txpkts 2000')
        self.pmd_virtio0.execute_cmd('start tx_first 1')

    def launch_pdump_to_capture_pkt(self, dump_port, file_prefix, filename):
        """
        launch pdump app with dump_port and file_prefix
        the pdump app should start after testpmd started
        if dump the vhost-testpmd, the vhost-testpmd should started before launch pdump
        if dump the virtio-testpmd, the virtio-testpmd should started before launch pdump
        """
        eal_params = self.dut.create_eal_parameters(cores='Default',
                        prefix=file_prefix, fixed_prefix=True)
        command_line = self.target + "/app/dpdk-pdump %s -v -- " + \
                    "--pdump  '%s,queue=*,rx-dev=%s,mbuf-size=8000'"
        self.pdump_session.send_expect(command_line % (eal_params, dump_port, filename), 'Port')

    def get_dump_file_of_virtio_user(self, path_mode, extern_param=''):
        """
        get the dump file of virtio user
        the virtio_user0 always send 251 small pkts + 32 large pkts(8k) to verify
        how many pkts can received by virtio1
        """
        dump_port = 'device_id=net_virtio_user1'
        self.launch_vhost_testpmd(vdev_num=2)
        self.start_virtio_testpmd_with_vhost_net1(path_mode, extern_param)
        self.launch_pdump_to_capture_pkt(dump_port, self.virtio_prefix, self.dump_virtio_pcap)
        # the virtio0 will send 251 small pkts
        self.start_virtio_testpmd_with_vhost_net0(path_mode, extern_param)
        # then send 32 large pkts
        self.pmd_virtio0.execute_cmd('stop')
        self.pmd_virtio0.execute_cmd('set burst 32')
        self.pmd_virtio0.execute_cmd('set txpkts 2000,2000,2000,2000')
        self.pmd_virtio0.execute_cmd('start tx_first 1')
        # packet will fwd after vhost testpmd start
        self.pmd_vhost.execute_cmd('start')

    def get_dump_file_of_vhost_user(self, path_mode, extern_param=''):
        """
        get the dump file of vhost testpmd
        the virtio0 will alway send 251 small pkts + some large pkts(depend on
        diff path_mode send diff pkts num) to verify how many pkts can received by vhost
        """
        dump_port = 'port=0'
        self.launch_vhost_testpmd(vdev_num=1, fixed_prefix=True, fwd_mode='rxonly')
        self.pmd_vhost.execute_cmd('start')
        self.launch_pdump_to_capture_pkt(dump_port, self.vhost_prefix, self.dump_vhost_pcap)
        # the virtio0 send 251 small pkts
        self.start_virtio_testpmd_with_vhost_net0(path_mode, extern_param)
        # if the path_mode is mergeable, then send large pkt to verify
        # and packed mergeable and split mergeable is diff about large pkt
        # in packed mergeable, 1 large pkt will occupies 5 ring, so send 1 large pkt to verify
        # in split mergeable, 1 large pkt will occupied 1 ring, so send 5 large pkt to verify
        mergeable = re.search('mrg_rxbuf\s*=\s*1', path_mode)
        split = re.search('packed_vq\s*=\s*0', path_mode)
        no_inorder = re.search('in_order\s*=\s*0', path_mode)
        pkt_num = 1
        if split and mergeable and no_inorder:
            pkt_num = 5
        if mergeable:
            self.pmd_virtio0.execute_cmd('stop')
            self.pmd_virtio0.execute_cmd('set burst %d' % pkt_num)
            self.pmd_virtio0.execute_cmd('set txpkts 2000,2000,2000,2000')
            self.pmd_virtio0.execute_cmd('start tx_first 1')

    def check_packet_payload_valid(self, filename, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num):
        """
        check the payload is valid
        """
        # stop pdump
        total_pkts_num = small_pkts_num + large_8k_pkts_num + large_2k_pkts_num
        time.sleep(2)
        self.pdump_session.send_expect('^c', '# ', 60)
        # quit testpmd
        self.quit_all_testpmd()
        time.sleep(2)
        self.dut.session.copy_file_from(src="%s" % filename, dst="%s" % filename)
        pkt = Packet()
        pkts = pkt.read_pcapfile(filename)
        self.verify(pkts is not None and len(pkts) == total_pkts_num,
                        "The virtio/vhost do not capture all the packets"
                        "expect pkt num is: %d, actual pkt num is: %d" % (total_pkts_num, len(pkts)))
        for i in range(len(pkts)):
            if i < small_pkts_num:
                pkt_len = 64
            elif i >= small_pkts_num and i < small_pkts_num+large_8k_pkts_num:
                pkt_len = 8000
            else:
                pkt_len = 2000
            self.verify(len(pkts[i]) == pkt_len, 'the received pkts len is wrong,'
                    'the received pkt len is: %d, expect pkt len is: %d' % (len(pkts[i]), pkt_len))

    def check_vhost_and_virtio_pkts_content(self):
        """
        vhost received pkts in self.dump_vhost_pcap, virtio received pkts self.dump_virtio_pcap
        check headers and payload of all pkts are same.
        """
        pk_rx_virtio = Packet()
        pk_rx_vhost = Packet()
        pk_rx_virtio.read_pcapfile(self.dump_virtio_pcap)
        pk_rx_vhost.read_pcapfile(self.dump_vhost_pcap)
        # check the headers and payload is same of vhost and virtio
        for i in range(len(pk_rx_virtio)):
            self.verify(pk_rx_virtio[i].haslayer('Raw'), 'The pkt index %d, virtio pkt has no layer Raw' % i)
            self.verify(pk_rx_vhost[i].haslayer('Raw'), 'The pkt index %d, vhost pkt has no layer Raw' % i)
            self.verify(pk_rx_virtio[i].haslayer('UDP'), 'The pkt index %d, virtio pkt has no layer UDP' % i)
            self.verify(pk_rx_vhost[i].haslayer('UDP'), 'The pkt index %d, vhost pkt has no layer UDP' % i)
            rx_virtio_load = pk_rx_virtio[i]['Raw'].load
            rx_vhost_load = pk_rx_vhost[i]['Raw'].load
            rx_virtio_head = pk_rx_virtio[i]['UDP'].remove_payload()
            rx_vhost_head = pk_rx_vhost[i]['UDP'].remove_payload()
            # check header is same
            self.verify(pk_rx_virtio[i] == pk_rx_vhost[i], 'the head is different on index: %d' % i + \
                    'virtio head: %s, vhost head: %s' % (pk_rx_virtio[i].show, pk_rx_vhost[i].show()))
            # check payload is same
            self.verify(len(rx_virtio_load) == len(rx_vhost_load),
                    'the len is diff between virtio pcap and vhost pcap,'
                    'virtio len:%d, vhost len: %d' % (len(rx_virtio_load), len(rx_vhost_load)))
            diff_list = [s for s in range(len(rx_virtio_load)) if rx_virtio_load[s] != rx_vhost_load[s]]
            self.verify(len(diff_list) == 0, 'there have some diff between the load of virtio and vhost pcap' + \
                'pkt index is: %d, the load index include %s' % (i, diff_list))

    def quit_all_testpmd(self):
        self.pmd_vhost.quit()
        self.pmd_virtio0.quit()
        self.pmd_virtio1.quit()
        self.pdump_session.send_expect('^c', '# ', 60)

    def test_vm2vm_virtio_user_packed_virtqueue_mergeable_path(self):
        """
        packed virtqueue vm2vm mergeable path test
        about packed virtqueue path, the 8k length pkt will occupies 5 ring,
        2000,2000,2000,2000 will need 4 consequent ring, still need one ring put header
        so, as the rxt=256, if received pkts include 8k chain pkt, it will received up to 252 pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 1
        large_2k_pkts_num = 32
        path_mode = 'packed_vq=1,mrg_rxbuf=1,in_order=0'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 252 pkts
        # then resend 32 large pkts, all will received
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.resend_32_large_pkt_from_virtio0()
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.resend_32_large_pkt_from_virtio0()
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_packed_virtqueue_inorder_mergeable_path(self):
        """
        packed virtqueue vm2vm inorder mergeable path test
        about packed virtqueue path, the 8k length pkt will occupies 5 ring,
        2000,2000,2000,2000 will need 4 consequent ring, still need one ring put header
        so, as the rxt=256, if received pkts include 8k chain pkt, it will received up to 252 pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 1
        large_2k_pkts_num = 0
        path_mode = 'packed_vq=1,mrg_rxbuf=1,in_order=1'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 252 pkts
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_packed_virtqueue_no_mergeable_path(self):
        """
        packed virtqueue vm2vm non-mergeable path test
        about non-mergeable path, it can not received large pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 0
        large_2k_pkts_num = 0
        path_mode = 'packed_vq=1,mrg_rxbuf=0,in_order=0'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 251 pkts
        # the no-mergeable path can not received large pkts
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_packed_virtqueue_inorder_no_mergeable_path(self):
        """
        packed virtqueue vm2vm inorder non-mergeable path test
        about non-mergeable path, it can not received large pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 0
        large_2k_pkts_num = 0
        path_mode = 'packed_vq=1,mrg_rxbuf=0,in_order=1'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 251 pkts
        # the no-mergeable path can not received large pkts
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_split_virtqueue_mergeable_path(self):
        """
        split virtqueue vm2vm mergeable path test
        about split virtqueue path, the 8k length pkt will occupies 1 ring,
        so, as the rxt=256, if received pkts include 8k chain pkt, also will received up to 256 pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 5
        large_2k_pkts_num = 32
        path_mode = 'packed_vq=0,mrg_rxbuf=1,in_order=0'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 256 pkts
        # then virtio send 32 large pkts, the virtio will all received
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.resend_32_large_pkt_from_virtio0()
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.resend_32_large_pkt_from_virtio0()
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_split_virtqueue_inorder_mergeable_path(self):
        """
        split virtqueue vm2vm inorder mergeable path test
        about split virtqueue path, the 8k length pkt will occupies 5 ring,
        2000,2000,2000,2000 will need 4 consequent ring, still need one ring put header
        so, as the rxt=256, if received pkts include 8k chain pkt, it will received up to 252 pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 1
        large_2k_pkts_num = 0
        path_mode = 'packed_vq=0,mrg_rxbuf=1,in_order=1'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 252 pkts
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_split_virtqueue_no_mergeable_path(self):
        """
        split virtqueue vm2vm non-mergeable path test
        about non-mergeable path, it can not received large pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 0
        large_2k_pkts_num = 0
        path_mode = 'packed_vq=0,mrg_rxbuf=0,in_order=0'
        extern_params = '--enable-hw-vlan-strip'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 251 pkts
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode, extern_params)
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode, extern_params)
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_split_virtqueue_inorder_no_mergeable_path(self):
        """
        split virtqueue vm2vm inorder non-mergeable path test
        about non-mergeable path, it can not received large pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 0
        large_2k_pkts_num = 0
        path_mode = 'packed_vq=0,mrg_rxbuf=0,in_order=1'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 251 pkts
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def test_vm2vm_virtio_user_split_virtqueue_vector_rx_path(self):
        """
        split virtqueue vm2vm vector_rx path test
        about vector_rx path, it can not received large pkts
        """
        small_pkts_num = 251
        large_8k_pkts_num = 0
        large_2k_pkts_num = 0
        path_mode = 'packed_vq=0,mrg_rxbuf=0,in_order=0'
        # get dump pcap file of virtio
        # the virtio0 will send 283 pkts, but the virtio only will received 251 pkts
        self.logger.info('check pcap file info about virtio')
        self.get_dump_file_of_virtio_user(path_mode)
        self.check_packet_payload_valid(self.dump_virtio_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        # get dump pcap file of vhost
        self.logger.info('check pcap file info about vhost')
        self.get_dump_file_of_vhost_user(path_mode)
        self.check_packet_payload_valid(self.dump_vhost_pcap, small_pkts_num, large_8k_pkts_num, large_2k_pkts_num)

        self.logger.info('diff the pcap file of vhost and virtio')
        self.check_vhost_and_virtio_pkts_content()

    def close_all_session(self):
        if getattr(self, 'vhost_user', None):
            self.dut.close_session(self.vhost_user)
        if getattr(self, 'virtio-user0', None):
            self.dut.close_session(self.virtio-user0)
        if getattr(self, 'virtio-user1', None):
            self.dut.close_session(self.virtio-user1)
        if getattr(self, 'pdump_session', None):
            self.dut.close_session(self.pdump_session)

    def tear_down(self):
        #
        # Run after each test case.
        #
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.disable_pcap_lib_in_dpdk(self.dut)
        self.close_all_session()

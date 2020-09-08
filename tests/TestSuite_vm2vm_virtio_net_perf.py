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

vm2vm split ring and packed ring with tx offload (TSO and UFO) with non-mergeable path.
vm2vm split ring and packed ring with UFO about virtio-net device capability with non-mergeable path.
vm2vm split ring and packed ring vhost-user/virtio-net check the payload of large packet is valid with
mergeable and non-mergeable dequeue zero copy.
please use qemu version greater 4.1.94 which support packed feathur to test this suite.
"""
import re
import time
import string
import random
from virt_common import VM
from test_case import TestCase
from pmd_output import PmdOutput


class TestVM2VMVirtioNetPerf(TestCase):
    def set_up_all(self):
        core_config = "1S/4C/1T"
        self.cores_list = self.dut.get_core_list(core_config)
        self.verify(len(self.cores_list) >= 4,
                    "There has not enough cores to test this suite %s" %
                    self.suite_name)
        self.vm_num = 2
        self.virtio_ip1 = "1.1.1.2"
        self.virtio_ip2 = "1.1.1.3"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.virtio_mac2 = "52:54:00:00:00:02"
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.random_string = string.ascii_letters + string.digits
        socket_num = len(set([int(core['socket']) for core in self.dut.cores]))
        self.socket_mem = ','.join(['2048']*socket_num)
        self.vhost = self.dut.new_session(suite="vhost")
        self.pmd_vhost = PmdOutput(self.dut, self.vhost)
        self.app_testpmd_path = self.dut.apps_name['test-pmd']

    def set_up(self):
        """
        run before each test case.
        """
        self.table_header = ['Mode', '[M|G]bits/sec']
        self.result_table_create(self.table_header)
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_dut = []
        self.vm = []

    def start_vhost_testpmd(self, zerocopy=False):
        """
        launch the testpmd with different parameters
        """
        if zerocopy is True:
            zerocopy_arg = ",dequeue-zero-copy=1"
        else:
            zerocopy_arg = ""
        testcmd = self.app_testpmd_path + " "
        vdev1 = "--vdev 'net_vhost0,iface=%s/vhost-net0,queues=1%s' " % (self.base_dir, zerocopy_arg)
        vdev2 = "--vdev 'net_vhost1,iface=%s/vhost-net1,queues=1%s' " % (self.base_dir, zerocopy_arg)
        eal_params = self.dut.create_eal_parameters(cores=self.cores_list, prefix='vhost', no_pci=True)
        para = " -- -i --nb-cores=2 --txd=1024 --rxd=1024"
        self.command_line = testcmd + eal_params + vdev1 + vdev2 + para
        self.pmd_vhost.execute_cmd(self.command_line, timeout=30)
        self.pmd_vhost.execute_cmd('start', timeout=30)

    def start_vms(self, mode="mergeable", packed=False):
        """
        start two VM, each VM has one virtio device
        """
        setting_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        if mode == "ufo":
            setting_args += ",guest_ufo=on,host_ufo=on"
        elif mode == "mergeable":
            setting_args = "mrg_rxbuf=on"
        elif mode == "normal":
            setting_args = "mrg_rxbuf=off"
        if packed is True:
            setting_args = "%s,packed=on" % setting_args

        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, 'vm%d' % i, 'vhost_sample')
            vm_params = {}
            vm_params['driver'] = 'vhost-user'
            vm_params['opt_path'] = self.base_dir + '/vhost-net%d' % i
            vm_params['opt_mac'] = "52:54:00:00:00:0%d" % (i+1)
            vm_params['opt_settings'] = setting_args
            vm_info.set_vm_device(**vm_params)
            time.sleep(3)
            try:
                vm_dut = vm_info.start(set_target=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                self.logger.error("Failure for %s" % str(e))
                raise e
            vm_dut.restore_interfaces()

            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def config_vm_env(self):
        """
        set virtio device IP and run arp protocal
        """
        vm1_intf = self.vm_dut[0].ports_info[0]['intf']
        vm2_intf = self.vm_dut[1].ports_info[0]['intf']
        self.vm_dut[0].send_expect("ifconfig %s %s" % (vm1_intf, self.virtio_ip1), "#", 10)
        self.vm_dut[1].send_expect("ifconfig %s %s" % (vm2_intf, self.virtio_ip2), "#", 10)
        self.vm_dut[0].send_expect("arp -s %s %s" % (self.virtio_ip2, self.virtio_mac2), "#", 10)
        self.vm_dut[1].send_expect("arp -s %s %s" % (self.virtio_ip1, self.virtio_mac1), "#", 10)

    def prepare_test_env(self, zerocopy, path_mode, packed_mode=False):
        """
        start vhost testpmd and qemu, and config the vm env
        """
        self.start_vhost_testpmd(zerocopy)
        self.start_vms(mode=path_mode, packed=packed_mode)
        self.config_vm_env()

    def start_iperf(self, mode):
        """
        run perf command between to vms
        """
        # clear the port xstats before iperf
        self.vhost.send_expect("clear port xstats all", "testpmd> ", 10)

        if mode == "ufo":
            iperf_server = "iperf -s -u -i 1"
            iperf_client = "iperf -c 1.1.1.2 -i 1 -t 30 -P 4 -u -b 1G -l 9000"
        else:
            iperf_server = "iperf -s -i 1"
            iperf_client = "iperf -c 1.1.1.2 -i 1 -t 30"
        self.vm_dut[0].send_expect("%s > iperf_server.log &" % iperf_server, "", 10)
        self.vm_dut[1].send_expect("%s > iperf_client.log &" % iperf_client, "", 60)
        time.sleep(90)

    def get_perf_result(self):
        """
        get the iperf test result
        """
        self.vm_dut[0].send_expect('pkill iperf', '# ')
        self.vm_dut[1].session.copy_file_from("%s/iperf_client.log" % self.dut.base_dir)
        fp = open("./iperf_client.log")
        fmsg = fp.read()
        fp.close()
        # remove the server report info from msg
        index = fmsg.find("Server Report")
        if index != -1:
            fmsg = fmsg[:index]
        iperfdata = re.compile('\S*\s*[M|G]bits/sec').findall(fmsg)
        # the last data of iperf is the ave data from 0-30 sec
        self.verify(len(iperfdata) != 0, "The iperf data between to vms is 0")
        self.logger.info("The iperf data between vms is %s" % iperfdata[-1])

        # put the result to table
        results_row = ["vm2vm", iperfdata[-1]]
        self.result_table_add(results_row)

        # rm the iperf log file in vm
        self.vm_dut[0].send_expect('rm iperf_server.log', '#', 10)
        self.vm_dut[1].send_expect('rm iperf_client.log', '#', 10)

    def verify_xstats_info_on_vhost(self):
        """
        check both 2VMs can receive and send big packets to each other
        """
        out_tx = self.vhost.send_expect("show port xstats 0", "testpmd> ", 20)
        out_rx = self.vhost.send_expect("show port xstats 1", "testpmd> ", 20)

        rx_info = re.search("rx_size_1523_to_max_packets:\s*(\d*)", out_rx)
        tx_info = re.search("tx_size_1523_to_max_packets:\s*(\d*)", out_tx)

        self.verify(int(rx_info.group(1)) > 0,
                    "Port 1 not receive packet greater than 1522")
        self.verify(int(tx_info.group(1)) > 0,
                    "Port 0 not forward packet greater than 1522")

    def start_iperf_and_verify_vhost_xstats_info(self, mode):
        """
        start to send packets and verify vm can received data of iperf
        and verify the vhost can received big pkts in testpmd
        """
        self.start_iperf(mode)
        self.get_perf_result()
        self.verify_xstats_info_on_vhost()
        self.result_table_print()

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.pmd_vhost.quit()

    def offload_capbility_check(self, vm_client):
        """
        check UFO and TSO offload status on for the Virtio-net driver in VM
        """
        vm_intf = vm_client.ports_info[0]['intf']
        vm_client.send_expect('ethtool -k %s > offload.log' % vm_intf, '#', 10)
        fmsg = vm_client.send_expect("cat ./offload.log", "#")
        udp_info = re.search("udp-fragmentation-offload:\s*(\S*)", fmsg)
        tcp_info = re.search("tx-tcp-segmentation:\s*(\S*)", fmsg)
        tcp_enc_info = re.search("tx-tcp-ecn-segmentation:\s*(\S*)", fmsg)
        tcp6_info = re.search("tx-tcp6-segmentation:\s*(\S*)", fmsg)

        self.verify(udp_info is not None and udp_info.group(1) == "on",
                    "the udp-fragmentation-offload in vm not right")
        self.verify(tcp_info is not None and tcp_info.group(1) == "on",
                    "tx-tcp-segmentation in vm not right")
        self.verify(tcp_enc_info is not None and tcp_enc_info.group(1) == "on",
                    "tx-tcp-ecn-segmentation in vm not right")
        self.verify(tcp6_info is not None and tcp6_info.group(1) == "on",
                    "tx-tcp6-segmentation in vm not right")

    def check_scp_file_valid_between_vms(self):
        """
        scp 64b and 64KB file form VM1 to VM2, check the data is valid
        """
        # create a 64b and 64K size file
        data = ''
        for b_size in [64, 65535]:
            for char in range(b_size):
                data += random.choice(self.random_string)
            self.vm_dut[0].send_expect('echo "%s" > /tmp/payload' % data, '# ')
            # scp this file to vm1
            out = self.vm_dut[1].send_command('scp root@%s:/tmp/payload /root' % self.virtio_ip1, timeout=5)
            if 'Are you sure you want to continue connecting' in out:
                self.vm_dut[1].send_command('yes', timeout=3)
            self.vm_dut[1].send_command(self.vm[0].password, timeout=3)
            # get the file info in vm1, and check it valid
            md5_send = self.vm_dut[0].send_expect('md5sum /tmp/payload', '# ')
            md5_revd = self.vm_dut[1].send_expect('md5sum /root/payload', '# ')
            md5_send = md5_send[: md5_send.find(' ')]
            md5_revd = md5_revd[: md5_revd.find(' ')]
            self.verify(md5_send == md5_revd, 'the received file is different with send file')

    def test_vm2vm_split_ring_iperf_with_tso(self):
        """
        VM2VM split ring vhost-user/virtio-net test with tcp traffic
        """
        zerocopy = False
        path_mode = "tso"
        self.prepare_test_env(zerocopy, path_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")

    def test_vm2vm_split_ring_dequeue_zero_copy_with_tso(self):
        """
        VM2VM split ring vhost-user/virtio-net zero copy test with tcp traffic
        """
        zerocopy = True
        path_mode = "tso"
        self.prepare_test_env(zerocopy, path_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")

    def test_vm2vm_packed_ring_iperf_with_tso(self):
        """
        VM2VM packed ring vhost-user/virtio-net test with tcp traffic
        """
        zerocopy = False
        path_mode = "tso"
        packed_mode = True
        self.prepare_test_env(zerocopy, path_mode, packed_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")

    def test_vm2vm_packed_ring_dequeue_zero_copy_with_tso(self):
        """
        VM2VM packed ring vhost-user/virtio-net zero copy test with tcp traffic
        """
        zerocopy = True
        path_mode = "tso"
        packed_mode = True
        self.prepare_test_env(zerocopy, path_mode, packed_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="tso")

    def test_vm2vm_split_ring_iperf_with_ufo(self):
        """
        VM2VM split ring vhost-user/virtio-net test with udp traffic
        """
        zerocopy = False
        path_mode = "ufo"
        self.prepare_test_env(zerocopy, path_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="ufo")

    def test_vm2vm_packed_ring_iperf_with_ufo(self):
        """
        VM2VM packed ring vhost-user/virtio-net test with udp traffic
        """
        zerocopy = False
        path_mode = "ufo"
        packed_mode = True
        self.prepare_test_env(zerocopy, path_mode, packed_mode)
        self.start_iperf_and_verify_vhost_xstats_info(mode="ufo")

    def test_vm2vm_split_ring_device_capbility(self):
        """
        Check split ring virtio-net device capability
        """
        self.start_vhost_testpmd(zerocopy=False)
        self.start_vms(mode="ufo")
        self.offload_capbility_check(self.vm_dut[0])
        self.offload_capbility_check(self.vm_dut[1])

    def test_vm2vm_packed_ring_device_capbility(self):
        """
        Check split ring virtio-net device capability
        """
        self.start_vhost_testpmd(zerocopy=False)
        self.start_vms(mode="ufo", packed=True)
        self.offload_capbility_check(self.vm_dut[0])
        self.offload_capbility_check(self.vm_dut[1])

    def test_vm2vm_split_ring_zero_copy_with_mergeable_path_check_large_packet(self):
        """
        VM2VM virtio-net split ring mergeable zero copy test with large packet payload valid check
        """
        zerocopy = True
        path_mode = 'mergeable'
        self.prepare_test_env(zerocopy, path_mode)
        self.check_scp_file_valid_between_vms()

    def test_vm2vm_split_ring_zero_copy_with_no_mergeable_path_check_large_packet(self):
        """
        VM2VM virtio-net split ring non-mergeable zero copy test with large packet payload valid check
        """
        zerocopy = True
        path_mode = 'normal'
        self.prepare_test_env(zerocopy, path_mode)
        self.check_scp_file_valid_between_vms()

    def test_vm2vm_packed_ring_zero_copy_with_mergeable_path_check_large_packet(self):
        """
        VM2VM packed ring virtio-net mergeable dequeue zero copy test with large packet payload valid check
        """
        zerocopy = True
        path_mode = 'mergeable'
        packed_mode = True
        self.prepare_test_env(zerocopy, path_mode, packed_mode)
        self.check_scp_file_valid_between_vms()

    def test_vm2vm_packed_ring_zero_copy_with_no_mergeable_path_check_large_packet(self):
        """
        VM2VM packed ring virtio-net non-mergeable dequeue zero copy test with large packet payload valid check
        """
        zerocopy = True
        path_mode = 'normal'
        packed_mode = True
        self.prepare_test_env(zerocopy, path_mode, packed_mode)
        self.check_scp_file_valid_between_vms()

    def tear_down(self):
        """
        run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if getattr(self, 'vhost', None):
            self.dut.close_session(self.vhost)

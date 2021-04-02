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
import utils
from virt_common import VM
from test_case import TestCase
from pmd_output import PmdOutput


class TestVM2VMVirtioNetPerf(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        core_config = "1S/5C/1T"
        self.cores_list = self.dut.get_core_list(core_config, socket=self.ports_socket)
        self.verify(len(self.cores_list) >= 4, "There has not enough cores to test this suite %s" % self.suite_name)
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
        # get cbdma device
        self.cbdma_dev_infos = []
        self.dmas_info = None
        self.device_str = None
        self.checked_vm = False
        self.dut.restore_interfaces()

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vm_dut = []
        self.vm = []

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num=2, allow_diff_socket=False):
        """
        get all cbdma ports
        """
        # check driver name in execution.cfg
        self.verify(self.drivername == 'igb_uio',
                    "CBDMA test case only use igb_uio driver, need config drivername=igb_uio in execution.cfg")
        str_info = 'Misc (rawdev) devices using kernel driver'
        out = self.dut.send_expect('./usertools/dpdk-devbind.py --status-dev misc', '# ', 30)
        device_info = out.split('\n')
        for device in device_info:
            pci_info = re.search('\s*(0000:\d*:\d*.\d*)', device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if allow_diff_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
                else:
                    if self.ports_socket == cur_socket:
                        self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(len(self.cbdma_dev_infos) >= cbdma_num, 'There no enough cbdma device to run this suite')
        used_cbdma = self.cbdma_dev_infos[0:cbdma_num]
        dmas_info = ''
        for dmas in used_cbdma[0:int(cbdma_num/2)]:
            number = used_cbdma[0:int(cbdma_num/2)].index(dmas)
            dmas = 'txq{}@{},'.format(number, dmas.replace('0000:', ''))
            dmas_info += dmas
        for dmas in used_cbdma[int(cbdma_num/2):]:
            number = used_cbdma[int(cbdma_num/2):].index(dmas)
            dmas = 'txq{}@{},'.format(number, dmas.replace('0000:', ''))
            dmas_info += dmas
        self.dmas_info = dmas_info[:-1]
        self.device_str = ' '.join(used_cbdma)
        self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=%s %s' % (self.drivername, self.device_str), '# ', 60)

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect('modprobe ioatdma', '# ')
            self.dut.send_expect('./usertools/dpdk-devbind.py -u %s' % self.device_str, '# ', 30)
            self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=ioatdma  %s' % self.device_str, '# ', 60)

    def start_vhost_testpmd(self, cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=2, rxq_txq=None):
        """
        launch the testpmd with different parameters
        """
        if cbdma is True:
            dmas_info_list = self.dmas_info.split(',')
            cbdma_arg_0_list = []
            cbdma_arg_1_list = []
            for item in dmas_info_list:
                if dmas_info_list.index(item) < int(len(dmas_info_list) / 2):
                    cbdma_arg_0_list.append(item)
                else:
                    cbdma_arg_1_list.append(item)
            cbdma_arg_0 = ",dmas=[{}],dmathr=512".format(";".join(cbdma_arg_0_list))
            cbdma_arg_1 = ",dmas=[{}],dmathr=512".format(";".join(cbdma_arg_1_list))
        else:
            cbdma_arg_0 = ""
            cbdma_arg_1 = ""
        testcmd = self.app_testpmd_path + " "
        if not client_mode:
            vdev1 = "--vdev 'net_vhost0,iface=%s/vhost-net0,queues=%d%s' " % (self.base_dir, enable_queues, cbdma_arg_0)
            vdev2 = "--vdev 'net_vhost1,iface=%s/vhost-net1,queues=%d%s' " % (self.base_dir, enable_queues, cbdma_arg_1)
        else:
            vdev1 = "--vdev 'net_vhost0,iface=%s/vhost-net0,client=1,queues=%d%s' " % (self.base_dir, enable_queues, cbdma_arg_0)
            vdev2 = "--vdev 'net_vhost1,iface=%s/vhost-net1,client=1,queues=%d%s' " % (self.base_dir, enable_queues, cbdma_arg_1)
        eal_params = self.dut.create_eal_parameters(cores=self.cores_list, prefix='vhost', no_pci=no_pci)
        if rxq_txq is None:
            params = " -- -i --nb-cores=%d --txd=1024 --rxd=1024" % nb_cores
        else:
            params = " -- -i --nb-cores=%d --txd=1024 --rxd=1024 --rxq=%d --txq=%d" % (nb_cores, rxq_txq, rxq_txq)
        self.command_line = testcmd + eal_params + vdev1 + vdev2 + params
        self.pmd_vhost.execute_cmd(self.command_line, timeout=30)
        self.pmd_vhost.execute_cmd('vhost enable tx all', timeout=30)
        self.pmd_vhost.execute_cmd('start', timeout=30)

    def start_vms(self, server_mode=False, opt_queue=None, vm_config='vhost_sample'):
        """
        start two VM, each VM has one virtio device
        """
        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, 'vm%d' % i, vm_config)
            vm_params = {}
            vm_params['driver'] = 'vhost-user'
            if not server_mode:
                vm_params['opt_path'] = self.base_dir + '/vhost-net%d' % i
            else:
                vm_params['opt_path'] = self.base_dir + '/vhost-net%d' % i + ',server'
            if opt_queue is not None:
                vm_params['opt_queue'] = opt_queue
            vm_params['opt_mac'] = "52:54:00:00:00:0%d" % (i+1)
            vm_params['opt_settings'] = self.vm_args
            vm_info.set_vm_device(**vm_params)
            try:
                vm_dut = vm_info.start(set_target=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print(utils.RED("Failure for %s" % str(e)))
            self.verify(vm_dut is not None, "start vm failed")
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def config_vm_env(self, combined=False, rxq_txq=1):
        """
        set virtio device IP and run arp protocal
        """
        vm1_intf = self.vm_dut[0].ports_info[0]['intf']
        vm2_intf = self.vm_dut[1].ports_info[0]['intf']
        if combined:
            self.vm_dut[0].send_expect("ethtool -L %s combined %d" % (vm1_intf, rxq_txq), "#", 10)
        self.vm_dut[0].send_expect("ifconfig %s %s" % (vm1_intf, self.virtio_ip1), "#", 10)
        if combined:
            self.vm_dut[1].send_expect("ethtool -L %s combined %d" % (vm2_intf, rxq_txq), "#", 10)
        self.vm_dut[1].send_expect("ifconfig %s %s" % (vm2_intf, self.virtio_ip2), "#", 10)
        self.vm_dut[0].send_expect("arp -s %s %s" % (self.virtio_ip2, self.virtio_mac2), "#", 10)
        self.vm_dut[1].send_expect("arp -s %s %s" % (self.virtio_ip1, self.virtio_mac1), "#", 10)

    def prepare_test_env(self, cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=2,
                         server_mode=False, opt_queue=None, combined=False, rxq_txq=None, vm_config='vhost_sample'):
        """
        start vhost testpmd and qemu, and config the vm env
        """
        self.start_vhost_testpmd(cbdma=cbdma, no_pci=no_pci, client_mode=client_mode, enable_queues=enable_queues,
                                 nb_cores=nb_cores, rxq_txq=rxq_txq)
        self.start_vms(server_mode=server_mode, opt_queue=opt_queue, vm_config=vm_config)
        self.config_vm_env(combined=combined, rxq_txq=rxq_txq)

    def start_iperf(self, iperf_mode='tso'):
        """
        run perf command between to vms
        """
        # clear the port xstats before iperf
        self.vhost.send_expect("clear port xstats all", "testpmd> ", 10)

        # add -f g param, use Gbits/sec report teste result
        if iperf_mode == "tso":
            iperf_server = "iperf -f g -s -i 1"
            iperf_client = "iperf -f g -c 1.1.1.2 -i 1 -t 60"
        else:
            iperf_server = "iperf -f g -s -u -i 1"
            iperf_client = "iperf -f g -c 1.1.1.2 -i 1 -t 30 -P 4 -u -b 1G -l 9000"
        self.vm_dut[0].send_expect("%s > iperf_server.log &" % iperf_server, "", 10)
        self.vm_dut[1].send_expect("%s > iperf_client.log &" % iperf_client, "", 60)
        time.sleep(90)

    def get_perf_result(self):
        """
        get the iperf test result
        """
        self.table_header = ['Mode', '[M|G]bits/sec']
        self.result_table_create(self.table_header)
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

        # print iperf resut
        self.result_table_print()
        # rm the iperf log file in vm
        self.vm_dut[0].send_expect('rm iperf_server.log', '#', 10)
        self.vm_dut[1].send_expect('rm iperf_client.log', '#', 10)
        return float(iperfdata[-1].split()[0])

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

    def start_iperf_and_verify_vhost_xstats_info(self, iperf_mode='tso'):
        """
        start to send packets and verify vm can received data of iperf
        and verify the vhost can received big pkts in testpmd
        """
        self.start_iperf(iperf_mode)
        iperfdata = self.get_perf_result()
        self.verify_xstats_info_on_vhost()
        return iperfdata

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

    def check_scp_file_valid_between_vms(self, file_size=1):
        """
        scp file form VM1 to VM2, check the data is valid
        """
        # default file_size=1K
        data = ''
        for char in range(file_size * 1024):
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

    def bind_nic_driver(self, ports, driver=""):
        if driver == "igb_uio":
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver = netdev.get_nic_driver()
                if driver != 'igb_uio':
                    netdev.bind_driver(driver='igb_uio')
        else:
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver_now = netdev.get_nic_driver()
                if driver == "":
                    driver = netdev.default_driver
                if driver != driver_now:
                    netdev.bind_driver(driver=driver)

    def test_vm2vm_split_ring_iperf_with_tso(self):
        """
        TestCase1: VM2VM split ring vhost-user/virtio-net test with tcp traffic
        """
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        self.prepare_test_env(cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=2,
                              server_mode=False, opt_queue=1, combined=False, rxq_txq=None)
        self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')

    def test_vm2vm_split_ring_with_tso_and_cbdma_enable(self):
        """
        TestCase2: VM2VM split ring vhost-user/virtio-net CBDMA enable test with tcp traffic
        """
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
        self.prepare_test_env(cbdma=True, no_pci=False, client_mode=False, enable_queues=1, nb_cores=2,
                              server_mode=False, opt_queue=1, combined=False, rxq_txq=None)
        cbdma_value = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        expect_value = self.get_suite_cfg()['expected_throughput'][self.running_case]
        self.verify(cbdma_value > expect_value, "CBDMA enable performance: %s is lower than CBDMA disable: %s." %(cbdma_value, expect_value))

    def test_vm2vm_split_ring_iperf_with_ufo(self):
        """
        TestCase3: VM2VM split ring vhost-user/virtio-net test with udp traffic
        """
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.prepare_test_env(cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=1,
                              server_mode=False, opt_queue=1, combined=False, rxq_txq=None)
        self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='ufo')

    def test_vm2vm_split_ring_device_capbility(self):
        """
        TestCase4: Check split ring virtio-net device capability
        """
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.start_vhost_testpmd(cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=2, rxq_txq=None)
        self.start_vms()
        self.offload_capbility_check(self.vm_dut[0])
        self.offload_capbility_check(self.vm_dut[1])

    def test_vm2vm_split_ring_mergeable_path_check_large_packet_and_cbdma_enable_8queue(self):
        """
        TestCase5: VM2VM virtio-net split ring mergeable CBDMA enable test with large packet payload valid check
        """
        # This test case need to use QEMU 3.0 to test
        ipef_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)

        self.logger.info("Launch vhost-testpmd with CBDMA and used 8 queue")
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.prepare_test_env(cbdma=True, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4,
                              server_mode=True, opt_queue=8, combined=True, rxq_txq=8, vm_config='vm')
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_enable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Enable', 'mergeable path', 8, iperf_data_cbdma_enable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 8 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=8)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable','mergeable path', 8, iperf_data_cbdma_disable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 1 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=1)
        self.config_vm_env(combined=True, rxq_txq=1)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_1_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable', 'mergeable path', 1, iperf_data_cbdma_disable_1_queue])

        self.table_header = ['CBDMA Enable/Disable', 'Mode', 'rxq/txq', 'Gbits/sec']
        self.result_table_create(self.table_header)
        for table_row in ipef_result:
            self.result_table_add(table_row)
        self.result_table_print()
        self.verify(iperf_data_cbdma_enable_8_queue > iperf_data_cbdma_disable_8_queue, \
                    "CMDMA enable: %s is lower than CBDMA disable: %s" % (
                        iperf_data_cbdma_enable_8_queue, iperf_data_cbdma_disable_8_queue))

    def test_vm2vm_split_ring_no_mergeable_path_check_large_packet_and_cbdma_enable_8queue(self):
        """
        TestCase6: VM2VM virtio-net split ring non-mergeable CBDMA enable test with large packet payload valid check
        """
        # This test case need to use QEMU 3.0 to test
        ipef_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)

        self.logger.info("Launch vhost-testpmd with CBDMA and used 8 queue")
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on"
        self.prepare_test_env(cbdma=True, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4,
                              server_mode=True, opt_queue=8, combined=True, rxq_txq=8, vm_config='vm')
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_enable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Enable', 'no-mergeable path', 8, iperf_data_cbdma_enable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 8 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=8)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable','no-mergeable path', 8, iperf_data_cbdma_disable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 1 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=1)
        self.config_vm_env(combined=True, rxq_txq=1)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_1_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable','no-mergeable path', 1, iperf_data_cbdma_disable_1_queue])

        self.table_header = ['CBDMA Enable/Disable', 'Mode', 'rxq/txq', 'Gbits/sec']
        self.result_table_create(self.table_header)
        for table_row in ipef_result:
            self.result_table_add(table_row)
        self.result_table_print()
        self.verify(iperf_data_cbdma_enable_8_queue > iperf_data_cbdma_disable_8_queue, \
                    "CMDMA enable: %s is lower than CBDMA disable: %s" % (
                        iperf_data_cbdma_enable_8_queue, iperf_data_cbdma_disable_8_queue))

    def test_vm2vm_packed_ring_iperf_with_tso(self):
        """
        TestCase7: VM2VM packed ring vhost-user/virtio-net test with tcp traffic
        """
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.prepare_test_env(cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=2,
                              server_mode=False, opt_queue=1, combined=False, rxq_txq=None)
        self.start_iperf_and_verify_vhost_xstats_info()

    def test_vm2vm_packed_ring_iperf_with_tso_and_cbdma_enable(self):
        """
        TestCase8: VM2VM packed ring vhost-user/virtio-net CBDMA enable test with tcp traffic
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.prepare_test_env(cbdma=True, no_pci=False, client_mode=False, enable_queues=1, nb_cores=2,
                              server_mode=False, opt_queue=None, combined=False, rxq_txq=None)
        self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='other')

    def test_vm2vm_packed_ring_device_capbility(self):
        """
        TestCase9: Check packed ring virtio-net device capability
        """
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on"
        self.prepare_test_env(cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=2,
                              server_mode=False, opt_queue=None, combined=False, rxq_txq=None)
        self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='ufo')

    def test_vm2vm_packed_ring_mergeable_path_check_large_packet(self):
        """
        TestCase10: VM2VM packed ring virtio-net mergeable with large packet payload valid check
        """
        self.vm_args = "disable-modern=false,mrg_rxbuf=on,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.start_vhost_testpmd(cbdma=False, no_pci=True, client_mode=False, enable_queues=1, nb_cores=2, rxq_txq=None)
        self.start_vms()
        self.offload_capbility_check(self.vm_dut[0])
        self.offload_capbility_check(self.vm_dut[1])

    def test_vm2vm_packed_ring_mergeable_path_check_large_packet_and_cbdma_enable_8queue(self):
        """
        Test Case 11: VM2VM virtio-net packed ring mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        # This test case need to use QEMU 3.0 to test
        ipef_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)

        self.logger.info("Launch vhost-testpmd with CBDMA and used 8 queue")
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.prepare_test_env(cbdma=True, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4,
                              server_mode=True, opt_queue=8, combined=True, rxq_txq=8, vm_config='vm')
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_enable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Enable', 'mergeable path', 8, iperf_data_cbdma_enable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 8 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=8)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable', 'mergeable path', 8, iperf_data_cbdma_disable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 1 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=1)
        self.config_vm_env(combined=True, rxq_txq=1)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_1_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable', 'mergeable path', 1, iperf_data_cbdma_disable_1_queue])

        self.table_header = ['CBDMA Enable/Disable', 'Mode', 'rxq/txq', 'Gbits/sec']
        self.result_table_create(self.table_header)
        for table_row in ipef_result:
            self.result_table_add(table_row)
        self.result_table_print()
        self.verify(iperf_data_cbdma_enable_8_queue > iperf_data_cbdma_disable_8_queue, \
                    "CMDMA enable: %s is lower than CBDMA disable: %s" % (
                        iperf_data_cbdma_enable_8_queue, iperf_data_cbdma_disable_8_queue))

    def test_vm2vm_packed_ring_no_mergeable_path_check_large_packet_and_cbdma_enable_8queue(self):
        """
        Test Case 12: VM2VM virtio-net packed ring non-mergeable 8 queues CBDMA enable test with large packet payload valid check
        """
        # This test case need to use QEMU 3.0 to test
        ipef_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=16, allow_diff_socket=True)

        self.logger.info("Launch vhost-testpmd with CBDMA and used 8 queue")
        self.vm_args = "disable-modern=false,mrg_rxbuf=off,mq=on,vectors=40,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,guest_ufo=on,host_ufo=on,packed=on"
        self.prepare_test_env(cbdma=True, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4,
                              server_mode=True, opt_queue=8, combined=True, rxq_txq=8, vm_config='vm')
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_enable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Enable', 'mergeable path', 8, iperf_data_cbdma_enable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 8 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=8)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_8_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable', 'mergeable path', 8, iperf_data_cbdma_disable_8_queue])

        self.logger.info("Re-launch without CBDMA and used 1 queue")
        self.vhost.send_expect("quit", "# ", 30)
        self.start_vhost_testpmd(cbdma=False, no_pci=False, client_mode=True, enable_queues=8, nb_cores=4, rxq_txq=1)
        self.config_vm_env(combined=True, rxq_txq=1)
        self.check_scp_file_valid_between_vms()
        iperf_data_cbdma_disable_1_queue = self.start_iperf_and_verify_vhost_xstats_info(iperf_mode='tso')
        ipef_result.append(['Disable', 'mergeable path', 1, iperf_data_cbdma_disable_1_queue])

        self.table_header = ['CBDMA Enable/Disable', 'Mode', 'rxq/txq', 'Gbits/sec']
        self.result_table_create(self.table_header)
        for table_row in ipef_result:
            self.result_table_add(table_row)
        self.result_table_print()
        self.verify(iperf_data_cbdma_enable_8_queue > iperf_data_cbdma_disable_8_queue, \
                    "CMDMA enable: %s is lower than CBDMA disable: %s" % (
                        iperf_data_cbdma_enable_8_queue, iperf_data_cbdma_disable_8_queue))

    def tear_down(self):
        """
        run after each test case.
        """
        self.stop_all_apps()
        self.dut.kill_all()
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.bind_nic_driver(self.dut_ports, self.drivername)
        if getattr(self, 'vhost', None):
            self.dut.close_session(self.vhost)

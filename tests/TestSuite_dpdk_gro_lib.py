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

dpdk gro lib test suite.
In this suite, in order to check the performance of gso lib, will use one
hostcpu to start qemu and only have one vcpu
"""
import re
import time

import framework.utils as utils
import tests.vhost_peer_conf as peer
from framework.test_case import TestCase
from framework.virt_common import VM


class TestDPDKGROLib(TestCase):

    def set_up_all(self):
        # This suite will not use the port config in ports.cfg
        # it will use the port config in vhost_peer_conf.cfg
        # And it need two interface reconnet in DUT

        # unbind the port which config in ports.cfg
        self.dut_ports = self.dut.get_ports()
        self.def_driver = self.dut.ports_info[self.dut_ports[0]]['port'].get_nic_driver()
        for i in self.dut_ports:
            port = self.dut.ports_info[i]['port']
            port.bind_driver()
        # get and bind the port in config file
        self.pci = peer.get_pci_info()
        self.pci_drv = peer.get_pci_driver_info()
        self.peer_pci = peer.get_pci_peer_info()
        self.nic_in_kernel = peer.get_pci_peer_intf_info()
        self.verify(len(self.pci) != 0 and len(self.pci_drv) != 0
                    and len(self.peer_pci) != 0
                    and len(self.nic_in_kernel) != 0,
                    'Pls config the direct connection info in vhost_peer_conf.cfg')
        bind_script_path = self.dut.get_dpdk_bind_script()
        self.dut.send_expect('%s --bind=%s %s' % (bind_script_path, self.def_driver, self.pci), '# ')
        self.path=self.dut.apps_name['test-pmd']
        self.testpmd_name=self.path.split("/")[-1]

        # get the numa info about the pci info which config in peer cfg
        bus = int(self.pci[5:7], base=16)
        if bus >= 128:
            self.socket = 1
        else:
            self.socket = 0
        # get core list on this socket, 2 cores for testpmd, 1 core for qemu
        cores_config = '1S/3C/1T'
        self.verify(self.dut.number_of_cores >= 3, "There has not enought cores to test this case %s" % self.suite_name)
        cores_list = self.dut.get_core_list("1S/3C/1T", socket=self.socket)
        self.vhost_list = cores_list[0:2]
        self.qemu_cpupin = cores_list[2:3][0]

        # Set the params for VM
        self.virtio_ip1 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.memory_channel = self.dut.get_memory_channels()
        if len(set([int(core['socket']) for core in self.dut.cores])) == 1:
            self.socket_mem = '1024'
        else:
            self.socket_mem = '1024,1024'
        self.prepare_dpdk()
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # get cbdma device
        self.cbdma_dev_infos = []
        self.dmas_info = None
        self.device_str = None

    def set_up(self):
        #
        # Run before each test case.
        #
        # Clean the execution ENV
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num):
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
                # the numa id of ioat dev, only add the device which
                # on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if self.ports_socket == cur_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(len(self.cbdma_dev_infos) >= cbdma_num, 'There no enough cbdma device to run this suite')
        used_cbdma = self.cbdma_dev_infos[0:cbdma_num]
        dmas_info = ''
        for dmas in used_cbdma:
            number = used_cbdma.index(dmas)
            dmas = 'txq{}@{};'.format(number, dmas)
            dmas_info += dmas
        self.dmas_info = dmas_info[:-1]
        self.device_str = ' '.join(self.cbdma_dev_infos)
        self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=%s %s' % (self.drivername, self.device_str), '# ', 60)

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect('modprobe ioatdma', '# ')
            self.dut.send_expect('./usertools/dpdk-devbind.py -u %s' % self.device_str, '# ', 30)
            self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=ioatdma  %s' % self.device_str, '# ', 60)

    def launch_testpmd_gro_on(self, mode=1, queue=1):
        #
        # Launch the vhost sample with different parameters
        # mode 1 : tcp traffic light mode
        # mode 2 : tcp traffic heavy mode
        # mode 3 : vxlan traffic light mode
        # mode 4 : tcp traffic flush 4
        # mode 5 : tcp traffice light mode with cdbma enable
        if mode == 5:
            self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=2)
            eal_param = self.dut.create_eal_parameters(cores=self.vhost_list, vdevs=["'net_vhost0,iface=%s/vhost-net,queues=%s,dmas=[%s]'" % (self.base_dir, queue, self.dmas_info)])
            self.testcmd_start = self.path + eal_param + " -- -i --txd=1024 --rxd=1024 --txq=2 --rxq=2"
            self.vhost_user = self.dut.new_session(suite="user")
            self.vhost_user.send_expect(self.testcmd_start, "testpmd> ", 120)
        else:
            eal_param = self.dut.create_eal_parameters(cores=self.vhost_list, vdevs=['net_vhost0,iface=%s/vhost-net,queues=%s' % (self.base_dir, queue)], ports=[self.pci])
            self.testcmd_start = self.path + eal_param + " -- -i  --enable-hw-vlan-strip --tx-offloads=0x00 --txd=1024 --rxd=1024"
            self.vhost_user = self.dut.new_session(suite="user")
            self.vhost_user.send_expect(self.testcmd_start, "testpmd> ", 120)
            self.set_testpmd_params()

    def set_testpmd_params(self, mode=1):
        # set testpmd params
        self.vhost_user.send_expect("set fwd csum", "testpmd> ", 120)
        self.vhost_user.send_expect("stop", "testpmd> ", 120)
        self.vhost_user.send_expect("port stop 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port stop 1", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set tcp hw 0", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set ip hw 0", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set tcp hw 1", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set ip hw 1", "testpmd> ", 120)
        if (mode == 1 or mode == 5):
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 1", "testpmd> ", 120)
        elif (mode == 2):
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 2", "testpmd> ", 120)
        elif (mode == 3):
            self.vhost_user.send_expect("csum parse-tunnel on 1", "testpmd> ", 120)
            self.vhost_user.send_expect("csum parse-tunnel on 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set outer-ip hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 2", "testpmd> ", 120)
        else:
            self.vhost_user.send_expect("set port 0 gro on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gro flush 4", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 1", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def set_testpmd_gro_off(self):
        #
        # Launch the vhost sample with different parameters
        #
        self.vhost_user.send_expect("stop", "testpmd> ", 120)
        self.vhost_user.send_expect("set port 0 gro off", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def quit_testpmd(self):
        # Quit testpmd and close temp ssh session
        self.vhost_user.send_expect("quit", "#", 120)
        self.dut.close_session(self.vhost_user)

    def config_kernel_nic_host(self, mode=1):
        if (mode == 0):
            self.dut.send_expect("ip netns del ns1", "#")
            self.dut.send_expect("ip netns add ns1", "#")
            self.dut.send_expect("ip link set %s netns ns1" %self.nic_in_kernel, "#")
            self.dut.send_expect("ip netns exec ns1 ifconfig %s 1.1.1.8 up" %self.nic_in_kernel, "#")
            self.dut.send_expect("ip netns exec ns1 ethtool -K %s tso on" %self.nic_in_kernel, "#")
        if (mode == 1):
            self.dut.send_expect("ip netns del ns1", "#")
            self.dut.send_expect("ip netns add ns1", "#")
            self.dut.send_expect("ip link set %s netns ns1" %self.nic_in_kernel, "#")
            self.dut.send_expect("ip netns exec ns1 ifconfig %s 1.1.2.4/24 up" %self.nic_in_kernel, "#")
            self.dut.send_expect("ip netns exec ns1 ip link add vxlan1 type vxlan id 42 dev %s dstport 4789" %self.nic_in_kernel, "#")
            self.dut.send_expect("ip netns exec ns1 bridge fdb append to 00:00:00:00:00:00 dst 1.1.2.3 dev vxlan1", "#")
            self.dut.send_expect("ip netns exec ns1 ip addr add 50.1.1.1/24 dev vxlan1", "#")
            self.dut.send_expect("ip netns exec ns1 ip link set up dev vxlan1", "#")

    def prepare_dpdk(self):
        #
        # Changhe the testpmd checksum fwd code for mac change
        self.dut.send_expect("cp ./app/test-pmd/csumonly.c ./app/test-pmd/csumonly_backup.c", "#")
        self.dut.send_expect("cp ./drivers/net/vhost/rte_eth_vhost.c ./drivers/net/vhost/rte_eth_vhost-backup.c", "#")
        self.dut.send_expect("sed -i '/ether_addr_copy(&peer_eth/i\#if 0' ./app/test-pmd/csumonly.c", "#")
        self.dut.send_expect("sed -i '/parse_ethernet(eth_hdr, &info/i\#endif' ./app/test-pmd/csumonly.c", "#")
        # change offload of vhost
        tx_offload = 'DEV_TX_OFFLOAD_VLAN_INSERT | ' + \
                    'DEV_TX_OFFLOAD_UDP_CKSUM | ' + \
                    'DEV_TX_OFFLOAD_TCP_CKSUM | ' + \
                    'DEV_TX_OFFLOAD_IPV4_CKSUM | ' + \
                    'DEV_TX_OFFLOAD_TCP_TSO;'
        rx_offload = 'DEV_RX_OFFLOAD_VLAN_STRIP | ' + \
                    'DEV_RX_OFFLOAD_TCP_CKSUM | ' + \
                    'DEV_RX_OFFLOAD_UDP_CKSUM | ' + \
                    'DEV_RX_OFFLOAD_IPV4_CKSUM | ' + \
                    'DEV_RX_OFFLOAD_TCP_LRO;'
        self.dut.send_expect("sed -i 's/DEV_TX_OFFLOAD_VLAN_INSERT;/%s/' drivers/net/vhost/rte_eth_vhost.c" % tx_offload, "#")
        self.dut.send_expect("sed -i 's/DEV_RX_OFFLOAD_VLAN_STRIP;/%s/' drivers/net/vhost/rte_eth_vhost.c" % rx_offload, "#")
        self.dut.build_install_dpdk(self.dut.target)

    def unprepare_dpdk(self):
        # Recovery the DPDK code to original
        self.dut.send_expect("cp ./app/test-pmd/csumonly_backup.c ./app/test-pmd/csumonly.c ", "#")
        self.dut.send_expect("cp ./drivers/net/vhost/rte_eth_vhost-backup.c ./drivers/net/vhost/rte_eth_vhost.c ", "#")
        self.dut.send_expect("rm -rf ./app/test-pmd/csumonly_backup.c", "#")
        self.dut.send_expect("rm -rf ./drivers/net/vhost/rte_eth_vhost-backup.c", "#")
        self.dut.build_install_dpdk(self.dut.target)

    def set_vm_cpu_number(self, vm_config):
        # config the vcpu numbers = 1
        # config the cpupin only have one core
        params_number = len(vm_config.params)
        for i in range(params_number):
            if list(vm_config.params[i].keys())[0] == 'cpu':
                vm_config.params[i]['cpu'][0]['number'] = 1
                vm_config.params[i]['cpu'][0]['cpupin'] = self.qemu_cpupin

    def start_vm(self, mode=1, queue=1):
        self.vm1 = VM(self.dut, 'vm0', 'vhost_sample')
        self.vm1.load_config()
        vm_params_1 = {}
        vm_params_1['driver'] = 'vhost-user'
        vm_params_1['opt_path'] = self.base_dir + '/vhost-net'
        vm_params_1['opt_mac'] = self.virtio_mac1
        vm_params_1['opt_queue'] = queue
        if mode == 5:
            vm_params_1['opt_settings'] = 'mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,mq=on,vectors=15'
        else:
            vm_params_1['opt_settings'] = 'mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on'
        self.vm1.set_vm_device(**vm_params_1)
        self.set_vm_cpu_number(self.vm1)
        try:
            self.vm1_dut = self.vm1.start(load_config=False, set_target=False)
            if self.vm1_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            print((utils.RED("Failure for %s" % str(e))))
        self.vm1_dut.restore_interfaces()

    def iperf_result_verify(self, run_info):
        '''
        Get the iperf test result
        '''
        fmsg = self.dut.send_expect("cat /root/iperf_client.log", "#")
        print(fmsg)
        iperfdata = re.compile('[\d+]*.[\d+]* [M|G|K]bits/sec').findall(fmsg)
        print(iperfdata)
        self.verify(iperfdata, 'There no data about this case')
        self.result_table_create(['Data', 'Unit'])
        results_row = [run_info]
        results_row.append(iperfdata[-1])
        self.result_table_add(results_row)
        self.result_table_print()
        self.output_result = "Iperf throughput is %s" % iperfdata[-1]
        self.logger.info(self.output_result)
        iperfdata_kb = 0
        tmp_value = iperfdata[-1].split(" ")[0]
        if 'Gbits' in iperfdata[-1]:
            iperfdata_kb = float(tmp_value)*1000000
        elif 'Mbits' in iperfdata[-1]:
            iperfdata_kb = float(tmp_value)*1000
        else:
            iperfdata_kb = float(tmp_value)
        return iperfdata_kb

    def test_vhost_gro_tcp_lightmode(self):
        self.config_kernel_nic_host(0)
        self.launch_testpmd_gro_on()
        self.start_vm()
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect('ifconfig %s %s' %(self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect('ethtool -K %s gro off' % (self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('iperf -s', '', 10)
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect('ip netns exec ns1 iperf -c %s -i 1 -t 10 -P 1> /root/iperf_client.log &' %(self.virtio_ip1), '', 180)
        time.sleep(30)
        tc1_perfdata = self.iperf_result_verify('GRO lib')
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        # Turn off DPDK GRO lib and Kernel GRO off
        self.set_testpmd_gro_off()
        self.dut.send_expect('ip netns exec ns1 iperf -c %s -i 1 -t 10  -P 1 > /root/iperf_client.log &' %(self.virtio_ip1), '', 180)
        time.sleep(30)
        self.iperf_result_verify('Kernel GRO')
        print(("the Kernel GRO %s " % (self.output_result)))
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect('echo %s > /root/dpdk_gro_lib_on_iperf_tc1.log' % tc1_perfdata, '#', 10)

    def test_vhost_gro_tcp_heavymode(self):
        self.config_kernel_nic_host(0)
        self.heavymode = 2
        self.launch_testpmd_gro_on(self.heavymode)
        self.start_vm()
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect('ifconfig %s %s' %(self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect('ethtool -K %s gro off' %(self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('iperf -s', '', 10)
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect('ip netns exec ns1 iperf -c %s -i 1 -t 10 -P 1> /root/iperf_client.log &' %(self.virtio_ip1), '', 180)
        time.sleep(30)
        self.iperf_result_verify('GRO lib')
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_gro_tcp_heavymode_flush4(self):
        self.config_kernel_nic_host(0)
        self.heavymode = 4
        self.launch_testpmd_gro_on(self.heavymode)
        self.start_vm()
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect('ifconfig %s %s' %(self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect('ethtool -K %s gro off' %(self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('iperf -s', '', 10)
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect('ip netns exec ns1 iperf -c %s -i 1 -t 10 -P 1> /root/iperf_client.log &' %(self.virtio_ip1), '', 180)
        time.sleep(30)
        self.iperf_result_verify('GRO lib')
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_gro_tcp_ipv4_with_cbdma_enable(self):
        self.config_kernel_nic_host(0)
        self.heavymode = 5
        self.launch_testpmd_gro_on(self.heavymode, queue=2)
        self.start_vm(mode=5, queue=2)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect('ifconfig %s %s up' %(self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ethtool -L %s combined 2' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect('ethtool -K %s gro off' %  (self.vm1_intf), '#', 10)
        self.set_testpmd_params()
        self.vm1_dut.send_expect('iperf -s', '', 10)
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        out = self.dut.send_expect('ip netns exec ns1 iperf -c %s -i 1 -t 60 -m -P 2 > /root/iperf_client.log &' %(self.virtio_ip1), '', 180)
        time.sleep(30)
        print(out)
        perfdata = self.iperf_result_verify('GRO lib')
        print(("the GRO lib %s " % (self.output_result)))
        #self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        exp_perfdata = self.dut.send_expect("cat /root/dpdk_gro_lib_on_iperf_tc5.log", "#")
        self.verify("No such file or directory" not in exp_perfdata,
                    "Cannot find dpdk_gro_lib_on_iperf_tc5.log, please run test_vhost_gro_with_2queues_tcp_lightmode firstly")
        if exp_perfdata:
            self.verify(float(perfdata) > float(exp_perfdata),
                        "TestFailed: W/cbdma iperf data is %s Kbits/sec, W/O cbdma iperf data is %s Kbits/sec" %(perfdata, exp_perfdata))

    def test_vhost_gro_with_2queues_tcp_lightmode(self):
        """
        Test Case5: DPDK GRO test with 2 queues using tcp/ipv4 traffic
        """
        self.config_kernel_nic_host(0)
        self.launch_testpmd_gro_on(mode=1, queue=2)
        self.start_vm(mode=1, queue=2)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect('ifconfig %s %s' %(self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect('ethtool -K %s gro off' % (self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('iperf -s', '', 10)
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect('ip netns exec ns1 iperf -c %s -i 2 -t 60 -f g -m > /root/iperf_client.log &' %(self.virtio_ip1), '', 180)
        time.sleep(60)
        perfdata = self.iperf_result_verify('GRO lib')
        print(("the GRO lib %s " % (self.output_result)))
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        # Turn off DPDK GRO lib and Kernel GRO off
        self.set_testpmd_gro_off()
        self.dut.send_expect('ip netns exec ns1 iperf -c %s -i 2 -t 60 -f g -m > /root/iperf_client.log &' %(self.virtio_ip1), '', 180)
        time.sleep(60)
        self.iperf_result_verify('Kernel GRO')
        print(("the Kernel GRO %s " % (self.output_result)))
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect('echo %s > /root/dpdk_gro_lib_on_iperf_tc5.log' % perfdata, '#', 10)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net" % self.base_dir, "#")
        time.sleep(2)
        self.dut.send_expect("ip netns del ns1", "# ", 30)
        self.dut.send_expect("./usertools/dpdk-devbind.py -u %s" % (self.peer_pci), '# ', 30)
        self.dut.send_expect("./usertools/dpdk-devbind.py -b %s %s" %(self.pci_drv, self.peer_pci), '# ', 30)
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        for i in self.dut_ports:
            port = self.dut.ports_info[i]['port']
            port.bind_driver(self.def_driver)
        self.unprepare_dpdk()
        self.dut.send_expect("ip netns del ns1", "# ", 30)
        self.dut.send_expect("./usertools/dpdk-devbind.py -u %s" % (self.pci), '# ', 30)
        self.dut.send_expect("./usertools/dpdk-devbind.py -b %s %s" % (self.pci_drv, self.pci), '# ', 30)

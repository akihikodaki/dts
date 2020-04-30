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

DPDK gso lib test suite.
In this suite, in order to check the performance of gso lib, will use one
hostcpu to start qemu and only have one vcpu
"""
import time
import utils
import re
from test_case import TestCase
from virt_common import VM
from config import UserConf
import vhost_peer_conf as peer


class TestDPDKGsoLib(TestCase):

    def set_up_all(self):
        # This suite will not use the port config in ports.cfg
        # it will use the port config in vhost_gro.cfg
        # And it need two interface reconnet in DUT

        # unbind the port which config in ports.cfg
        self.dut_ports = self.dut.get_ports()
        self.def_driver = self.dut.ports_info[self.dut_ports[0]]['port'].get_nic_driver()
        for i in self.dut_ports:
            port = self.dut.ports_info[i]['port']
            port.bind_driver()

        # get and bind the port in conf file
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

        # get the numa info about the pci info which config in peer cfg
        bus = int(self.pci[5:7], base=16)
        if bus >= 128:
            self.socket = 1
        else:
            self.socket = 0
        # get core list on this socket, 2 cores for testpmd, 1 core for qemu
        cores_config = '1S/3C/1T'
        self.verify(self.dut.number_of_cores >= 3,
                "There has not enought cores to test this case %s" % self.suite_name)
        cores_list = self.dut.get_core_list("1S/3C/1T", socket=self.socket)
        self.vhost_list = cores_list[0:2]
        self.qemu_cpupin = cores_list[2:3][0]

        # Set the params for VM
        self.virtio_ip1 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.memory_channel = self.dut.get_memory_channels()
        # set diff arg about mem_socket base on socket number
        if len(set([int(core['socket']) for core in self.dut.cores])) == 1:
            self.socket_mem = '1024'
        else:
            self.socket_mem = '1024,1024'

        self.prepare_dpdk()
        self.base_dir = self.dut.base_dir.replace('~', '/root')

    def set_up(self):
        #
        # Run before each test case.
        # Clean the execution ENV
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def launch_testpmd_gso_on(self, mode=0):
        # mode = 0: DPDK GSO for TCP Traffic
        # mode = 1: DPDK GSO for UDP Traffic
        # mode = 2: DPDK GSO for Vxlan/GRE Traffic
        # mode = 3: TSO
        # mode = others: NO DPDK GSO/TSO
        eal_param = self.dut.create_eal_parameters(cores=self.vhost_list, vdevs=['net_vhost0,iface=%s/vhost-net,queues=1' % self.base_dir])
        self.testcmd_start = self.target + "/app/testpmd " + eal_param + " -- -i --tx-offloads=0x00 --txd=1024 --rxd=1024"
        self.vhost_user = self.dut.new_session(suite="user")
        self.vhost_user.send_expect(self.testcmd_start, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd csum", "testpmd> ", 120)
        self.vhost_user.send_expect("stop", "testpmd> ", 120)
        if(mode == 0):
            self.vhost_user.send_expect("port stop 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set ip hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set tcp hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("set port 0 gso on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gso segsz 1460", "testpmd> ", 120)
            self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        if (mode == 1):
            self.vhost_user.send_expect("port stop 1", "testpmd> ", 120)
            self.vhost_user.send_expect("port stop 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set ip hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set tcp hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("set port 0 gso on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gso segsz 1460", "testpmd> ", 120)
            self.vhost_user.send_expect("port start 1", "testpmd> ", 120)
            self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        elif(mode == 3):
            self.vhost_user.send_expect("port stop 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set ip hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set tcp hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("tso set 1460 0", "testpmd> ", 120)
            self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        elif (mode == 2):
            self.vhost_user.send_expect("port stop 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set ip hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set tcp hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum set outer-ip hw 0", "testpmd> ", 120)
            self.vhost_user.send_expect("csum parse-tunnel on 0", "testpmd> ", 120)
            self.vhost_user.send_expect("set port 0 gso on", "testpmd> ", 120)
            self.vhost_user.send_expect("set gso segsz 1400", "testpmd> ", 120)
            self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        else:
            self.vhost_user.send_expect("set fwd csum", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def quit_testpmd(self):
        # Quit testpmd and close temp ssh session
        self.vhost_user.send_expect("quit", "#", 120)
        self.dut.close_session(self.vhost_user)

    def config_kernel_nic_host(self):
        #
        self.dut.send_expect("ip netns del ns1", "#")
        self.dut.send_expect("ip netns add ns1", "#")
        self.dut.send_expect(
            "ip link set %s netns ns1" %
            self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ifconfig %s 1.1.1.8 up" %
            self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ethtool -K %s gro on" %
            self.nic_in_kernel, "#")

    def config_kernel_nic_host_for_vxlan(self):
        self.dut.send_expect("ip netns del ns1", "#")
        self.dut.send_expect("ip netns add ns1", "#")
        self.dut.send_expect(
            "ip link set %s netns ns1" %
            self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ifconfig %s 188.0.0.1 up" %
            self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ip link add vxlan100 type vxlan id 1000 remote 188.0.0.2 local 188.0.0.1 dstport 4789 dev %s" %
            self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ifconfig vxlan100 1.1.1.1/24 up",
            "#")

    def config_kernel_nic_host_for_gre(self):
        self.dut.send_expect("ip netns del ns1", "#")
        self.dut.send_expect("ip netns add ns1", "#")
        self.dut.send_expect(
            "ip link set %s netns ns1" %
            self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ifconfig %s 188.0.0.1 up" %
            self.nic_in_kernel, "#")
        self.dut.send_expect(
            "ip netns exec ns1 ip tunnel add gre100 mode gre remote 188.0.0.2 local 188.0.0.1",
            "#")
        self.dut.send_expect(
            "ip netns exec ns1 ifconfig gre100 1.1.1.1/24 up",
            "#")

    def prepare_dpdk(self):
        # Changhe the testpmd checksum fwd code for mac change
        self.dut.send_expect(
            "cp ./app/test-pmd/csumonly.c ./app/test-pmd/csumonly_backup.c",
            "#")
        self.dut.send_expect(
            "sed -i '/ether_addr_copy(&peer_eth/i\#if 0' ./app/test-pmd/csumonly.c", "#")
        self.dut.send_expect(
            "sed -i '/parse_ethernet(eth_hdr, &info/i\#endif' ./app/test-pmd/csumonly.c", "#")
        self.dut.build_install_dpdk(self.dut.target)

    def unprepare_dpdk(self):
        # Recovery the DPDK code to original
        time.sleep(5)
        self.dut.send_expect(
            "cp ./app/test-pmd/csumonly_backup.c ./app/test-pmd/csumonly.c ",
            "#")
        self.dut.send_expect("rm -rf ./app/test-pmd/csumonly_backup.c", "#")
        self.dut.build_install_dpdk(self.dut.target)

    def set_vm_cpu_number(self, vm_config):
        # config the vcpu numbers = 1
        # config the cpupin only have one core
        params_number = len(vm_config.params)
        for i in range(params_number):
            if list(vm_config.params[i].keys())[0] == 'cpu':
                vm_config.params[i]['cpu'][0]['number'] = 1
                vm_config.params[i]['cpu'][0]['cpupin'] = self.qemu_cpupin

    def start_vm(self, mode=0):
        '''
        Start two VM, each VM has one virtio device
        mode 0 : VM will send big packet , above MTU
        mdoe 1:  VM only send packet under MTU
        '''
        self.vm1 = VM(self.dut, 'vm0', 'vhost_sample')
        self.vm1.load_config()
        vm_params_1 = {}
        vm_params_1['driver'] = 'vhost-user'
        vm_params_1['opt_path'] = self.base_dir + '/vhost-net'
        vm_params_1['opt_mac'] = self.virtio_mac1
        # tcp and udp traffic
        if(mode == 0):
            vm_params_1[
                'opt_settings'] = 'mrg_rxbuf=on,csum=on,gso=on,host_tso4=on,guest_tso4=on,host_ufo=on,guest_ufo=on'
        # no offload
        elif(mode == 1):
            vm_params_1[
                'opt_settings'] = 'mrg_rxbuf=on,csum=off,gso=off,host_tso4=off,guest_tso4=off'
        # gre and vxlan
        elif(mode == 2):
            vm_params_1[
                'opt_settings'] = 'mrg_rxbuf=on,csum=on,guest_csum=on,gso=on,host_tso4=on,guest_tso4=on,guest_ecn=on'
        self.vm1.set_vm_device(**vm_params_1)
        self.set_vm_cpu_number(self.vm1)

        time.sleep(5)
        try:
            self.vm1_dut = self.vm1.start(load_config=False, set_target=False)
            if self.vm1_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            print((utils.RED("Failure for %s" % str(e))))
        self.vm1_dut.restore_interfaces()

    def iperf_result_verify(self, vm_client):
        '''
        Get the iperf test result
        '''
        fmsg = vm_client.send_expect("cat /root/iperf_client.log", "#")
        print(fmsg)
        iperfdata = re.compile('[\d+]*.[\d+]* [M|G|K]bits/sec').findall(fmsg)
        print(iperfdata)
        self.verify(iperfdata, 'There no data about this case')
        self.result_table_create(['Data', 'Unit'])
        results_row = ['GSO']
        results_row.append(iperfdata[-1])
        self.result_table_add(results_row)
        self.result_table_print()
        self.output_result = "Iperf throughput is %s" % iperfdata[-1]
        self.logger.info(self.output_result)

    def test_vhost_gso_dpdk_tcp(self):
        """
        DPDK GSO test with tcp traffic
        """
        # Config the NIC which will be assigned to another namespace
        self.config_kernel_nic_host()
        self.launch_testpmd_gso_on(0)
        self.start_vm(0)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        self.vm1_dut.send_expect("sh /home/lei/dpdk/Guest_script.sh", '#', 60)
        self.vm1_dut.send_expect('ifconfig %s %s' % (self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect('ethtool -K %s gso off' % (self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect('ip netns exec ns1 iperf -s', '', 10)
        self.vm1_dut.send_expect('iperf -c 1.1.1.8 -i 1 -t 10 -P 5 > /root/iperf_client.log &', '', 180)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.vm1_dut)
        print(("the GSO lib for TCP traffic %s " % (self.output_result)))
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect("ip netns del ns1", "#")
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_gso_dpdk_udp(self):
        """
        DPDK GSO test with udp traffic
        """
        # Config the NIC which will be assigned to another namespace
        self.config_kernel_nic_host()
        self.launch_testpmd_gso_on(1)
        self.start_vm(0)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        self.vm1_dut.send_expect(
            'ifconfig %s %s' %
            (self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect('ethtool -K %s gso off' % (self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect('ip netns exec ns1 iperf -s -u', '', 10)
        self.vm1_dut.send_expect(
            'iperf -c 1.1.1.8 -i 1 -u -t 10 -l 9000 -b 10G -P 5 > /root/iperf_client.log &',
            '',
            60)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.vm1_dut)
        print(("the GSO lib for UDP traffic %s " % (self.output_result)))
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect("ip netns del ns1", "#")
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_tso_dpdk(self):
        self.config_kernel_nic_host()
        self.launch_testpmd_gso_on(3)
        self.start_vm(0)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect(
            'ifconfig %s %s' %
            (self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect(
            'ethtool -K %s gso off' %
            (self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect(
            'ip netns exec ns1 iperf -s',
            '',
            10)
        self.vm1_dut.send_expect(
            'iperf -c 1.1.1.8 -i 1 -t 10 -P 5 > /root/iperf_client.log &',
            '',
            180)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.vm1_dut)
        print(("the TSO lib %s " % (self.output_result)))
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_kernel_gso_dpdk(self):
        self.config_kernel_nic_host()
        self.launch_testpmd_gso_on(4)
        self.start_vm(1)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect(
            'ifconfig %s %s' %
            (self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect(
            'ethtool -K %s gso on' %
            (self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect(
            'ip netns exec ns1 iperf -s',
            '',
            10)

        self.vm1_dut.send_expect(
            'iperf -c 1.1.1.8 -i 1 -t 10 -P 5 > /root/iperf_client.log &',
            '',
            180)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.vm1_dut)
        print(("Kernel GSO %s " % (self.output_result)))
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_no_gso_dpdk(self):
        self.config_kernel_nic_host()
        self.launch_testpmd_gso_on(4)
        self.start_vm(1)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        # Start the Iperf test
        self.vm1_dut.send_expect('ifconfig -a', '#', 30)
        self.vm1_dut.send_expect(
            'ifconfig %s %s' %
            (self.vm1_intf, self.virtio_ip1), '#', 10)
        self.vm1_dut.send_expect('ifconfig %s up' % self.vm1_intf, '#', 10)
        self.vm1_dut.send_expect(
            'ethtool -K %s gso off' %
            (self.vm1_intf), '#', 10)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect(
            'ip netns exec ns1 iperf -s',
            '',
            10)
        self.vm1_dut.send_expect(
            'iperf -c 1.1.1.8 -i 1 -t 10 -P 5 > /root/iperf_client.log &',
            '',
            180)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.vm1_dut)
        print(("NO GSO/TSO %s " % (self.output_result)))
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_gso_with_vxlan(self):
        """
        Test Performance with GSO for VXLAN traffic
        """
        self.config_kernel_nic_host_for_vxlan()
        self.launch_testpmd_gso_on(2)
        self.start_vm(2)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name and unbind virtio net
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        self.vm1_dut.send_expect(
            'ifconfig %s 188.0.0.2 up' %
            self.vm1_intf, '#', 30)
        self.vm1_dut.send_expect(
            'ip link add vxlan100 type vxlan id 1000 remote 188.0.0.1 local 188.0.0.2 dstport 4789 dev %s' %
            self.vm1_intf, '#', 30)
        self.vm1_dut.send_expect('ifconfig vxlan100 1.1.1.2/24 up', '#', 30)
        # Start Iperf test
        self.dut.send_expect('ip netns exec ns1 iperf -s ', '', 10)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.vm1_dut.send_expect('iperf -c 1.1.1.1 -i 1 -t 10 -P 5 > /root/iperf_client.log &', '', 60)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.vm1_dut)
        print(("the GSO lib for Vxlan traffic %s " % (self.output_result)))
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect("ip netns del ns1", "#")
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def test_vhost_gso_with_gre(self):
        """
        Test Performance with GSO for GRE traffic
        """
        self.config_kernel_nic_host_for_gre()
        self.launch_testpmd_gso_on(2)
        self.start_vm(2)
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        # Get the virtio-net device name and unbind virtio net
        for port in self.vm1_dut.ports_info:
            self.vm1_intf = port['intf']
        self.vm1_dut.send_expect(
            'ifconfig %s 188.0.0.2 up' %
            self.vm1_intf, '#', 30)
        self.vm1_dut.send_expect(
            'ip tunnel add gre100 mode gre remote 188.0.0.1 local 188.0.0.2',
            '#',
            30)
        self.vm1_dut.send_expect('ifconfig gre100 1.1.1.2/24 up', '#', 30)
        self.dut.send_expect('ip netns exec ns1 iperf -s', '', 10)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.vm1_dut.send_expect('iperf -c 1.1.1.1 -i 1 -t 10 -P 5 > /root/iperf_client.log &', '', 60)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.vm1_dut)
        self.vm1_dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.dut.send_expect("ip netns del ns1", "#")
        self.quit_testpmd()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % (self.peer_pci), '# ', 30)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -b %s %s" %
            (self.pci_drv, self.peer_pci), '# ', 30)
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        for i in self.dut_ports:
            port = self.dut.ports_info[i]['port']
            port.bind_driver(self.def_driver)
        self.unprepare_dpdk()
        self.dut.send_expect("ip netns del ns1", "#", 30)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % (self.pci), '# ', 30)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -b %s %s" %
            (self.pci_drv, self.pci), '# ', 30)

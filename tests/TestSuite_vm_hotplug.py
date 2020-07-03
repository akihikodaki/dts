# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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

Test some vm hotplug function with vfio

"""
import os
import re
import time
from qemu_kvm import QEMUKvm
from test_case import TestCase
from pmd_output import PmdOutput

VM_CORES_MASK = 'all'


class TestVmHotplug(TestCase):

    def set_up_all(self):

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.dut.restore_interfaces()
        tester_port = self.tester.get_local_port(self.dut_ports[0])
        self.tester_intf = self.tester.get_interface(tester_port)

        self.ports = self.dut.get_ports()
        self.dut.send_expect('modprobe vfio-pci', '#')
        self.setup_pf_1vm_env_flag = 0
        tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_intf0 = self.tester.get_interface(tester_port0)
        self.tester_intf1 = self.tester.get_interface(tester_port1)
        self.device = 0
        self.test_pmd_flag = 1
        # due to current dts framework is not support monitor stdio,
        # so start vm command is written with hardcode
        self.qemu_cmd = "taskset -c 0-7 qemu-system-x86_64 -enable-kvm \
               -pidfile /tmp/.vm0.pid \
               -m 10240 -cpu host -smp 8 -name vm0 \
               -monitor unix:/tmp/vm0_monitor.sock,server,nowait \
               -chardev socket,path=/tmp/vm0_qga0.sock,server,nowait,id=vm0_qga0 \
               -device virtio-serial \
               -device virtserialport,chardev=vm0_qga0,name=org.qemu.guest_agent.0 \
               -device e1000,netdev=nttsip1 \
               -netdev user,id=nttsip1,hostfwd=tcp:%s:6000-:22 \
               -monitor stdio \
               -drive file=/home/image/test_vfio.img \
               -vnc :5 \
               -device vfio-pci,host=%s,id=dev1 \
               "

    def start_vm(self, device=1):
        self.host_session = self.dut.new_session(suite="host_session")
        self.dut.bind_interfaces_linux('vfio-pci', [self.ports[0]])
        if device == 2:
            self.dut.bind_interfaces_linux('vfio-pci', [self.ports[1]])
            self.qemu_cmd += '-device vfio-pci,host=%s,id=dev2'
            cmd = self.qemu_cmd % (self.dut.get_ip_address(), self.dut.ports_info[0]['pci'], self.dut.ports_info[1]['pci'])
        else:
            cmd = self.qemu_cmd % (self.dut.get_ip_address(), self.dut.ports_info[0]['pci'])
        self.host_session.send_expect(cmd, "QEMU ")
        time.sleep(10)
        self.vm0_dut = self.connect_vm()
        self.verify(self.vm0_dut is not None, 'vm start fail')
        self.setup_pf_1vm_env_flag = 1
        self.vm_session = self.vm0_dut.new_session(suite="vm_session")
        self.vf_pci0 = self.vm0_dut.ports_info[0]['pci']
        if device == 2:
            self.vf_pci1 = self.vm0_dut.ports_info[1]['pci']
        self.vm0_dut.get_ports('any')
        self.vm_testpmd = PmdOutput(self.vm0_dut)

    def connect_vm(self):
        self.vm0 = QEMUKvm(self.dut, 'vm0', 'vm_hotplug')
        self.vm0.net_type = 'hostfwd'
        self.vm0.hostfwd_addr = '%s:6000' % self.dut.get_ip_address()
        self.vm0.def_driver = 'vfio-pci'
        self.vm0.driver_mode = 'noiommu'
        self.wait_vm_net_ready()
        vm_dut = self.vm0.instantiate_vm_dut(autodetect_topo=False)
        if vm_dut:
            return vm_dut
        else:
            return None

    def wait_vm_net_ready(self):
        self.vm_net_session = self.dut.new_session(suite='vm_net_session')
        self.start_time = time.time()
        cur_time = time.time()
        time_diff = cur_time - self.start_time
        while time_diff < 120:
            try:
                out = self.vm_net_session.send_expect('~/QMP/qemu-ga-client --address=/tmp/vm0_qga0.sock ifconfig', '#')
            except Exception as EnvironmentError:
                pass
            if '10.0.2' in out:
                pos = self.vm0.hostfwd_addr.find(':')
                ssh_key = '[' + self.vm0.hostfwd_addr[:pos] + ']' + self.vm0.hostfwd_addr[pos:]
                os.system('ssh-keygen -R %s' % ssh_key)
                break
            time.sleep(1)
            cur_time = time.time()
            time_diff = cur_time - self.start_time
        self.dut.close_session(self.vm_net_session)

    def set_up(self):
        # according to nic number starts vm
        if self.device == 1:
            if 'two' in self.running_case:
                self.device = 2
                self.destroy_pf_1vm_env()
                self.dut.restore_interfaces()
                self.start_vm(self.device)
        elif self.device == 0:
            if 'two' in self.running_case:
                self.device = 2
            else:
                self.device = 1
            self.start_vm(self.device)
        else:
            if 'two' in self.running_case:
                pass
            else:
                self.destroy_pf_1vm_env()
                self.dut.restore_interfaces()
                self.start_vm(self.device)

    def test_one_device_hotplug(self):
        self.vm_testpmd.start_testpmd('all', '--hot-plug')
        self.verify_rxtx_only()
        # add cycle for del/add device
        for i in range(3):
            self.host_session.send_expect('device_del dev1', '(qemu)')
            time.sleep(2)
            self.check_vf_device(has_device=False)
            self.add_pf_device_qemu(device=1)
            out = self.vm_testpmd.execute_cmd('port attach %s' % self.vm0_dut.ports_info[0]['pci'])
            self.verify('Port 0 is attached' in out, 'attach device fail')
            self.verify_rxtx_only()
        self.vm_testpmd.execute_cmd('quit', '#')
        time.sleep(1)

    def test_one_device_reset_hotplug(self):
        for i in range(3):
            self.vm_testpmd.start_testpmd('all', '--hot-plug')
            self.verify_rxtx_only()
            # del device
            self.host_session.send_expect('device_del dev1', '(qemu)')
            self.vm_testpmd.execute_cmd('quit', '#')
            self.check_vf_device(has_device=False)
            self.add_pf_device_qemu(device=1)

            self.vm_testpmd.start_testpmd('all', '--hot-plug')
            self.verify_rxtx_only()
            self.vm_testpmd.execute_cmd('quit', '#')

    def test_two_device_hotplug(self):
        self.vm_testpmd.start_testpmd('all', '--hot-plug')
        self.verify_rxtx_only()
        # add cycle for del or add device
        for i in range(3):
            self.host_session.send_expect('device_del dev1', '(qemu)')
            self.host_session.send_expect('device_del dev2', '(qemu)')
            time.sleep(1)
            self.check_vf_device(has_device=False, device=2)
            self.add_pf_device_qemu(device=2)
            out = self.vm_testpmd.execute_cmd('port attach %s' % self.vm0_dut.ports_info[0]['pci'])
            self.verify('Port 0 is attached' in out, 'attach device fail')
            out = self.vm_testpmd.execute_cmd('port attach %s' % self.vm0_dut.ports_info[1]['pci'])
            self.verify('Port 1 is attached' in out, 'attach device fail')
            self.verify_rxtx_only()
        self.vm_testpmd.execute_cmd('quit', '#')

    def test_two_device_reset_hotplug(self):
        for i in range(3):
            self.vm_testpmd.start_testpmd('all', '--hot-plug')
            self.verify_rxtx_only()
            # del device
            self.host_session.send_expect('device_del dev1', '(qemu)')
            self.host_session.send_expect('device_del dev2', '(qemu)')
            self.vm_testpmd.execute_cmd('quit', '#')
            time.sleep(1)

            self.check_vf_device(has_device=False, device=2)
            self.add_pf_device_qemu(device=2)

            self.vm_testpmd.start_testpmd('all', '--hot-plug')
            self.verify_rxtx_only()
            self.vm_testpmd.execute_cmd('quit', '#')

    def start_tcpdump(self, iface_list):
        for iface in iface_list:
            self.tester.send_expect("rm -rf tcpdump%s.out" % iface, "#")
            self.tester.send_expect("tcpdump -c 1500 -i %s -vv -n 2>tcpdump%s.out &" % (iface, iface), "#")
        time.sleep(1)

    def get_tcpdump_package(self, iface_list):
        self.tester.send_expect("killall tcpdump", "#")
        result = []
        for iface in iface_list:
            out = self.tester.send_expect("cat tcpdump%s.out" % iface, "#", timeout=60)
            cap_num = re.findall('(\d+) packets', out)
            result.append(cap_num[0])
        return result

    def check_link_status(self, vm_info):
        loop = 1
        while (loop <= 3):
            out = vm_info.execute_cmd("show port info all", "testpmd> ", 120)
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if ("down" not in port_status):
                break
            time.sleep(3)
            loop += 1
        self.verify("down" not in port_status, "port can not up after start")

    def verify_rxtx_only(self):
        # rxonly
        self.vm_testpmd.execute_cmd('set fwd rxonly')
        self.vm_testpmd.execute_cmd('set verbose 1')
        self.vm_testpmd.execute_cmd('port start all')
        self.vm_testpmd.execute_cmd('start')
        self.check_link_status(self.vm_testpmd)

        self.send_packet()
        out = self.vm0_dut.get_session_output()
        time.sleep(1)
        self.verify(self.vf0_mac in out, 'vf0 receive packet fail')
        if self.device == 2:
            self.verify(self.vf1_mac in out, 'vf1 receive packet fail')
        # txonly
        self.vm_testpmd.execute_cmd('stop')
        self.vm_testpmd.execute_cmd('set fwd txonly')
        iface_list = []
        iface_list.append(self.tester_intf0)
        if self.device == 2:
            iface_list.append(self.tester_intf1)
        self.start_tcpdump(iface_list)
        self.vm_testpmd.execute_cmd('start')
        time.sleep(1)
        self.vm_testpmd.execute_cmd('stop')
        out = self.get_tcpdump_package(iface_list)
        for pkt_num in out:
            # rule out miscellaneous package possibility
            self.verify(int(pkt_num) > 1000, 'vf send packet fail')

    def check_vf_device(self, has_device=True, device=1):
        time.sleep(1)
        out = self.vm_session.send_expect('./usertools/dpdk-devbind.py -s', '#')
        time.sleep(2)
        if has_device:
            self.verify(self.vf_pci0 in out, 'no vf device')
            if device == 2:
                self.verify(self.vf_pci1 in out, 'no vf device')
        else:
            self.verify(self.vf_pci0 not in out, 'have vf device')
            if device == 2:
                self.verify(self.vf_pci1 not in out, 'have vf device')

    def add_pf_device_qemu(self, device=1):
        self.host_session.send_expect('device_add vfio-pci,host=%s,id=dev1' % self.dut.ports_info[0]['pci'], '(qemu)')
        if device == 2:
            self.host_session.send_expect('device_add vfio-pci,host=%s,id=dev2' % self.dut.ports_info[1]['pci'], '(qemu)')
        time.sleep(3)
        self.check_vf_device(has_device=True, device=device)
        self.vm_session.send_expect('./usertools/dpdk-devbind.py -b vfio-pci %s' % self.vf_pci0, '#')
        if device == 2:
            self.vm_session.send_expect('./usertools/dpdk-devbind.py -b vfio-pci %s' % self.vf_pci1, '#')
        time.sleep(1)

    def send_packet(self):
        self.vf0_mac = self.vm_testpmd.get_port_mac(0)
        pkts = []
        pkt1 = r'sendp([Ether(dst="%s")/IP()/UDP()/Raw(load="P"*26)], iface="%s")' % (self.vf0_mac, self.tester_intf)
        pkts.append(pkt1)
        if self.device == 2:
            self.vf1_mac = self.vm_testpmd.get_port_mac(1)
            pkt2 = r'sendp([Ether(dst="%s")/IP()/UDP()/Raw(load="P"*26)], iface="%s")' % (self.vf1_mac, self.tester_intf)
            pkts.append(pkt2)
        for pkt in pkts:

            self.tester.scapy_append(pkt)
        self.tester.scapy_execute()
        time.sleep(2)

    def destroy_pf_1vm_env(self):
        if getattr(self, 'vm0', None):
            self.vm0_dut.close_session(self.vm_session)
            try:
                self.vm0.stop()
            except Exception:
                pass
            self.dut.send_expect('killall qemu-system-x86_64', '#')
            time.sleep(1)
            out = self.dut.send_expect('ps -ef |grep qemu', '#')
            if self.dut.get_ip_address() in out:
                self.dut.send_expect('killall qemu-system-x86_64', '#')
            self.vm0 = None
            self.setup_pf_1vm_env_flag = 0
            self.dut.close_session(self.host_session)
            self.host_session = None
            self.vm_session = None

        self.dut.virt_exit()

        if getattr(self, 'used_dut_port', None):
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]['port']
            port.bind_driver()
            self.used_dut_port = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]['port']
            port.bind_driver()

    def tear_down(self):
        self.add_pf_device_qemu(self.device)

    def tear_down_all(self):
        self.destroy_pf_1vm_env()

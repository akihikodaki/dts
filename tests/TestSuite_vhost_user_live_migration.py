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

import re
import time
import utils
from virt_common import VM
from test_case import TestCase
from config import UserConf
from exception import VirtDutInitException


class TestVhostUserLiveMigration(TestCase):

    def set_up_all(self):
        # verify at least two duts
        self.verify(len(self.duts) >= 2, "Insufficient duts for live migration!!!")
        self.host_dut = self.duts[0]
        self.backup_dut = self.duts[1]

        # each dut required one ports
        host_dut_ports = self.host_dut.get_ports()
        backup_dut_ports = self.backup_dut.get_ports()
        self.verify(len(host_dut_ports) >= 1 and len(backup_dut_ports) >= 1,
                        "Insufficient ports for testing")

        # get mount info from cfg file
        conf_info = UserConf('conf/%s.cfg' % self.suite_name)
        conf_session = conf_info.conf._sections['mount_info']
        self.mount_path = conf_session['backup_mount_path']
        self.share_path = conf_session['host_share_dir']
        # config the mount server and client
        self.config_mount_server()
        self.config_mount_client()

        host_dut_port = host_dut_ports[0]
        host_dut_ip = self.host_dut.crb['My IP']
        backup_dut_port = backup_dut_ports[0]
        self.backup_dut_ip = self.backup_dut.crb['My IP']

        host_tport = self.tester.get_local_port_bydut(host_dut_port, host_dut_ip)
        backup_tport = self.tester.get_local_port_bydut(backup_dut_port, self.backup_dut_ip)
        self.host_tintf = self.tester.get_interface(host_tport)
        self.backup_tintf = self.tester.get_interface(backup_tport)

        self.host_pci_info = self.host_dut.ports_info[0]['pci']
        self.backup_pci_info = self.backup_dut.ports_info[0]['pci']

        self.virio_mac = "52:54:00:00:00:01"
        self.queue_number = 1
        self.vm_dut_host = None
        self.backup_vm = None
        self.screen_name = 'migration'
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        host_socket_num = len(set([int(core['socket']) for core in self.host_dut.cores]))
        backup_socket_num = len(set([int(core['socket']) for core in self.backup_dut.cores]))
        self.host_socket_mem = ','.join(['1024']*host_socket_num)
        self.backup_socket_mem = ','.join(['1024']*backup_socket_num)
        self.backup_speed = self.dut.skip_setup
        self.flag_compiled = False

    def set_up(self):
        self.host_dut.send_expect('rm ./vhost-net*', '# ', 30)
        self.backup_dut.send_expect('rm ./vhost-net*', '# ', 30)
        self.migration_done = False

    def config_mount_server(self):
        '''
        get the mount server config from file /etc/exports
        if not config the mount info of host_dut and backup_dut, config it
        '''
        config = '%s %s(rw,sync,no_root_squash)' % (
                    self.share_path, self.backup_dut.crb['IP'])
        try:
            fd = open('/etc/exports', 'r+')
        except Exception as e:
            self.logger.error('read file /etc/exports failed as %s' % str(e))
            raise e
        line = fd.readline()
        while(line):
            # already config in etc file
            if not line.startswith('#') and config in line:
                break
            line = fd.readline()
        # not config in etc file, wirte the config to it
        if not line:
            fd.write(config)
        fd.close()

    def config_mount_client(self):
        '''
        config the mount client to access the mount server
        '''
        out = self.backup_dut.send_expect('ls -d %s' % self.mount_path, '# ')
        if 'No such file or directory' in out:
            self.backup_dut.send_expect('mkdir -p %s' % self.mount_path, '# ')
        config = 'mount -t nfs -o nolock,vers=4  %s:%s %s' % (
                    self.host_dut.crb['IP'], self.share_path, self.mount_path)
        self.host_dut.send_expect('service nfs-server restart', '# ')
        self.backup_dut.send_expect('service nfs-server restart', '# ')
        self.backup_dut.send_expect('umount %s' % self.mount_path, '# ')
        self.backup_dut.send_expect(config, '# ')
        time.sleep(2)
        # verify the mount result
        out_host = self.host_dut.send_expect('ls %s' % self.share_path, '#')
        out_backup = self.backup_dut.send_expect('ls %s' % self.mount_path, '#')
        self.verify(out_host == out_backup, 'the mount action failed, please confrim it')

    def get_core_list(self):
        core_number = self.queue_number + 1
        core_config = '1S/%dC/1T' % core_number
        self.core_list0 = self.duts[0].get_core_list(core_config)
        self.core_list1 = self.duts[1].get_core_list(core_config)
        self.verify(len(self.core_list0) >= core_number and len(self.core_list1) >= core_number,
                    'There have not enough cores to start testpmd on duts')

    def launch_testpmd_as_vhost_on_both_dut(self, zero_copy=False):
        """
        start testpmd as vhost user on host_dut and backup_dut
        """
        self.get_core_list()
        zero_copy_str = ''
        if zero_copy is True:
            zero_copy_str = ',dequeue-zero-copy=1'
        testcmd = self.dut.target + "/app/testpmd "
        vdev = ['eth_vhost0,iface=%s/vhost-net,queues=%d%s' % (self.base_dir, self.queue_number, zero_copy_str)]
        para = " -- -i --nb-cores=%d --rxq=%d --txq=%d" % (self.queue_number, self.queue_number, self.queue_number)
        eal_params_first = self.dut.create_eal_parameters(cores=self.core_list0, prefix='vhost', ports=[self.host_pci_info], vdevs=vdev)
        eal_params_secondary = self.dut.create_eal_parameters(cores=self.core_list1, prefix='vhost', ports=[self.backup_pci_info], vdevs=vdev)
        host_cmd_line = testcmd + eal_params_first + para
        backup_cmd_line = testcmd + eal_params_secondary + para
        self.host_dut.send_expect(host_cmd_line, 'testpmd> ', 30)
        self.backup_dut.send_expect(backup_cmd_line, 'testpmd> ', 30)

    def start_testpmd_with_fwd_mode_on_both_dut(self, fwd_mode='io'):
        self.host_dut.send_expect('set fwd %s' % fwd_mode, 'testpmd> ', 30)
        self.host_dut.send_expect('start', 'testpmd> ', 30)
        self.backup_dut.send_expect('set fwd %s' % fwd_mode, 'testpmd> ', 30)
        self.backup_dut.send_expect('start', 'testpmd> ', 30)

    def setup_vm_env_on_both_dut(self, driver='default', packed=False):
        """
        Create testing environment on Host and Backup
        """
        if self.flag_compiled:
            self.dut.skip_setup = True
        try:
            # set up host virtual machine
            self.host_vm = VM(self.duts[0], 'host', '%s' % self.suite_name)
            vhost_params = {}
            vhost_params['driver'] = 'vhost-user'
            vhost_params['opt_path'] = self.base_dir + '/vhost-net'
            vhost_params['opt_mac'] = self.virio_mac
            opt_params = 'mrg_rxbuf=on'
            if self.queue_number > 1:
                vhost_params['opt_queue'] = self.queue_number
                opt_params = 'mrg_rxbuf=on,mq=on,vectors=%d' % (2*self.queue_number + 2)
            if packed:
                opt_params = opt_params + ',packed=on'
            vhost_params['opt_settings'] = opt_params
            self.host_vm.set_vm_device(**vhost_params)

            self.logger.info("Start virtual machine on host")
            self.vm_dut_host = self.host_vm.start()

            if self.vm_dut_host is None:
                raise Exception("Set up host VM ENV failed!")
            self.flag_compiled = True

            self.logger.info("Start virtual machine on backup host")
            # set up backup virtual machine
            self.backup_vm = VM(self.duts[1], 'backup', 'vhost_user_live_migration')
            vhost_params = {}
            vhost_params['driver'] = 'vhost-user'
            vhost_params['opt_path'] = self.base_dir + '/vhost-net'
            vhost_params['opt_mac'] = self.virio_mac
            if self.queue_number > 1:
                vhost_params['opt_queue'] = self.queue_number
            vhost_params['opt_settings'] = opt_params
            self.backup_vm.set_vm_device(**vhost_params)

            # start qemu command
            self.backup_vm.start()

        except Exception as ex:
            if ex is VirtDutInitException:
                self.host_vm.stop()
                self.host_vm = None
                # no session created yet, call internal stop function
                self.backup_vm._stop_vm()
                self.backup_vm = None
            else:
                self.destroy_vm_env()
                raise Exception(ex)

    def destroy_vm_env(self):
        self.logger.info("Stop virtual machine on host")
        try:
            if self.vm_dut_host is not None:
                if not self.migration_done:
                    self.vm_dut_host.send_expect('pkill screen', '# ')
                self.host_vm.stop()
                self.host_vm = None
        except Exception as e:
            self.logger.error('stop the qemu host failed as %s' % str(e))

        self.logger.info("Stop virtual machine on backup host")
        try:
            if self.backup_vm is not None:
                if self.migration_done:
                    self.vm_dut_backup.kill_all()
                    self.vm_dut_backup.send_expect('pkill screen', '# ')
                self.backup_vm.stop()
                self.backup_vm = None
        except Exception as e:
            self.logger.error('stop the qemu backup failed as %s' % str(e))

        # after vm stopped, stop vhost testpmd
        for crb in self.duts:
            crb.send_expect('quit', '# ')
            crb.kill_all()

    def bind_nic_driver_of_vm(self, crb, driver=""):
        # modprobe vfio driver
        ports = crb.get_ports()
        if driver == "vfio-pci":
            crb.send_expect('modprobe vfio-pci', '# ')
        for port in ports:
            netdev = crb.ports_info[port]['port']
            driver_now = netdev.get_nic_driver()
            if driver_now != driver:
                netdev.bind_driver(driver)

    def send_pkts_in_bg(self):
        """
        send packet from tester
        """
        sendp_fmt = "sendp([Ether(dst='%s')/IP(src='%s', dst='%s')/UDP(sport=11,dport=12)/('x'*18)], iface='%s', loop=1, inter=0.5)"
        sendp_cmd = sendp_fmt % (self.virio_mac, '1.1.1.1', '2.2.2.2', self.host_tintf)
        self.send_pks_session = self.tester.create_session("scapy1")
        self.send_pks_session.send_expect("scapy", ">>>")
        self.send_pks_session.send_command(sendp_cmd)

        if self.host_tintf != self.backup_tintf:
            sendp_cmd = sendp_fmt % {'DMAC': self.virio_mac, 'INTF': self.backup_tintf}
            self.send_pks_session2 = self.tester.create_session("scapy2")
            self.send_pks_session2.send_expect("scapy", ">>>")
            self.send_pks_session2.send_command(sendp_cmd)

    def stop_send_pkts_on_tester(self):
        self.tester.send_expect('pkill scapy', '# ')
        if getattr(self, "scapy1", None):
            self.tester.destroy_session(self.send_pks_session)
        if getattr(self, "scapy2", None):
            self.tester.destroy_session(self.send_pks_session2)

    def start_testpmd_on_vm(self, vm_dut):
        vm_dut.send_expect('export TERM=screen', '# ')
        vm_dut.send_expect('screen -S %s' % self.screen_name, '# ', 120)

        vm_testpmd = self.target + '/app/testpmd -c 0x3 -n 4 -- -i'
        vm_dut.send_expect(vm_testpmd, 'testpmd> ', 120)
        vm_dut.send_expect('set fwd rxonly', 'testpmd> ', 30)
        vm_dut.send_expect('set promisc all off', 'testpmd> ', 30)
        vm_dut.send_expect('start', 'testpmd> ', 30)
        vm_dut.send_command('^a')
        vm_dut.send_command('^d')

    def verify_dpdk(self, vm_dut):
        vm_dut.send_expect('export TERM=screen', '# ')
        vm_dut.send_command('screen -r %s' % self.screen_name)

        stats_pat = re.compile("RX-packets: (\d+)")
        vm_dut.send_expect("clear port stats all", "testpmd> ")
        time.sleep(5)
        out = vm_dut.send_expect("show port stats 0", "testpmd> ")
        print(out)
        m = stats_pat.search(out)
        if m:
            num_received = int(m.group(1))
        else:
            num_received = 0

        self.verify(num_received > 0, "Not receive packets as expected!!!")
        vm_dut.send_command('^a')
        vm_dut.send_command('^d')

    def verify_kernel(self, vm_dut):
        """
        Function to verify packets received by virtIO
        """
        vm_dut.send_expect('export TERM=screen', '# ')
        vm_dut.send_command('screen -r %s' % self.screen_name)
        # clean the output info before verify
        vm_dut.get_session_output(timeout=1)
        time.sleep(5)
        out = vm_dut.get_session_output(timeout=1)
        print(out)
        num = out.count('UDP')
        self.verify(num > 0, "Not receive packets as expected!!!")
        vm_dut.send_command('^a')
        vm_dut.send_command('^d')

    def start_tcpdump_on_vm(self, vm_dut):
        vm_dut.send_expect('export TERM=screen', '# ')
        vm_dut.send_expect('screen -S %s' % self.screen_name, '# ', 120)

        # get host interface
        vm_intf = vm_dut.ports_info[0]['port'].get_interface_name()
        # start tcpdump the interface
        vm_dut.send_expect("ifconfig %s up" % vm_intf, "# ")

        direct_pat = re.compile(r"(\s+)\[ (\S+) in\|out\|inout \]")
        vm_dut.send_expect("tcpdump -h", "# ")
        out = vm_dut.get_session_output(timeout=1)
        m = direct_pat.search(out)
        if m:
            direct_param = "-" + m.group(2)[1] + " in"
        else:
            direct_param = ""

        vm_dut.send_expect("tcpdump -i %s %s -v" % (vm_intf, direct_param), "listening on", 120)
        time.sleep(2)
        vm_dut.send_command('^a')
        vm_dut.send_command('^d')

    def send_and_verify(self, verify_fun, multi_queue=False):
        '''
        start to send packets
        verify vm_host can recevied packets before migration
        verify vm_host can recevied packets during migration
        verify vm_backup can recevied packets after migration
        '''
        # send packets from tester
        self.send_pkts_in_bg()

        # verify host virtio-net work fine
        verify_fun(self.vm_dut_host)

        self.logger.info("Migrate host VM to backup host")
        # start live migration
        ret = self.host_vm.start_migration(self.backup_dut_ip, self.backup_vm.migrate_port)
        self.verify(ret, "Failed to migration, please check VM and qemu version")

        if multi_queue is True:
            vm_intf = self.vm_dut_host.ports_info[0]['port'].get_interface_name()
            out = self.vm_dut_host.send_expect('ethtool -L %s combined 4' % vm_intf, '# ')
            self.verify('Error' not in out and 'Failed' not in out, 'ethtool set combined failed during migration')

        self.logger.info("Waiting migration process done")
        # wait live migration done
        self.host_vm.wait_migration_done()
        self.migration_done = True

        self.logger.info("Migration process done, then go to backup VM")
        # connected backup VM
        self.vm_dut_backup = self.backup_vm.migrated_start(set_target=False)

        # make sure still can receive packets
        verify_fun(self.vm_dut_backup)

    def test_migrate_with_split_ring_virtio_net(self):
        """
        Verify migrate virtIO device from host to backup host,
        Verify before/in/after migration, device with kernel driver can receive packets
        """
        self.queue_number = 1
        self.launch_testpmd_as_vhost_on_both_dut()
        self.start_testpmd_with_fwd_mode_on_both_dut()
        self.setup_vm_env_on_both_dut()

        # bind virtio-net back to virtio-pci
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="")
        # start screen and tcpdump on vm
        self.start_tcpdump_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_kernel)

    def test_adjust_split_ring_virtio_net_queue_numbers_while_migreting_with_virtio_net(self):
        self.queue_number = 4
        self.launch_testpmd_as_vhost_on_both_dut()
        self.start_testpmd_with_fwd_mode_on_both_dut()
        self.setup_vm_env_on_both_dut()

        # bind virtio-net back to virtio-pci
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="")
        self.start_tcpdump_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_kernel, True)

    def test_migrate_with_split_ring_virtio_pmd(self):
        self.queue_number = 1
        self.launch_testpmd_as_vhost_on_both_dut()
        self.start_testpmd_with_fwd_mode_on_both_dut()
        self.setup_vm_env_on_both_dut()

        # bind virtio-net to igb_uio
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="igb_uio")
        self.start_testpmd_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_dpdk)

    def test_migrate_with_split_ring_virtio_pmd_zero_copy(self):
        self.queue_number = 1
        zero_copy = True
        # start testpmd and qemu on dut
        # after qemu start ok, then send 'start' command to testpmd
        # if send 'start' command before start qemu, maybe qemu will start failed
        self.launch_testpmd_as_vhost_on_both_dut(zero_copy)
        self.setup_vm_env_on_both_dut()
        self.start_testpmd_with_fwd_mode_on_both_dut()

        # bind virtio-net to igb_uio
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="igb_uio")
        self.start_testpmd_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_dpdk)

    def test_migrate_with_packed_ring_virtio_pmd(self):
        self.queue_number = 1
        self.launch_testpmd_as_vhost_on_both_dut()
        self.start_testpmd_with_fwd_mode_on_both_dut()
        self.setup_vm_env_on_both_dut(packed=True)

        # bind virtio-net to igb_uio
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="igb_uio")
        self.start_testpmd_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_dpdk)

    def test_migrate_with_packed_ring_virtio_pmd_zero_copy(self):
        self.queue_number = 1
        zero_copy = True
        # start testpmd and qemu on dut
        # after qemu start ok, then send 'start' command to testpmd
        # if send 'start' command before start qemu, maybe qemu will start failed
        self.launch_testpmd_as_vhost_on_both_dut(zero_copy)
        self.setup_vm_env_on_both_dut(packed=True)
        self.start_testpmd_with_fwd_mode_on_both_dut()

        # bind virtio-net to igb_uio
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="igb_uio")
        self.start_testpmd_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_dpdk)

    def test_migrate_with_packed_ring_virtio_net(self):
        """
        Verify migrate virtIO device from host to backup host,
        Verify before/in/after migration, device with kernel driver can receive packets
        """
        self.queue_number = 1
        self.launch_testpmd_as_vhost_on_both_dut()
        self.start_testpmd_with_fwd_mode_on_both_dut()
        self.setup_vm_env_on_both_dut(packed=True)

        # bind virtio-net back to virtio-pci
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="")
        # start screen and tcpdump on vm
        self.start_tcpdump_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_kernel)

    def test_adjust_packed_ring_virtio_net_queue_numbers_while_migreting_with_virtio_net(self):
        self.queue_number = 4
        self.launch_testpmd_as_vhost_on_both_dut()
        self.start_testpmd_with_fwd_mode_on_both_dut()
        self.setup_vm_env_on_both_dut(packed=True)

        # bind virtio-net back to virtio-pci
        self.bind_nic_driver_of_vm(self.vm_dut_host, driver="")
        self.start_tcpdump_on_vm(self.vm_dut_host)

        self.send_and_verify(self.verify_kernel, True)

    def tear_down(self):
        self.destroy_vm_env()
        # stop send packet on tester
        self.stop_send_pkts_on_tester()
        self.duts[0].send_expect('killall -s INT qemu-system-x86_64', '#')
        self.duts[1].send_expect('killall -s INT qemu-system-x86_64', '#')
        pass

    def tear_down_all(self):
        self.dut.skip_setup = self.backup_speed
        pass

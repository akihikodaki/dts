# BSD LICENSE
#
# Copyright(c) <2019>, Intel Corporation. All rights reserved.
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
DPDK Test suite
Test DPDK vhost + virtio scenarios
"""
import os
import utils
import time
import subprocess
import binascii
from test_case import TestCase
from qemu_kvm import QEMUKvm
import cryptodev_common as cc
from packet import Packet

class VirtioCryptodevIpsecTest(TestCase):
    def set_up_all(self):
        self.sample_app = self.dut.apps_name['vhost_crypto']
        self.user_app = self.dut.apps_name['ipsec-secgw']
        self._default_ipsec_gw_opts = {
            "p": "0x3",
            "config": None,
            "f": "ipsec_test.cfg",
            "u": "0x1"
        }

        self.vm0, self.vm0_dut = None, None
        self.vm1, self.vm1_dut = None, None
        self.dut.skip_setup = True

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 4, 'Insufficient ports for test')
        self.cores = self.dut.get_core_list("1S/5C/1T")
        self.mem_channel = self.dut.get_memory_channels()
        self.port_mask = utils.create_mask([self.dut_ports[0]])
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])

        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.rx_port = self.tester.get_local_port(self.dut_ports[-1])

        self.tx_interface = self.tester.get_interface(self.tx_port)
        self.rx_interface = self.tester.get_interface(self.rx_port)

        self.logger.info("tx interface = " + self.tx_interface)
        self.logger.info("rx interface = " + self.rx_interface)

        self.sriov_port = self.bind_vfio_pci()

        if not cc.is_build_skip(self):
            self.dut.skip_setup = False
            cc.build_dpdk_with_cryptodev(self)
        cc.bind_qat_device(self)
        self.dut.build_dpdk_apps("./examples/vhost_crypto")
        self.bind_vfio_pci()

        self.launch_vhost_switch()

        self.vm0, self.vm0_dut = self.launch_virtio_dut("vm0")
        self.vm1, self.vm1_dut = self.launch_virtio_dut("vm1")

    def set_up(self):
        pass

    def dut_execut_cmd(self, cmdline, ex='#', timout=30):
        return self.dut.send_expect(cmdline, ex, timout)

    def build_user_dpdk(self, user_dut):
        user_dut.send_expect(
            "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=n$/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=y/' config/common_base", '#', 30)
        user_dut.send_expect(
            "sed -i 's/CONFIG_RTE_EAL_IGB_UIO=n/CONFIG_RTE_EAL_IGB_UIO=y/g' config/common_base", '#', 30)
        user_dut.set_build_options({'RTE_LIBRTE_PMD_AESNI_MB': 'y'})
        user_dut.build_install_dpdk(self.target)
        user_dut.build_dpdk_apps("./examples/ipsec-secgw")

    def get_vhost_eal(self):
        default_eal_opts = {
            "c": None,
            "l": ','.join(self.cores),
            "w": None,
            "vdev": None,
            "config": None,
            "socket-mem": "2048,0",
            "n": self.mem_channel
        }
        opts = default_eal_opts.copy()

        # Update options with test suite/case config file
        for key in list(opts.keys()):
            if key in self.get_suite_cfg():
                opts[key] = self.get_suite_cfg()[key]

        # Generate option string
        opt_str = ""
        for key,value in list(opts.items()):
            if value is None:
                continue
            dash = "-" if len(key) == 1 else "--"
            opt_str = opt_str + "{0}{1} {2} ".format(dash, key, value)

        return opt_str

    def cfg_prepare(self, dut):
        """
        ipsec configuration file
        """
        ep0 = (
            "#SP IPv4 rules\n"
            "sp ipv4 out esp protect 5 pri 1 dst 192.168.105.0/24 sport 0:65535 dport 0:65535\n"
            "sp ipv4 in esp protect 105 pri 1 dst 192.168.115.0/24 sport 0:65535 dport 0:65535\n"

            "#SA rules\n"
            "sa out 5 cipher_algo aes-128-cbc cipher_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 auth_algo sha1-hmac auth_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5\n"
            "sa in 105 cipher_algo aes-128-cbc cipher_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 auth_algo sha1-hmac auth_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 mode ipv4-tunnel src 172.16.2.5 dst 172.16.1.5\n"

            "#Routing rules\n"
            "rt ipv4 dst 172.16.2.5/32 port 0\n"
            "rt ipv4 dst 192.168.115.0/24 port 1\n")

        ep1 = (
            "#SP IPv4 rules\n"
            "sp ipv4 in esp protect 5 pri 1 dst 192.168.105.0/24 sport 0:65535 dport 0:65535\n"
            "sp ipv4 out esp protect 105 pri 1 dst 192.168.115.0/24 sport 0:65535 dport 0:65535\n"

            "#SA rules\n"
            "sa in 5 cipher_algo aes-128-cbc cipher_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 auth_algo sha1-hmac auth_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 mode ipv4-tunnel src 172.16.1.5 dst 172.16.2.5\n"
            "sa out 105 cipher_algo aes-128-cbc cipher_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 auth_algo sha1-hmac auth_key 0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0 mode ipv4-tunnel src 172.16.2.5 dst 172.16.1.5\n"

            "#Routing rules\n"
            "rt ipv4 dst 172.16.1.5/32 port 0\n"
            "rt ipv4 dst 192.168.105.0/24 port 1\n")

        self.set_cfg(dut, 'ep0.cfg', ep0)
        self.set_cfg(dut, 'ep1.cfg', ep1)

    def set_cfg(self, dut, filename, cfg):
        with open(filename, 'w') as f:
            f.write(cfg)

        dut.session.copy_file_to(filename, dut.base_dir)
        dut.session.copy_file_to(filename, dut.base_dir)

    def launch_vhost_switch(self):
        eal_opt_str = self.get_vhost_eal()

        config = '"(%s,0,0),(%s,0,0),(%s,0,0),(%s,0,0)"' % tuple(self.cores[-4:])
        socket_file = "%s,/tmp/vm0_crypto0.sock\
        --socket-file=%s,/tmp/vm0_crypto1.sock\
        --socket-file=%s,/tmp/vm1_crypto0.sock\
        --socket-file=%s,/tmp/vm1_crypto1.sock"% tuple(self.cores[-4:])
        self.vhost_switch_cmd = cc.get_dpdk_app_cmd_str(self.sample_app, eal_opt_str,
                                    '--config %s --socket-file %s' % (config, socket_file))
        self.dut_execut_cmd("rm -r /tmp/*")
        out = self.dut_execut_cmd(self.vhost_switch_cmd, "socket created", 30)
        self.logger.info(out)

    def bind_vfio_pci(self):
        self.vf_assign_method = "vfio-pci"
        self.dut.setup_modules(None, self.vf_assign_method, None)

        sriov_ports = []
        for port in self.dut.ports_info:
            port["port"].bind_driver("vfio-pci")
            sriov_ports.append(port["port"])
        return sriov_ports

    def set_virtio_pci(self, dut):
        out = dut.send_expect("lspci -d:1054|awk '{{print $1}}'", "# ", 10)
        virtio_list = out.replace("\r", "\n").replace("\n\n", "\n").split("\n")
        dut.send_expect('modprobe uio_pci_generic', '#', 10)
        for line in virtio_list:
            cmd = "echo 0000:{} > /sys/bus/pci/devices/0000\:{}/driver/unbind".format(
                line, line.replace(":", "\:"))
            dut.send_expect(cmd, "# ", 10)
        dut.send_expect('echo "1af4 1054" > /sys/bus/pci/drivers/uio_pci_generic/new_id', "# ", 10)

        return virtio_list

    def launch_virtio_dut(self, vm_name):
        vm = QEMUKvm(self.dut, vm_name, 'virtio_ipsec_cryptodev_func')
        if vm_name == "vm0":
            vf0 = {'opt_host': self.sriov_port[0].pci}
            vf1 = {'opt_host': self.sriov_port[1].pci}
        elif vm_name == "vm1":
            vf0 = {'opt_host': self.sriov_port[2].pci}
            vf1 = {'opt_host': self.sriov_port[3].pci}

        vm.set_vm_device(driver=self.vf_assign_method, **vf0)
        vm.set_vm_device(driver=self.vf_assign_method, **vf1)
        skip_setup = self.dut.skip_setup

        try:
            self.dut.skip_setup = True
            vm_dut = vm.start()
            if vm_dut is None:
                print(('{} start failed'.format(vm_name)))
        except Exception as err:
            raise err

        self.dut.skip_setup = skip_setup
        vm_dut.restore_interfaces()

        if not self.dut.skip_setup:
            self.build_user_dpdk(vm_dut)

        vm_dut.setup_modules(self.target, "igb_uio", None)
        vm_dut.bind_interfaces_linux('igb_uio')
        vm.virtio_list = self.set_virtio_pci(vm_dut)
        self.logger.info("{} virtio list: {}".format(vm_name, vm.virtio_list))
        vm.cores = vm_dut.get_core_list("all")
        self.logger.info("{} core list: {}".format(vm_name, vm.cores))
        vm.ports = [port["pci"] for port in vm_dut.ports_info]
        self.logger.info("{} port list: {}".format(vm_name, vm.ports))
        self.cfg_prepare(vm_dut)

        return vm, vm_dut

    def send_and_dump_pkg(self):
        status = True

        inst = self.tester.tcpdump_sniff_packets(self.rx_interface)

        PACKET_COUNT = 65
        payload = 256 * ['11']

        pkt = Packet()
        pkt.assign_layers(["ether", "ipv4", "udp", "raw"])
        pkt.config_layer("ether", {"src": "52:00:00:00:00:00", "dst": "52:00:00:00:00:01"})
        src_ip = "192.168.105.200"
        dst_ip = "192.168.105.100"
        pkt.config_layer("ipv4", {"src": src_ip, "dst": dst_ip})
        pkt.config_layer("udp", {"src": 1111, "dst": 2222})
        pkt.config_layer("raw", {"payload": payload})
        pkt.send_pkt(self.tester, tx_port=self.tx_interface, count=PACKET_COUNT)
        pkt_rec = self.tester.load_tcpdump_sniff_packets(inst)

        self.logger.info("dump: {} packets".format(len(pkt_rec)))
        if len(pkt_rec) != PACKET_COUNT:
            self.logger.info("dump pkg: {}, the num of pkg dumped is incorrtct!".format(len(pkt_rec)))
            status = False
        for i in range(len(pkt_rec)):
            if src_ip != pkt_rec.pktgen.strip_layer3("src", p_index=i) or dst_ip != pkt_rec.pktgen.strip_layer3("dst", p_index=i):
                self.logger.info("the ip of pkg dumped is incorrtct!")
                status = False

            dump_text = str(binascii.b2a_hex(pkt_rec[i]["Raw"].getfieldval("load")), encoding='utf-8')
            if dump_text != ''.join(payload):
                self.logger.info(dump_text)
                self.logger.info(''.join(payload))
                self.logger.info("the text of pkg dumped is incorrtct!")
                status = False

        return status

    def test_aesni_mb_aes_cbc_sha1_hmac(self):
        if cc.is_test_skip(self):
            return

        eal_opt_str_0 = cc.get_eal_opt_str(self, {"l": ','.join(self.vm0.cores[-3:]),
                                                "socket-mem":"512,0",
                                                "w": " -w ".join(self.vm0.ports),
                                                "vdev":"crypto_aesni_mb_pmd_1 --vdev crypto_aesni_mb_pmd_2"})

        crypto_ipsec_opt_str0 = cc.get_opt_str(self, self._default_ipsec_gw_opts, override_opts={'f': "/root/dpdk/ep0.cfg", "config": '"(0,0,%s),(1,0,%s)"' % tuple(self.vm0.cores[-2:])})

        out0 = self._run_crypto_ipsec(self.vm0_dut, eal_opt_str_0, crypto_ipsec_opt_str0)
        self.logger.info(out0)

        eal_opt_str_1 = cc.get_eal_opt_str(self, {"l": ','.join(self.vm1.cores[-3:]),
                                                "socket-mem":"512,0",
                                                "w": " -w ".join(self.vm1.ports),
                                                "vdev": "crypto_aesni_mb_pmd_1 --vdev crypto_aesni_mb_pmd_2"})

        crypto_ipsec_opt_str1 = cc.get_opt_str(self, self._default_ipsec_gw_opts, override_opts={'f': "/root/dpdk/ep1.cfg", "config": '"(0,0,%s),(1,0,%s)"' % tuple(self.vm1.cores[-2:])})
        out1 = self._run_crypto_ipsec(self.vm1_dut, eal_opt_str_1, crypto_ipsec_opt_str1)
        self.logger.info(out1)

        result = self.send_and_dump_pkg()
        self.verify(result, "FAILED")

    def test_virtio_aes_cbc_sha1_hmac(self):
        if cc.is_test_skip(self):
            return

        eal_opt_str_0 = cc.get_eal_opt_str(self, {"l": ','.join(self.vm0.cores[-3:]),
                                                "socket-mem":"512,0",
                                                "w": " -w ".join(self.vm0.ports + self.vm0.virtio_list),
                                                "vdev":None})

        crypto_ipsec_opt_str0 = cc.get_opt_str(self, self._default_ipsec_gw_opts, override_opts={'f': "/root/dpdk/ep0.cfg", "config": '"(0,0,%s),(1,0,%s)"' % tuple(self.vm0.cores[-2:])})
        out0 = self._run_crypto_ipsec(self.vm0_dut, eal_opt_str_0, crypto_ipsec_opt_str0)
        self.logger.info(out0)

        eal_opt_str_1 = cc.get_eal_opt_str(self, {"l": ','.join(self.vm1.cores[-3:]),
                                                "socket-mem":"512,0",
                                                "w": " -w ".join(self.vm1.ports + self.vm1.virtio_list),
                                                "vdev": None})

        crypto_ipsec_opt_str1 = cc.get_opt_str(self, self._default_ipsec_gw_opts, override_opts={'f': "/root/dpdk/ep1.cfg", "config": '"(0,0,%s),(1,0,%s)"' % tuple(self.vm1.cores[-2:])})
        out1 = self._run_crypto_ipsec(self.vm1_dut, eal_opt_str_1, crypto_ipsec_opt_str1)
        self.logger.info(out1)

        result = self.send_and_dump_pkg()
        self.verify(result, "FAILED")

    def _run_crypto_ipsec(self, vm_dut, eal_opt_str, case_opt_str):
        cmd_str = cc.get_dpdk_app_cmd_str(self.user_app,
                                          eal_opt_str,
                                          case_opt_str + " -l")
        self.logger.info(cmd_str)
        try:
            out = vm_dut.send_expect(cmd_str, "IPSEC", 600)
        except Exception as ex:
            self.logger.error(ex)
            raise ex

        return out

    def tear_down(self):
        self.vm0_dut.send_expect("^C", "# ")
        self.vm1_dut.send_expect("^C", "# ")

    def tear_down_all(self):
        if getattr(self, 'vm0', None):
            self.vm0_dut.kill_all()
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, 'vm1', None):
            self.vm1_dut.kill_all()
            self.vm1.stop()
            self.vm1 = None

        if self.vm1:
            self.vm1.stop()
            self.dut.virt_exit()
            self.vm1 = None

        self.dut_execut_cmd("^C", "# ")
        self.app_name = self.sample_app[self.sample_app.rfind('/')+1:]
        self.dut.send_expect("killall -s INT %s" % self.app_name, "#")
        self.dut_execut_cmd("killall -s INT qemu-system-x86_64")
        self.dut_execut_cmd("rm -r /tmp/*")

        cc.clear_dpdk_config(self)

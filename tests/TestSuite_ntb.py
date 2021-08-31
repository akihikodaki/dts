# BSD LICENSE
#
# Copyright(c) <2020> Intel Corporation.
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

import os
import re
import time
from test_case import TestCase
from net_device import GetNicObj
from settings import HEADER_SIZE
from packet import Packet
from pktgen import PacketGeneratorHelper

class TestNtb(TestCase):

    def set_up_all(self):
        self.verify(len(self.duts) >= 2, "Insufficient duts for NTB!!!")
        self.ntb_host = self.duts[0]
        self.ntb_client = self.duts[1]

        # each dut required one ports
        self.verify(len(self.ntb_host.get_ports()) >= 1 and
                len(self.ntb_client.get_ports()) >= 1,
                "Insufficient ports for testing")

        self.host_port = self.ntb_host.get_ports()[0]
        self.client_port = self.ntb_client.get_ports()[0]
        self.host_mac = self.ntb_host.get_mac_address(self.host_port)
        self.client_mac = self.ntb_client.get_mac_address(self.client_port)

        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.header_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + HEADER_SIZE['udp']
        self.pktgen_helper = PacketGeneratorHelper()

        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        out = self.ntb_host.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.ntb_host.send_expect('mkdir -p %s' % self.out_path, '# ')

        self.prepare_dpdk_app(self.ntb_host)
        self.prepare_dpdk_app(self.ntb_client)

    def set_up(self):
        pass

    def create_table(self, index=1):
        self.table_header = ["FrameSize(B)", "Throughput(Mpps)", "% linerate"]
        self.result_table_create(self.table_header)

    def prepare_dpdk_app(self, crb):
        out = crb.send_expect("ls ./" + crb.target + "/kmod/igb_uio.ko", "#", 10)
        if "No such file or directory" in out:
            crb.build_install_dpdk(crb.target)

        out = crb.build_dpdk_apps("./examples/ntb")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

    def get_core_list(self):
        core_number = 5
        core_config = '1S/{}C/1T'.format(core_number)
        self.host_core_list = self.ntb_host.get_core_list(core_config)
        self.client_core_list = self.ntb_client.get_core_list(core_config)
        self.verify(len(self.host_core_list) >= core_number and len(self.client_core_list) >= core_number,
                    'There have not enough cores to start testpmd on duts')

    def get_ntb_port(self, crb):
        device = crb.send_expect("lspci -D | grep Non-Transparent |awk '{{print $1}}'", "# ", 10)
        self.verify(device, "Falied to find ntb device")
        addr_array = device.strip().split(':')
        domain_id = addr_array[0]
        bus_id = addr_array[1]
        devfun_id = addr_array[2]
        port = GetNicObj(crb, domain_id, bus_id, devfun_id)
        return port

    def set_driver(self, driver=""):
        self.ntb_host.restore_interfaces()
        self.ntb_client.restore_interfaces()

        for crb in [self.ntb_host, self.ntb_client]:
            crb.setup_modules(crb.target, driver, None)
            if driver == "igb_uio":
                crb.send_expect("rmmod -f igb_uio", "#", 30)
                crb.send_expect("insmod ./" + crb.target + "/kmod/igb_uio.ko wc_activate=1", "#", 30)
            if driver == "vfio-pci":
                crb.send_expect("echo 'base=0x39bfa0000000 size=0x400000 type=write-combining' >> /proc/mtrr", "#", 10)
                crb.send_expect("echo 'base=0x39bfa0000000 size=0x4000000 type=write-combining' >> /proc/mtrr", "#", 10)

    def port_bind_driver(self, driver=""):
        self.ntb_host.bind_interfaces_linux(driver=driver)
        self.ntb_client.bind_interfaces_linux(driver=driver)

    def ntb_bind_driver(self, driver=""):
        ntb = self.get_ntb_port(self.ntb_host)
        ntb.bind_driver(driver)

        ntb = self.get_ntb_port(self.ntb_client)
        ntb.bind_driver(driver)

    def launch_ntb_fwd(self, **param):
        """
        launch ntb_fwd on ntb host and ntb client
        """
        cmd_opt = " ".join(["{}={}".format(key, param[key]) for key in param.keys()])

        self.get_core_list()
        app = self.dut.apps_name['ntb']
        eal_host = self.ntb_host.create_eal_parameters(cores=self.host_core_list)
        eal_client = self.ntb_client.create_eal_parameters(cores=self.client_core_list)
        host_cmd_line = ' '.join([app, eal_host, cmd_opt])
        client_cmd_line = ' '.join([app, eal_client, cmd_opt])
        self.ntb_host.send_expect(host_cmd_line, 'Checking ntb link status', 30)
        self.ntb_client.send_expect(client_cmd_line, 'ntb>', 30)
        time.sleep(3)
        #self.ntb_host.send_expect(" ", 'ntb> ', 10)
        #self.ntb_client.send_expect(" ", 'ntb> ', 10)

    def start_ntb_fwd_on_dut(self, crb, fwd_mode='io'):
        crb.send_expect('set fwd %s' % fwd_mode, 'ntb> ', 30)
        crb.send_expect('start', 'ntb> ', 30)

    def config_stream(self, frame_size):
        payload = frame_size - self.header_size
        tgen_input = []

        for i, each_mac in enumerate([self.host_mac, self.client_mac]):
            flow = 'Ether(dst="%s")/IP(dst="192.168.%d.1", proto=255)/UDP()/Raw(b"%s")' % (each_mac, i, "X"*payload)
            pcap = os.path.join(self.out_path, "ntb_%d_%d.pcap" %
                    (i, frame_size))
            self.tester.scapy_append("flow=" + flow)
            self.tester.scapy_append("wrpcap('%s', flow)" % pcap)
            self.tester.scapy_execute()
            tgen_input.append((i, (i+1)%2, pcap))

        return tgen_input

    def calculate_avg_throughput(self, frame_size, tgen_input):
        """
        send packet and get the throughput
        """
        # set traffic option
        traffic_opt = {'delay': 5}

        # clear streams before add new streams
        self.tester.pktgen.clear_streams()

        # run packet generator
        fields_config = {'ip': {'dst': {'action': 'random'}, }, }
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                                            fields_config, self.tester.pktgen)
        _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)

        Mpps = pps / 1000000.0

        throughput = Mpps * 100 / \
                    float(self.wirespeed(self.nic, frame_size, 1))
        return Mpps, throughput

    def get_packets_of_each_port(self, crb):
        out = crb.send_expect('show port stats', 'ntb> ', 10)
        info = re.findall("statistics for NTB port", out)
        index = out.find(info[0])
        tx = re.search("Tx-packets:\s*(\d*)", out[index:])
        rx = re.search("Rx-packets:\s*(\d*)", out[index:])
        rx_packets = int(rx.group(1))
        tx_packets = int(tx.group(1))
        self.logger.info("tx-packets:%d, rx-packets:%d" %
                (tx_packets, rx_packets))
        return tx_packets, rx_packets

    def check_packets_for_iofwd(self):
        """
        check transmit/receive packets for iofwd mode
        """
        tx, rx = self.get_packets_of_each_port(self.ntb_host)
        self.verify(tx > 0 and rx > 0,
                "tx-packets:%d, rx-packets:%d" % (tx, rx))

        tx, rx = self.get_packets_of_each_port(self.ntb_client)
        self.verify(tx > 0 and rx > 0,
                "tx-packets:%d, rx-packets:%d" % (tx, rx))

    def check_packets_for_rxtx(self):
        """
        check transmit/receive packets for rxonly and txonly mode
        """
        tx, rx = self.get_packets_of_each_port(self.ntb_host)
        self.verify(tx == 0 and rx > 0,
                "tx-packets:%d, rx-packets:%d" % (tx, rx))

        tx, rx = self.get_packets_of_each_port(self.ntb_client)
        self.verify(tx > 0 and rx == 0,
                "tx-packets:%d, rx-packets:%d" % (tx, rx))

    def send_file_and_verify(self):
        # Send file from host
        src_file = "{}/ntb.txt".format(self.out_path)
        base_dir = self.ntb_client.base_dir.replace('~', '/root')
        dst_file = "{}/ntb_recv_file0".format(base_dir)
        content = "ntb!123"
        self.ntb_client.alt_session.send_expect("rm {}".format(dst_file), '# ')
        self.ntb_host.alt_session.send_expect("echo '{}' >{}".format(content, src_file), '# ')
        self.ntb_host.send_expect('send {}'.format(src_file), 'ntb> ', 30)
        time.sleep(3)

        # Check file received on client.
        cnt = self.ntb_client.alt_session.send_expect('cat %s' % dst_file, '# ')
        self.verify(cnt == content, "the content can't match with the sent")

    def send_pkg_and_verify(self):
        for frame_size in self.frame_sizes:
            info = "Running test: %s, frame size: %d." % (self.running_case, frame_size)
            self.logger.info(info)
            self.ntb_host.send_expect("stop", "ntb> ", 60)
            self.ntb_host.send_expect("start", "ntb> ", 60)
            self.ntb_client.send_expect("stop", "ntb> ", 60)
            self.ntb_client.send_expect("start", "ntb> ", 60)
            time.sleep(1)

            result = [frame_size]
            tgen_input = self.config_stream(frame_size)
            Mpps, throughput = self.calculate_avg_throughput(frame_size, tgen_input)
            result.append(Mpps)
            result.append(throughput)

            self.check_packets_for_iofwd()
            self.update_table_info(result)

    def test_file_tran_mode_and_igb_uio(self):
        driver = "igb_uio"
        self.set_driver(driver)
        self.ntb_bind_driver(driver)

        self.launch_ntb_fwd(**{"buf-size": 65407})
        self.start_ntb_fwd_on_dut(self.ntb_host, fwd_mode="file-trans")
        self.start_ntb_fwd_on_dut(self.ntb_client, fwd_mode="file-trans")
        self.send_file_and_verify()

    def test_file_tran_mode_and_vfio_pci(self):
        driver = "vfio-pci"
        self.set_driver(driver)
        self.ntb_bind_driver(driver)

        self.launch_ntb_fwd(**{"buf-size": 65407})
        self.start_ntb_fwd_on_dut(self.ntb_host, fwd_mode="file-trans")
        self.start_ntb_fwd_on_dut(self.ntb_client, fwd_mode="file-trans")
        self.send_file_and_verify()

    def test_pkt_rxtx_mode_and_igb_uio(self):
        driver = "igb_uio"
        self.set_driver(driver)
        self.ntb_bind_driver(driver)

        self.launch_ntb_fwd(**{"buf-size": 65407})
        self.start_ntb_fwd_on_dut(self.ntb_host, fwd_mode="rxonly")
        self.start_ntb_fwd_on_dut(self.ntb_client, fwd_mode="txonly")
        time.sleep(1)
        self.check_packets_for_rxtx()

    def test_pkt_rxtx_mode_and_vfio_pci(self):
        driver = "vfio-pci"
        self.set_driver(driver)
        self.ntb_bind_driver(driver)

        self.launch_ntb_fwd(**{"buf-size": 65407})
        self.start_ntb_fwd_on_dut(self.ntb_host, fwd_mode="rxonly")
        self.start_ntb_fwd_on_dut(self.ntb_client, fwd_mode="txonly")
        time.sleep(1)
        self.check_packets_for_rxtx()

    def test_perf_iofwd_mode_and_igb_uio(self):
        driver = "igb_uio"
        self.set_driver(driver)
        self.ntb_bind_driver(driver)
        self.port_bind_driver(driver)

        self.create_table()
        self.launch_ntb_fwd(**{"burst": 32})
        self.start_ntb_fwd_on_dut(self.ntb_host, fwd_mode="iofwd")
        self.start_ntb_fwd_on_dut(self.ntb_client, fwd_mode="iofwd")
        self.send_pkg_and_verify()

        self.result_table_print()

    def test_perf_iofwd_mode_and_vfio_pci(self):
        driver = "vfio-pci"
        self.set_driver(driver)
        self.ntb_bind_driver(driver)
        self.port_bind_driver(driver)

        self.create_table()
        self.launch_ntb_fwd(**{"burst": 32})
        self.start_ntb_fwd_on_dut(self.ntb_host, fwd_mode="iofwd")
        self.start_ntb_fwd_on_dut(self.ntb_client, fwd_mode="iofwd")
        self.send_pkg_and_verify()

        self.result_table_print()

    def update_table_info(self, *param):
        for each in param:
            self.result_table_add(each)

    def tear_down(self):
        self.ntb_host.send_expect('quit', '# ', 30)
        self.ntb_client.send_expect('quit', '# ', 30)

    def tear_down_all(self):
        self.ntb_host.kill_all()
        self.ntb_client.kill_all()

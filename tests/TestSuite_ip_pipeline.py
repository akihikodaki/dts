# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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
Test userland 10Gb PMD
"""

from scapy.layers.inet import Ether, IP, TCP
from scapy.utils import struct, socket, PcapWriter
from settings import HEADER_SIZE
from test_case import TestCase
from time import sleep
import utils


class TestIPPipeline(TestCase):
    payload_watermark = 'TestPF'

    frame_sizes = [64, 65, 128, 1024]
    """Sizes of the frames to be sent"""

    number_of_frames = [1, 3, 63, 64, 65, 127, 128]
    """Number of frames in the pcap file to be created"""

    incremental_ip_address = [True, False]
    """True if the IP address is incremented in the frames"""

    inter = [0, 0.7]
    """Interval between frames sent in seconds"""

    dummy_pcap = 'dummy.pcap'

    def increment_ip_addr(self, ip_address, increment):

        ip2int = lambda ipstr: struct.unpack('!I', socket.inet_aton(ipstr))[0]
        x = ip2int(ip_address)
        int2ip = lambda n: socket.inet_ntoa(struct.pack('!I', n))
        return int2ip(x + increment)

    def create_tcp_ipv4_frame(
        self, ip_id, src_ip_addr, dst_ip_addr, frame_size,
        src_mac_addr='00:00:0A:00:0B:00',
            dst_mac_addr='00:00:0A:00:0A:00'):

        payload_size = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] -\
            HEADER_SIZE['tcp'] - \
            len(TestIPPipeline.payload_watermark)

        if payload_size < 0:
            payload_size = 0

        frame = Ether() / IP() / TCP(flags="") / (TestIPPipeline.payload_watermark +
                                                  "X" * payload_size)
        frame[Ether].src = src_mac_addr
        frame[Ether].dst = dst_mac_addr

        frame[IP].src = src_ip_addr
        frame[IP].dst = dst_ip_addr
        frame[IP].id = ip_id

        # TCP ports always 0
        frame[TCP].sport = 0
        frame[TCP].dport = 0

        return frame

    def create_pcap_file_from_frames(self, file_name, frames):

        writer = PcapWriter(file_name, append=False)

        for frame in frames:
            writer.write(frame)

        writer.close()

    def create_pcap_file(self, file_name, frame_size, number_of_frames,
                         incremental_ip_address,
                         src_ip="0.0.0.0",
                         dst_ip="0.0.0.0"):

        current_frame = 0
        writer = PcapWriter(file_name, append=False)

        while current_frame < number_of_frames:
            ip_id = 0  # current_frame % 0x10000

            frame = self.create_tcp_ipv4_frame(ip_id, src_ip, dst_ip,
                                               frame_size)
            writer.write(frame)

            if incremental_ip_address:
                dst_ip = self.increment_ip_addr(dst_ip, 1)

            current_frame += 1

        writer.close()

    def create_passthrough_cfgfile(self):
        """
        Create configuration file for passthrough pipeline.
        Two ports are connected as follows: RXQ0.0 -> TXQ1.0, RXQ1.0 -> TXQ0.0.
        """

        self.dut.send_expect('echo [PIPELINE0] > /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo type = MASTER >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo core = 0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo [PIPELINE1] >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo type = PASS-THROUGH >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo core = 1 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo pktq_in = RXQ0.0 RXQ1.0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo pktq_out = TXQ1.0 TXQ0.0 >> /tmp/ip_pipeline.cfg', '#')

    def create_routing_cfgfile(self):
        """
        Create configuration file for ip routing pipeline.
        It is mainly to set ip header offset and arp key offset in the packet buffer.
        """

        self.dut.send_expect('echo [PIPELINE0] > /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo type = MASTER >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo core = 0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo [PIPELINE1] >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo type = ROUTING >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo core = 1 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo pktq_in = RXQ0.0 RXQ1.0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo pktq_out = TXQ0.0 TXQ1.0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo encap = ethernet >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo ip_hdr_offset = 270 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo arp_key_offset = 128 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo n_arp_entries = 1000 >> /tmp/ip_pipeline.cfg', '#')

    def create_flow_cfgfile(self):
        """
        Create configuration file for flow classification pipeline.
        It is mainly to set key size, offset and mask to get the ipv4 5-tuple.
        """

        self.dut.send_expect('echo [PIPELINE0] > /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo type = MASTER >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo core = 0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo [PIPELINE1] >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo type = FLOW_CLASSIFICATION >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo core = 1 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo pktq_in = RXQ0.0 RXQ1.0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo pktq_out = TXQ0.0 TXQ1.0 SINK0 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo n_flows = 65536 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo key_size = 16 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo key_offset = 278 >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo key_mask = 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF >> /tmp/ip_pipeline.cfg', '#')
        self.dut.send_expect('echo flowid_offset = 128 >> /tmp/ip_pipeline.cfg', '#')

    def start_ip_pipeline(self, ports):
        command_line = "./examples/ip_pipeline/build/ip_pipeline -p %s -f /tmp/ip_pipeline.cfg" % ports

        out = self.dut.send_expect(command_line, 'pipeline>', 60)
        sleep(5)    # 'Initialization completed' is not the last output, some
        # seconds are still needed for init.

        self.verify("Aborted" not in out, "Error starting ip_pipeline")
        self.verify("PANIC" not in out, "Error starting ip_pipeline")
        self.verify("ERROR" not in out, "Error starting ip_pipeline")

    def quit_ip_pipeline(self):
        self.dut.send_expect("quit", "# ", 5)

    def tcpdump_start_sniffing(self, ifaces=[]):
        """
        Starts tcpdump in the background to sniff the tester interface where
        the packets are transmitted to and from the self.dut.
        All the captured packets are going to be stored in a file for a
        post-analysis.
        """

        for iface in ifaces:
            command = ('rm -f tcpdump_{0}.pcap').format(iface)
            self.tester.send_expect(command, '#')
            command = (
                'tcpdump -w tcpdump_{0}.pcap -i {0} 2>tcpdump_{0}.out &').format(iface)
            self.tester.send_expect(command, '#')

    def tcpdump_stop_sniff(self):
        """
        Stops the tcpdump process running in the background.
        """

        self.tester.send_expect('killall tcpdump', '#')
        # For the [pid]+ Done tcpdump... message after killing the process
        sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', '#')
        sleep(1)

    def tcpdump_command(self, command, machine):
        """
        Sends a tcpdump related command and returns an integer from the output
        """

        if machine == 'dut':
            result = self.dut.send_expect(command, '#', alt_session=True)
        else:
            result = self.tester.send_expect(command, '#', alt_session=True)

        return int(result.strip())

    def number_of_packets(self, file_name, machine='tester'):
        """
        By reading the file generated by tcpdump it counts how many packets were
        forwarded by the sample app and received in the self.tester. The sample app
        will add a known MAC address for the test to look for.
        """

        command = ('tcpdump -A -nn -e -v -r %s 2>/dev/null | grep -c "%s"' %
                   (file_name, TestIPPipeline.payload_watermark))
        return int(self.tcpdump_command(command, machine))

    def send_and_sniff_pcap_file(self, pcap_file, frames_number, from_port,
                                 to_port, inter=0):
        """
        Sent frames_number frames from the pcap_file with inter seconds of
        interval.
        Returns the number of received frames.
        """

        tx_port = self.tester.get_local_port(self.dut_ports[from_port])
        rx_port = self.tester.get_local_port(self.dut_ports[to_port])
        port0 = self.tester.get_local_port(self.dut_ports[0])

        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)

        self.tcpdump_start_sniffing([tx_interface, rx_interface])

        timeout = frames_number * inter + 2
        inter = ", inter=%d" % inter

        # Prepare the frames to be sent
        self.tester.scapy_foreground()
        self.tester.scapy_append('p = rdpcap("%s")' % (pcap_file))
        self.tester.scapy_append(
            'sendp(p[:%s], iface="%s" %s)' % (frames_number,
                                              tx_interface,
                                              inter))

        # Execute scapy to sniff sniffing and send the frames
        self.tester.scapy_execute(timeout)

        self.tcpdump_stop_sniff()

        rx_stats = self.number_of_packets('tcpdump_%s.pcap' % rx_interface)
        tx_stats = self.number_of_packets('tcpdump_%s.pcap' % tx_interface)

        # Do not count the sent frames in the tx_interface
        tx_stats = tx_stats - frames_number

        if port0 == tx_port:
            return {'rx0': tx_stats, 'rx1': rx_stats}
        else:
            return {'rx0': rx_stats, 'rx1': tx_stats}

    def check_results(self, stats, expected):
        """
        This function check that the received packet numbers of port0 and port1 match the expected.
        expected = [Rx0, Rx1]
        """

        for port in ['rx0', 'rx1']:
            self.verify(stats[port] == expected[port],
                        'Frames expected (%s) and received (%s) mismatch on %s port' % (
                expected[port], stats[port], port))

    def pipeline_command(self, command):
        out = self.dut.send_expect(command, 'pipeline>')
        self.verify("arguments" not in out, "Incorrect arguments: '%s'" % command)
        self.verify("Invalid" not in out, "Invalid argument: '%s'" % command)
        self.verify("Syntax error" not in out, "Syntax error: '%s'" % command)
        return out

    def pipeline_add_flow(self, port, src_ip, dst_ip, src_port, dst_port, flowid,
                          protocol=6):
        command = 'p 1 flow add ipv4 %s %s %d %d %d port %d id %d' % (src_ip, dst_ip, src_port,
                                                  dst_port, protocol, port, flowid)
        out = self.pipeline_command(command)
        self.verify("failed" not in out, "Add flow error")

    def pipeline_del_flow(self, src_ip, dst_ip, src_port, dst_port,
                          protocol=6):
        command = 'p 1 flow del ipv4 %s %s %d %d %d' % (src_ip, dst_ip, src_port,
                                               dst_port, protocol)
        out = self.pipeline_command(command)
        self.verify("failed" not in out, "Del flow error")

    def pipeline_add_route(self, port, src_ip, netmask, gw_ip):
        command = 'p 1 route add %s %d port %d ether %s' % (src_ip, netmask, port, gw_ip)
        out = self.pipeline_command(command)
        self.verify("failed" not in out, "Add route error")

    def pipeline_del_route(self, src_ip, netmask):
        command = 'p 1 route del %s %d' % (src_ip, netmask)
        out = self.pipeline_command(command)
        self.verify("failed" not in out, "Del route error")

    def set_up_all(self):
        """
        Run at the start of each test suite.

        PMD prerequisites.
        """

        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2,
                    "Insufficient ports for speed testing")

        out = self.dut.build_dpdk_apps("./examples/ip_pipeline")
        self.verify("Error" not in out, "Compilation error")

        self.ports_mask = utils.create_mask(
            [self.dut_ports[0], self.dut_ports[1]])
        self.coremask = "0x3e"  # IP Pipeline app requires FIVE cores

        self.dut.setup_memory(4096)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_incremental_ip(self):
        """
        Testing that frames with incremental IP addresses pass through the
        pipeline regardless the frames_number and the speed.
        """
        pcap_file = 'ip_pipeline.pcap'
        frame_size = 64

        self.create_passthrough_cfgfile()
        self.start_ip_pipeline(ports=self.ports_mask)
        self.dut.send_expect(
            'run examples/ip_pipeline/config/ip_pipeline.sh', 'pipeline>', 10)

        # Create a PCAP file containing the maximum frames_number of frames needed
        # with fixed size and incremental IP
        self.create_pcap_file(pcap_file, frame_size,
                              max(TestIPPipeline.number_of_frames), True)
        self.tester.session.copy_file_to(pcap_file)

        for frames_number in TestIPPipeline.number_of_frames:
            for inter in TestIPPipeline.inter:
                print utils.BLUE(
                    "\tNumber of frames %d, interval %.1f" % (frames_number,
                                                              inter))
                stats = self.send_and_sniff_pcap_file(pcap_file, frames_number,
                                                      1, 0, inter)

                expected = {'rx0': frames_number, 'rx1': 0}
                self.check_results(stats, expected)

                stats = self.send_and_sniff_pcap_file(pcap_file, frames_number,
                                                      0, 1, inter)

                expected = {'rx0': 0, 'rx1': frames_number}
                self.check_results(stats, expected)

    def test_frame_sizes(self):
        """
        Testing that frames with different sizes pass through the pipeline.
        """
        pcap_file = 'ip_pipeline.pcap'
        frames_number = 100
        inter = 0.5

        self.create_passthrough_cfgfile()
        self.start_ip_pipeline(ports=self.ports_mask)
        self.dut.send_expect(
            'run examples/ip_pipeline/config/ip_pipeline.sh', 'pipeline>', 10)

        for frame_size in TestIPPipeline.frame_sizes:

            # Create a PCAP file containing the fixed number of frames above
            # with variable size and incremental IP
            self.create_pcap_file(pcap_file, frame_size, 100, True)
            self.tester.session.copy_file_to(pcap_file)

            print utils.BLUE("\tFrame size %d, interval %.1f" % (frame_size,
                                                               inter))

            stats = self.send_and_sniff_pcap_file(pcap_file, frames_number,
                                                  1, 0, inter)

            expected = {'rx0': frames_number, 'rx1': 0}
            self.check_results(stats, expected)

            stats = self.send_and_sniff_pcap_file(pcap_file, frames_number,
                                                  0, 1, inter)

            expected = {'rx0': 0, 'rx1': frames_number}
            self.check_results(stats, expected)

    def test_flow_management(self):
        """
        Add several flows and check only frames with matching IPs passes
        """
        pcap_file = 'ip_pipeline.pcap'
        frame_size = 64

        ip_addrs = [
            '0.0.0.0', '0.0.0.1', '0.0.0.127', '0.0.0.128', '0.0.0.255',
            '0.0.1.0', '0.0.127.0', '0.0.128.0', '0.0.129.0', '0.0.255.0',
            '0.127.0.0', '0.127.1.0', '0.127.127.0', '0.127.255.0',
            '0.127.255.255']

        frames = []

        for addr in ip_addrs:
            frames.append(self.create_tcp_ipv4_frame(0, '0.0.0.0', addr,
                                                     frame_size))

        self.create_flow_cfgfile()
        self.create_pcap_file_from_frames(pcap_file, frames)
        self.tester.session.copy_file_to(pcap_file)

        # Start ip_pipeline app and setup defaults
        self.start_ip_pipeline(ports=self.ports_mask)

        # default to SINK0
        self.pipeline_command('p 1 flow add default 2')

        # Check that no traffic pass though
        stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                              1, 0, 0.2)
        expected = {'rx0': 0, 'rx1': 0}
        self.check_results(stats, expected)

        # Add the flows
        flows_added = 0
        for addrs in ip_addrs:
            self.pipeline_add_flow(0, '0.0.0.0', addrs, 0, 0, flows_added)
            flows_added += 1

            # Check that traffic matching flows pass though
            stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                                  1, 0, 0.2)
            expected = {'rx0': flows_added, 'rx1': 0}
            self.check_results(stats, expected)

        # Remove flows
        for addrs in ip_addrs:
            self.pipeline_del_flow('0.0.0.0', addrs, 0, 0)
            flows_added -= 1

            # Check that traffic matching flows pass though
            stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                                  1, 0, 0.2)
            expected = {'rx0': flows_added, 'rx1': 0}
            self.check_results(stats, expected)

        out = self.dut.send_expect('flow print', 'pipeline>')
        self.verify("=> Port =" not in out, "Flow found after deletion")

        # Check that again no traffic pass though
        stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                              1, 0, 0.2)
        expected = {'rx0': 0, 'rx1': 0}
        self.check_results(stats, expected)

        self.quit_ip_pipeline()

    def test_route_management(self):
        """
        Add several flows and check only frames with matching IPs passes
        """
        pcap_file = 'ip_pipeline.pcap'
        frame_size = 64

        default_setup = ['p 1 arp add 0 0.0.0.1 0a:0b:0c:0d:0e:0f',
                         'p 1 arp add 1 0.128.0.1 1a:1b:1c:1d:1e:1f']

        ip_addrs = [
            '0.0.0.0', '0.0.0.1', '0.0.0.127', '0.0.0.128', '0.0.0.255',
            '0.0.1.0', '0.0.127.0', '0.0.128.0', '0.0.129.0', '0.0.255.0',
            '0.127.0.0', '0.127.1.0', '0.127.127.0', '0.127.255.0',
            '0.127.255.255']

        frames = []

        for addr in ip_addrs:
            frames.append(self.create_tcp_ipv4_frame(0, '0.0.0.0', addr,
                                                     frame_size))

        self.create_pcap_file_from_frames(pcap_file, frames)
        self.tester.session.copy_file_to(pcap_file)

        self.create_routing_cfgfile()
        # Start ip_pipeline app and setup defaults
        self.start_ip_pipeline(ports=self.ports_mask)
        for command in default_setup:
            self.pipeline_command(command)

        # Check that no traffic pass though
        stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                              1, 0, 0.2)
        expected = {'rx0': 0, 'rx1': 0}
        self.check_results(stats, expected)

        # Add the routes
        routes_added = 0
        for addr in ip_addrs:
            self.pipeline_add_route(0, addr, 32, '0.0.0.1')
            routes_added += 1

            # Check that traffic matching routes pass though
            stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                                  1, 0, 0.2)

            expected = {'rx0': routes_added, 'rx1': 0}
            self.check_results(stats, expected)

        # Remove routes
        for addr in ip_addrs:
            self.pipeline_del_route(addr, 32)
            routes_added -= 1

            # Check that traffic matching flows pass though
            stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                                  1, 0, 0.2)
            expected = {'rx0': routes_added, 'rx1': 0}
            self.check_results(stats, expected)

        out = self.dut.send_expect('route print', 'pipeline>')
        self.verify("Destination = " not in out, "Route found after deletion")

        # Check that again no traffic pass though
        stats = self.send_and_sniff_pcap_file(pcap_file, len(frames),
                                              1, 0, 0.2)
        expected = {'rx0': 0, 'rx1': 0}
        self.check_results(stats, expected)

        self.quit_ip_pipeline()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.quit_ip_pipeline()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("rm -f /tmp/ip_pipeline.cfg", "#")
        self.dut.send_expect("rm -f /tmp/ip_pipeline.cfg.out", "#")
        out = self.dut.build_dpdk_apps("./examples/ip_pipeline")
        self.verify("Error" not in out, "Compilation error")

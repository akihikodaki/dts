# BSD LICENSE
#
# Copyright(c) 2010-2016 Intel Corporation. All rights reserved.
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
Test port hot plug.
"""

import os
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.test_case import TestCase


class TestPortHotPlug(TestCase):
    """
    This feature supports igb_uio, vfio-pci and vfio-pci:noiommu now and not support freebsd
    """

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.coremask = utils.create_mask(cores)
        self.port = len(self.dut_ports) - 1
        if self.drivername == "vfio-pci:noiommu":
            self.driver_name = "vfio-pci"
        else:
            self.driver_name = self.drivername
        self.path = self.dut.apps_name["test-pmd"]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % self.dut.ports_info[self.port]["pci"],
            "#",
            60,
        )

    def attach(self, port):
        """
        attach port
        """
        # dpdk hotplug discern NIC by pci bus and include domid
        out = self.dut.send_expect(
            "port attach %s" % self.dut.ports_info[port]["pci"], "testpmd>", 60
        )
        self.verify("is attached" in out, "Failed to attach")
        out = self.dut.send_expect("port start %s" % port, "testpmd>", 120)
        self.verify("Configuring Port" in out, "Failed to start port")
        # sleep 10 seconds for Intel® Ethernet 700 Series update link stats
        time.sleep(10)
        self.dut.send_expect("show port info %s" % port, "testpmd>", 60)

    def detach(self, port):
        """
        detach port
        """
        out = self.dut.send_expect("port stop %s" % port, "testpmd>", 60)
        self.verify("Stopping ports" in out, "Failed to stop port")
        # sleep 10 seconds for Intel® Ethernet 700 Series update link stats
        time.sleep(10)
        out = self.dut.send_expect("port detach %s" % port, "testpmd>", 60)
        self.verify("is detached" in out, "Failed to detach port")

    def test_after_attach(self):
        """
        first run testpmd after attach port
        """
        cmd = "%s %s -- -i" % (self.path, self.eal_para)
        self.dut.send_expect(cmd, "testpmd>", 60)
        session_secondary = self.dut.new_session()
        session_secondary.send_expect(
            "./usertools/dpdk-devbind.py --bind=%s %s"
            % (self.driver_name, self.dut.ports_info[self.port]["pci"]),
            "#",
            60,
        )
        self.dut.close_session(session_secondary)
        self.attach(self.port)
        self.dut.send_expect("start", "testpmd>", 60)
        out = self.dut.send_expect("port detach %s" % self.port, "testpmd>", 60)
        self.verify("Port not stopped" in out, "able to detach port without stopping")
        self.dut.send_expect("stop", "testpmd>", 60)
        self.detach(self.port)
        self.attach(self.port)

        self.dut.send_expect("start", "testpmd>", 60)
        out = self.dut.send_expect("port detach %s" % self.port, "testpmd>", 60)
        self.verify("Port not stopped" in out, "able to detach port without stopping")
        self.dut.send_expect("clear port stats %s" % self.port, "testpmd>", 60)
        self.send_packet(self.port)
        out = self.dut.send_expect("show port stats %s" % self.port, "testpmd>", 60)
        packet = re.search("RX-packets:\s*(\d*)", out)
        sum_packet = packet.group(1)
        self.verify(int(sum_packet) == 1, "Insufficient the received package")
        self.dut.send_expect("quit", "#", 60)

    def send_packet(self, port):
        """
        Send a packet to port
        """
        self.dmac = self.dut.get_mac_address(port)
        txport = self.tester.get_local_port(port)
        self.txItf = self.tester.get_interface(txport)
        pkt = Packet(pkt_type="UDP")
        pkt.config_layer(
            "ether",
            {
                "dst": self.dmac,
            },
        )
        pkt.send_pkt(self.tester, tx_port=self.txItf)

    def test_before_attach(self):
        """
        first attach port after run testpmd
        """
        session_secondary = self.dut.new_session()
        session_secondary.send_expect(
            "./usertools/dpdk-devbind.py --bind=%s %s"
            % (self.driver_name, self.dut.ports_info[self.port]["pci"]),
            "#",
            60,
        )
        self.dut.close_session(session_secondary)
        cmd = "%s %s -- -i" % (self.path, self.eal_para)
        self.dut.send_expect(cmd, "testpmd>", 60)
        self.detach(self.port)
        self.attach(self.port)

        self.dut.send_expect("start", "testpmd>", 60)
        out = self.dut.send_expect("port detach %s" % self.port, "testpmd>", 60)
        self.verify("Port not stopped" in out, "able to detach port without stopping")
        self.dut.send_expect("clear port stats %s" % self.port, "testpmd>", 60)
        self.send_packet(self.port)
        out = self.dut.send_expect("show port stats %s" % self.port, "testpmd>", 60)
        packet = re.search("RX-packets:\s*(\d*)", out)
        sum_packet = packet.group(1)
        self.verify(int(sum_packet) == 1, "Insufficient the received package")
        self.dut.send_expect("quit", "#", 60)

    def test_port_detach_attach_for_vhost_user_virtio_user(self):
        vdev = "eth_vhost0,iface=vhost-net,queues=1"
        iface = "vhost-net1"
        path = self.dut.base_dir + os.path.sep + iface
        path = path.replace("~", "/root")
        self.dut.send_expect("rm -rf %s" % iface, "# ")
        cores = self.dut.get_core_list("all")
        self.verify(len(cores) > 8, "insufficient cores for this case")
        eal_param = self.dut.create_eal_parameters(
            no_pci=True, cores=cores[1:5], vdevs=[vdev], prefix="vhost"
        )
        testpmd_cmd = "%s " % self.path + eal_param + " -- -i"
        self.dut.send_expect(testpmd_cmd, "testpmd>", timeout=60)
        self.dut.send_expect("port stop 0", "testpmd>")
        out = self.dut.send_expect("port detach 0", "testpmd>")
        self.verify("Device is detached" in out, "Failed to detach")
        stats = self.dut.send_expect(
            "ls %s" % path, "#", timeout=3, alt_session=True, verify=True
        )
        self.verify(stats == 2, "port detach failed")
        time.sleep(1)
        out = self.dut.send_expect(
            "port attach eth_vhost1,iface=%s,queues=1" % iface, "testpmd>"
        )
        self.verify("Port 0 is attached." in out, "Failed to attach")
        self.dut.send_expect("port start 0", "testpmd>")
        out = self.dut.send_expect(
            "ls %s" % path, "#", timeout=3, alt_session=True, verify=True
        )
        self.verify(iface in out, "port attach failed")

        self.session2 = self.dut.create_session(name="virtio_user")
        eal_param = self.dut.create_eal_parameters(
            no_pci=True, fixed_prefix="virtio1", cores=cores[5:9]
        )
        testpmd_cmd2 = "%s/%s " % (self.dut.base_dir, self.path) + eal_param + " -- -i"
        self.session2.send_expect(testpmd_cmd2, "testpmd>", timeout=60)
        self.session2.send_expect(
            "port attach net_virtio_user1,mac=00:01:02:03:04:05,path=%s,queues=1,packed_vq=1,mrg_rxbuf=1,in_order=0"
            % path,
            "testpmd",
        )
        self.session2.send_expect("port start 0", "testpmd>", timeout=60)
        out = self.dut.send_expect(
            "ls %s" % path, "#", timeout=3, alt_session=True, verify=True
        )
        self.verify(iface in out, "port attach failed")
        self.dut.send_expect("start", "testpmd")
        self.session2.send_expect("start tx_first 32", "testpmd")
        out = self.session2.send_expect("show port stats 0", "testpmd")
        rx_pkts = int(re.search("RX-packets: (\d+)", out).group(1))
        tx_pkts = int(re.search("TX-packets: (\d+)", out).group(1))
        self.logger.info("rx packets: %d" % rx_pkts)
        self.logger.info("tx packets: %d" % tx_pkts)
        self.verify(
            rx_pkts != 0 and tx_pkts != 0, "not received packets or transport packets"
        )
        self.session2.send_expect("show port stats 0", "testpmd", timeout=2)
        self.session2.send_expect("stop", "testpmd", timeout=2)
        self.session2.send_expect("quit", "#", timeout=2)
        self.dut.send_expect("stop", "testpmd", timeout=2)
        self.dut.send_expect("quit", "#", timeout=2)
        self.session2.close()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --bind=%s %s"
            % (self.driver_name, self.dut.ports_info[self.port]["pci"]),
            "#",
            60,
        )
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass

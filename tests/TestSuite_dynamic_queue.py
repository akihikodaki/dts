# <COPYRIGHT_TAG>

import time
import re
import utils
from test_case import TestCase
from pmd_output import PmdOutput
from settings import get_nic_name
from packet import Packet
import random

test_loop = 3


class TestDynamicQueue(TestCase):

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        out = self.dut.send_expect("cat config/rte_config.h", "]# ", 10)
        self.PF_Q_strip = 'RTE_LIBRTE_I40E_QUEUE_NUM_PER_PF'
        pattern = "define (%s) (\d*)" % self.PF_Q_strip
        self.PF_QUEUE = self.element_strip(out, pattern, True)
        self.used_dut_port = self.dut_ports[0]
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        self.dut_testpmd = PmdOutput(self.dut)

    def set_up(self):
        # Fortville_spirit needs more cores to run properly
        if (self.nic in ["fortville_spirit"]):
            self.verify("len(self.dut.cores)>=7", "Less than seven cores can't run testpmd")
            self.dut_testpmd.start_testpmd(
                "all", "--port-topology=chained --txq=%s --rxq=%s"
                % (self.PF_QUEUE, self.PF_QUEUE))
        elif (self.nic in ["cavium_a063", "cavium_a064"]):
            eal_opts = ""
            for port in self.dut_ports:
                eal_opts += "-w %s,max_pools=256 "%(self.dut.get_port_pci(self.dut_ports[port]))
            self.dut_testpmd.start_testpmd(
                "Default", "--port-topology=chained --txq=%s --rxq=%s"
                % (self.PF_QUEUE, self.PF_QUEUE), eal_param = eal_opts)
        else:
            self.dut_testpmd.start_testpmd(
                "Default", "--port-topology=chained --txq=%s --rxq=%s"
                % (self.PF_QUEUE, self.PF_QUEUE))

    def element_strip(self, out, pattern, if_get_from_cfg=False):
        """
        Strip and get queue number.
        """
        s = re.compile(pattern, re.DOTALL)
        res = s.search(out)
        if res is None:
            print((utils.RED('Fail to search number.')))
            return None
        else:
            result = res.group(2) if if_get_from_cfg else res.group(1)
            return int(result)

    def send_packet(self):
        """
        Generate packets and send them to dut
        """
        mac = self.dut.get_mac_address(0)
        pktnum = self.PF_QUEUE * 4
        pkt = Packet()
        pkt.generate_random_pkts(mac, pktnum=pktnum, random_type=['IP_RAW'])
        pkt.send_pkt(self.tester, tx_port=self.tester_intf)

    def rxq_setup_test(self, chgflag=0):
        """
        Dynamic to setup rxq and reconfigure ring size at runtime.
        chgflag: reconfigure ring size flag
                 1: reconfigure Rx ring size
                 0: no change on Rx ring size
        """
        queue = list()
        for i in range(test_loop):
            queue.append(random.randint(1, self.PF_QUEUE - 1))
            self.dut_testpmd.execute_cmd('port 0 rxq %d stop' % queue[i])

        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('start')
        self.send_packet()
        self.dut.get_session_output(timeout=10)
        out = self.dut_testpmd.execute_cmd('stop')

        # Check Rx stopped queues can't receive packets
        for i in range(test_loop):
            self.verify(
                "Forward Stats for RX Port= 0/Queue=%2d" % queue[i] not in out,
                "Fail to verify rxq stop!")

        if chgflag == 1:
            for i in range(test_loop):
                out = self.dut_testpmd.execute_cmd(
                        'show rxq info 0 %d' % queue[i])
                qring_strip = 'Number of RXDs: '
                pattern = "%s([0-9]+)" % qring_strip
                qringsize = self.element_strip(out, pattern)
                chg_qringsize = qringsize % 1024 + 256
                if qringsize == 512:
                    chg_qringsize = 256
                self.dut_testpmd.execute_cmd(
                    'port config 0 rxq %d ring_size %d'
                    % (queue[i], chg_qringsize))
                self.dut_testpmd.execute_cmd('port 0 rxq %d setup' % queue[i])
                out = self.dut_testpmd.execute_cmd(
                    'show rxq info 0 %d' % queue[i])
                chk_qringsize = self.element_strip(out, pattern)
                self.verify(chk_qringsize == chg_qringsize,
                            "Fail to change ring size at runtime!")

        for i in range(test_loop):
            if chgflag == 0:
                self.dut_testpmd.execute_cmd('port 0 rxq %d setup' % queue[i])
            self.dut_testpmd.execute_cmd('port 0 rxq %d start' % queue[i])

        self.dut_testpmd.execute_cmd('start')
        self.send_packet()
        self.dut.get_session_output(timeout=10)
        out = self.dut_testpmd.execute_cmd('stop')

        # Check Rx setup queues could receive packets
        for i in range(test_loop):
            self.verify("Forward Stats for RX Port= 0/Queue=%2d"
                        % queue[i] in out, "Fail to setup rxq %d at runtime"
                        % queue[i])

    def txq_setup_test(self, chgflag=0):
        """
        Dynamic to setup txq and reconfigure ring size at runtime.
        chgflag: reconfigure ring size flag
                 1: reconfigure Tx ring size
                 0: no change on Tx ring size
        """
        for i in range(test_loop):
            queue = random.randint(1, self.PF_QUEUE - 1)
            out = self.dut_testpmd.execute_cmd('show txq info 0 %d' % queue)
            qring_strip = 'Number of TXDs: '
            pattern = "%s([0-9]+)" % qring_strip
            qringsize = self.element_strip(out, pattern)
            self.dut_testpmd.execute_cmd('port 0 txq %d stop' % queue)
            self.dut_testpmd.execute_cmd('set fwd txonly')
            self.dut_testpmd.execute_cmd('start')
            time.sleep(10)
            out = self.dut_testpmd.execute_cmd('stop')
            tx_num = qringsize - 1

            if (self.nic in ["cavium_a063", "cavium_a064"]):
                self.verify("TX-packets: 0" in out,
                            "Fail to stop txq at runtime")
            else:
                # Check Tx stopped queue only transmits qringsize-1 packets
                self.verify("TX-packets: %d" % tx_num in out,
                            "Fail to stop txq at runtime")
            if chgflag == 1:
                chg_qringsize = qringsize % 1024 + 256
                if qringsize == 512:
                    chg_qringsize = 256
                self.dut_testpmd.execute_cmd(
                    'port config 0 txq %d ring_size %d'
                    % (queue, chg_qringsize))
                self.dut_testpmd.execute_cmd('port 0 txq %d setup' % queue)
                out = self.dut_testpmd.execute_cmd(
                    'show txq info 0 %d' % queue)
                chk_qringsize = self.element_strip(out, pattern)
                self.verify(chk_qringsize == chg_qringsize,
                            "Fail to change ring size at runtime!")
            if chgflag == 0:
                self.dut_testpmd.execute_cmd('port 0 txq %d setup' % queue)

            self.dut_testpmd.execute_cmd('port 0 txq %d start' % queue)
            self.dut_testpmd.execute_cmd('start')
            time.sleep(10)
            out = self.dut_testpmd.execute_cmd('stop')
            """
            Check Tx setup queue could transmit packets normally, not only
            qringsize-1 packets
            """
            self.verify("TX-packets: %d" % tx_num not in out,
                        "Fail to setup txq at runtime")
            if chgflag == 1:
                chgtx_num = chg_qringsize - 1
                self.verify("TX-packets: %d" % chgtx_num not in out,
                            "Fail to change txq ring size at runtime")

    def test_rxq_setup(self):
        """
        Dynamic to setup rxq test
        """
        self.rxq_setup_test()

    def test_rxq_chgring_setup(self):
        """
        Dynamic to setup rxq and change ring size test
        """
        self.rxq_setup_test(chgflag=1)

    def test_txq_setup(self):
        """
        Dynamic to setup txq test
        """
        self.txq_setup_test()

    def test_txq_chgring_setup(self):
        """
        Dynamic to setup txq and change ring size test
        """
        self.txq_setup_test(chgflag=1)

    def tear_down(self):
        self.dut_testpmd.quit()

    def tear_down_all(self):
        pass

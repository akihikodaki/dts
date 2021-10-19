# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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

import time
import traceback

# import dts/framework libs
import framework.utils as utils

# import bonding lib
import tests.bonding as bonding
from framework.exception import VerifyFailure
from framework.test_case import TestCase

from .bonding import (
    FRAME_SIZE_64,
    MODE_ACTIVE_BACKUP,
    MODE_ALB_BALANCE,
    MODE_BROADCAST,
    MODE_LACP,
    MODE_ROUND_ROBIN,
    MODE_TLB_BALANCE,
    MODE_XOR_BALANCE,
)


class TestBondingStacked(TestCase):

    #
    # On dut, dpdk bonding
    #
    def check_bonded_device_queue_config(self, *devices):
        '''
        check if master bonded device/slave device queue configuration
        is the same.
        '''
        # get master bonded device queue configuration
        master = self.bond_inst.get_port_info(devices[0], 'queue_config')
        # get slave device queue configuration
        for port_id in devices[1:]:
            config = self.bond_inst.get_port_info(port_id, 'queue_config')
            if config == master:
                continue
            msg = ("slave bonded port [{0}] is "
                   "different to top bonded port [{1}]").format(
                                                        port_id, devices[0])
            raise VerifyFailure('bonded device queue config:: ' + msg)

    def set_stacked_bonded(self, slaveGrpOne, slaveGrpTwo, bond_mode,
                           ignore=False):
        '''
        set stacked bonded mode for a custom bonding mode
        '''
        inst = self.bond_inst
        socket_id = self.dut.get_numa_id(self.bond_slave)
        # create first bonded device 1, add slaves in it
        bond_port_1 = inst.create_bonded_device(bond_mode, socket_id)
        inst.add_slave(bond_port_1, False, '', *slaveGrpOne)
        # create second bonded device 2, add slaves in it
        bond_port_2 = inst.create_bonded_device(bond_mode, socket_id)
        inst.add_slave(bond_port_2, False, '', *slaveGrpTwo)
        # create master bonded device 3, which is the top bonded device
        master_bond_port = inst.create_bonded_device(bond_mode, socket_id)
        # add bond bonded device 1 to bonded device 3
        # check bonding config status
        inst.add_slave(master_bond_port, False, '', *[bond_port_1])
        # add bonded device 2 to bonded device 3
        # check bonding config status
        inst.add_slave(master_bond_port, False, '', *[bond_port_2])
        # check if master bonding/each slaves queue configuration is the same.
        if not ignore:
            self.check_bonded_device_queue_config(*[master_bond_port,
                                                 bond_port_1, bond_port_2])

        return [bond_port_1, bond_port_2, master_bond_port]

    def set_third_stacked_bonded(self, bond_port, bond_mode):
        '''
        set third level stacked bonded to check if stacked level can be set
        more than 2
        '''
        inst = self.bond_inst
        socket_id = self.dut.get_numa_id(self.bond_slave)
        third_bond_port = inst.create_bonded_device(bond_mode, socket_id)
        inst.add_slave(third_bond_port, False, '', *[bond_port])

    def duplicate_add_stacked_bonded(self, bond_port_1, bond_port_2,
                                     master_bond_port):
        '''
        check if adding duplicate stacked bonded device is forbidden
        '''
        inst = self.bond_inst
        # check exception process
        expected_str = 'Slave device is already a slave of a bonded device'
        # add bonded device 1 to bonded device 3
        # check bonding config status
        inst.add_slave(master_bond_port, False, expected_str, *[bond_port_1])
        # add bonded device 2 to bonded device 3
        # check bonding config status
        inst.add_slave(master_bond_port, False, expected_str, *[bond_port_2])

    def preset_stacked_bonded(self, slaveGrpOne, slaveGrpTwo, bond_mode):
        bond_port_1, bond_port_2, master_bond_port = self.set_stacked_bonded(
                                                                slaveGrpOne,
                                                                slaveGrpTwo,
                                                                bond_mode,
                                                                ignore=True)
        portList = [slaveGrpOne[0],
                    slaveGrpTwo[0],
                    bond_port_1,
                    bond_port_2,
                    master_bond_port]
        cmds = [
            ["port stop all", ''],
            ["set portlist " + ",".join([str(port) for port in portList]), ''],
            # start top level bond port only, and let it propagate the start
            # action to slave bond ports and its the real nics.
            ["port start {}".format(master_bond_port), ' ', 15]
        ]
        self.bond_inst.d_console(cmds)
        # blank space command is used to skip LSC event to avoid core dumped issue
        time.sleep(5)
        cmds = [ [' ', ''],
                 ["start", '']]
        self.bond_inst.d_console(cmds)
        time.sleep(5)

        return bond_port_1, bond_port_2, master_bond_port

    #
    # packet transmission
    #
    def traffic(self, traffic_config, ports):
        # get ports statistics before sending packets
        stats_pre = self.bond_inst.get_all_stats(ports)
        # send packets
        self.bond_inst.send_packet(traffic_config)
        # get ports statistics after sending packets
        stats_post = self.bond_inst.get_all_stats(ports)
        # calculate ports statistics result
        for port_id in ports:
            stats_post[port_id]['RX-packets'] -= stats_pre[port_id]['RX-packets']
            stats_post[port_id]['TX-packets'] -= stats_pre[port_id]['TX-packets']

        return stats_post

    def config_port_traffic(self, tx_port, rx_port, total_pkt):
        ''' set traffic configuration '''
        traffic_config = {
            'port topo': [tx_port, rx_port],
            'stream': self.bond_inst.set_stream_to_slave_port(rx_port),
            'traffic configs': {
                  'count': total_pkt,
            },}

        return traffic_config

    def active_slave_rx(self, slave, bond_port, mode):
        msg = "send packet to active slave port <{0}>".format(slave)
        self.logger.info(msg)
        tx_intf = self.tester.get_interface(
                        self.tester.get_local_port(self.dut_ports[slave]))
        # get traffic config
        traffic_config = self.config_port_traffic(tx_intf, slave,self.total_pkt)
        # select ports for statistics
        ports = [slave, bond_port]
        # run traffic
        stats = self.traffic(traffic_config, ports)
        # check slave statistics
        msg = "port <{0}> Data not received by port <{1}>".format(
                                                       tx_intf, slave)
        # here using `>=` to ignore some miscellaneous packets, e.g. lldp
        self.verify(stats[slave]['RX-packets'] >= self.total_pkt, msg)
        msg = "tester port {0}  <----> dut port {1} is ok".format(
                                                        tx_intf, slave)
        self.logger.info(msg)
        # check bond port statistics
        # here using `>=` to ignore some miscellaneous packets, e.g. lldp
        self.verify(stats[slave]['RX-packets'] >= self.total_pkt,
                    "Bond port have error RX packet in XOR")

    def inactive_slave_rx(self, slave, bond_port, mode):
        msg = "send packet to inactive slave port <{0}>".format(slave)
        self.logger.info(msg)
        tx_intf = self.tester.get_interface(
                        self.tester.get_local_port(self.dut_ports[slave]))
        # get traffic config
        traffic_config = self.config_port_traffic(tx_intf, slave,self.total_pkt)
        # select ports for statistics
        ports = [slave, bond_port]
        # run traffic
        stats = self.traffic(traffic_config, ports)
        # check slave statistics
        msg = ("port <{0}> Data received by port <{1}>, "
               "but should not.").format(tx_intf, slave)
        self.verify(stats[slave]['RX-packets'] == 0, msg)
        msg = "tester port {0}  <-|  |-> dut port {1} is blocked".format(
                                                                tx_intf, slave)
        self.logger.info(msg)
        # check bond port statistics
        self.verify(stats[slave]['RX-packets'] == 0,
                    "Bond port have error RX packet in {0}".format(mode))

    def check_traffic_with_one_slave_down(self, mode):
        """
        Verify that transmitting packets correctly when set one slave of
        the bonded device link down.
        """
        results = []
        #-------------------------------
        # boot up testpmd
        self.bond_inst.start_testpmd()
        try:
            slaves = {'active' : [], 'inactive' : []}
            #-------------------------------
            # preset stacked bonded device
            slaveGrpOne = self.slaveGrpOne
            slaveGrpTwo = self.slaveGrpTwo
            bond_port_1, bond_port_2, master_bond_port = \
                    self.preset_stacked_bonded(slaveGrpOne, slaveGrpTwo, mode)
            #---------------------------------------------------
            # set one slave of first bonded device link down
            primary_slave = slaveGrpOne[0]
            self.bond_inst.set_dut_port_status(primary_slave, "down")
            slaves['inactive'].append(primary_slave)
            # get slave status
            primary_port, active_slaves = \
                                self.bond_inst.get_active_slaves(bond_port_1)
            slaves['active'].extend(active_slaves)
            if primary_slave in slaves['active']:
                msg = "{0} should not be in active slaves list".format(
                                                                primary_slave)
                raise Exception(msg)
            #---------------------------------------------------
            # set one slave of second bonded device link down
            primary_slave = slaveGrpTwo[0]
            self.bond_inst.set_dut_port_status(primary_slave, "down")
            slaves['inactive'].append(primary_slave)
            # check active slaves
            primary_port_2, active_slaves_2 = \
                                self.bond_inst.get_active_slaves(bond_port_2)
            slaves['active'].extend(active_slaves_2)
            if primary_slave in slaves['active']:
                msg = "{0} should not be in active slaves list".format(
                                                                primary_slave)
                raise Exception(msg)
            # traffic testing
            # active slave traffic testing
            for slave in slaves['active']:
                self.active_slave_rx(slave, master_bond_port, mode)
            # inactive slave traffic testing
            for slave in slaves['inactive']:
                self.inactive_slave_rx(slave, master_bond_port, mode)
        except Exception as e:
            results.append(e)
            self.logger.error(traceback.format_exc())
        finally:
            self.bond_inst.close_testpmd()

        return results

    def check_traffic(self, mode):
        """ normal traffic with all slaves are under active status.
        verify the RX packets are all correct with stacked bonded device.
        bonded device's statistics should be the sum of slaves statistics.
        """
        self.bond_inst.start_testpmd()
        slaveGrpOne = self.slaveGrpOne
        slaveGrpTwo = self.slaveGrpTwo
        bond_port_1, bond_port_2, master_bond_port = \
                self.preset_stacked_bonded(slaveGrpOne, slaveGrpTwo, mode)
        results = []
        # check first bonded device
        try:
            self.logger.info('check first bonded device')
            # active slave traffic testing
            for slave in slaveGrpOne:
                self.active_slave_rx(slave, bond_port_1, mode)
        except Exception as e:
            results.append(e)
        # check second bonded device
        try:
            self.logger.info('check second bonded device')
            # active slave traffic testing
            for slave in slaveGrpOne:
                self.active_slave_rx(slave, bond_port_2, mode)
        except Exception as e:
            results.append(e)

        # check top bonded device
        try:
            self.logger.info('check master bonded device')
            # active slave traffic testing
            for slave in slaveGrpOne + slaveGrpTwo:
                self.active_slave_rx(slave, master_bond_port, mode)
        except Exception as e:
            results.append(e)

        self.bond_inst.close_testpmd()

        return results

    def backup_check_traffic(self):
        mode = MODE_ACTIVE_BACKUP
        msg = "begin checking bonding backup(stacked) mode transmission"
        self.logger.info(msg)
        results = self.check_traffic(mode)
        if results:
            for item in results:
                self.logger.error(item)
            raise VerifyFailure("backup(stacked) mode: rx failed")

    def backup_check_traffic_with_slave_down(self):
        mode = MODE_ACTIVE_BACKUP
        self.logger.info("begin checking bonding backup(stacked) "
                         "mode transmission with one slave down")
        results = self.check_traffic_with_one_slave_down(mode)
        if results:
            for item in results:
                self.logger.error(item)
            msg = "backup(stacked) mode: rx with one slave down failed"
            raise VerifyFailure(msg)

    def xor_check_rx(self):
        mode = MODE_XOR_BALANCE
        msg = "begin checking bonding xor(stacked) mode transmission"
        self.logger.info(msg)
        results = self.check_traffic(mode)
        if results:
            for item in results:
                self.logger.error(item)
            raise VerifyFailure("xor(stacked) mode: rx failed")

    def xor_check_stacked_rx_one_slave_down(self):
        mode = MODE_XOR_BALANCE
        self.logger.info("begin checking bonding xor(stacked) mode "
                         "transmission with one slave down")
        results = self.check_traffic_with_one_slave_down(mode)
        if results:
            for item in results:
                self.logger.error(item)
            msg = "xor(stacked) mode: rx with one slave down failed"
            raise VerifyFailure(msg)
    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run before each test suite
        """
        self.verify('bsdapp' not in self.target, "Bonding not support freebsd")
        self.dut_ports = self.dut.get_ports()
        num_ports = len(self.dut_ports)
        self.verify(num_ports == 2 or num_ports == 4, "Insufficient ports")
        # separate ports into two group as first level bond ports' slaves
        sep_index = len(self.dut_ports)//2
        self.slaveGrpOne = self.dut_ports[:sep_index]
        self.slaveGrpTwo = self.dut_ports[sep_index:]
        self.bond_slave = self.dut_ports[0]
        # initialize bonding common methods name
        self.total_pkt = 100
        config = {
            'parent': self,
            'pkt_name': 'udp',
            'pkt_size': FRAME_SIZE_64,
            'src_mac': '52:00:00:00:00:03',
            'src_ip': '10.239.129.65',
            'src_port': 61,
            'dst_ip': '10.239.129.88',
            'dst_port': 53,}
        self.bond_inst = bonding.PmdBonding(**config)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """

    def test_basic_behav(self):
        '''
        allow a bonded device to be added to another bonded device.
        There's two limitations to create master bonding:

         - Total depth of nesting is limited to two levels,
         - 802.3ad mode is not supported if one or more slaves is a bond device

        note: There 802.3ad mode can not be supported on this bond device.

        This case is aimed at testing basic behavior of stacked bonded commands.

        '''
        #------------------------------------------------
        # check stacked bonded status, except mode 4 (802.3ad)
        mode_list =[MODE_ROUND_ROBIN,
                    MODE_ACTIVE_BACKUP,
                    MODE_XOR_BALANCE,
                    MODE_BROADCAST,
                    MODE_TLB_BALANCE,
                    MODE_ALB_BALANCE]
        slaveGrpOne = self.slaveGrpOne
        slaveGrpTwo = self.slaveGrpTwo
        check_result = []
        for bond_mode in mode_list:
            self.logger.info("begin mode <{0}> checking".format(bond_mode))
            # boot up testpmd
            self.bond_inst.start_testpmd()
            try:
                self.logger.info("check bonding mode <{0}>".format(bond_mode))
                # set up stacked bonded status
                bond_port_1, bond_port_2, master_bond_port = \
                    self.set_stacked_bonded(slaveGrpOne, slaveGrpTwo, bond_mode)
                # check duplicate add slave
                self.duplicate_add_stacked_bonded(bond_port_1, bond_port_2,
                                                  master_bond_port)
                # check stacked limitation
                self.set_third_stacked_bonded(master_bond_port, bond_mode)
                # quit testpmd, it is not supported to reset testpmd
                self.logger.info("mode <{0}> done !".format(bond_mode))
                check_result.append([bond_mode, None])
            except Exception as e:
                check_result.append([bond_mode, e])
                self.logger.error(e)
            finally:
                self.bond_inst.close_testpmd()
                time.sleep(5)
        #------------------------------------------------
        # 802.3ad mode is not supported
        # if one or more slaves is a bond device
        # so it should raise a exception
        msg = ''
        try:
            # boot up testpmd
            self.bond_inst.start_testpmd()
            # set up stacked bonded status
            self.set_stacked_bonded(slaveGrpOne, slaveGrpTwo, MODE_LACP)
            # quit testpmd, it is not supported to reset testpmd
            msg = ("802.3ad mode hasn't been forbidden to "
                   "use stacked bonded setting")
            check_result.append([MODE_LACP, msg])
        except Exception as e:
            check_result.append([MODE_LACP, None])
        finally:
            self.bond_inst.close_testpmd()

        exception_flag = False
        for bond_mode, e in check_result:
            msg = "mode <{0}>".format(bond_mode)
            if e:
                self.logger.info(msg)
                self.logger.error(e)
                exception_flag = True
            else:
                self.logger.info(msg + ' done !')
        # if some checking item is failed, raise exception
        if exception_flag:
            raise VerifyFailure('some test items failed')
        else:
            self.logger.info('all test items have done !')

    def test_mode_backup_rx(self):
        """
        Verify receive packets correctly in the active-backup(stacked) mode.
        """
        self.backup_check_traffic()

    def test_mode_backup_one_slave_down(self):
        """
        Verify that receive packets correctly in the active-backup(stacked) mode
        when bringing any one slave of the bonding device link down.
        """
        slave_down_port_limit = 4
        if len(self.dut_ports) < slave_down_port_limit:
            msg = ("ports less than {0}, "
                   "ignore stacked one slave down check").format(
                                                        slave_down_port_limit)
            self.logger.warning(msg)
            return
        self.backup_check_traffic_with_slave_down()

    def test_mode_xor_rx(self):
        """
        Verify that receive packets correctly in the XOR(stacked) mode.
        """
        self.xor_check_rx()

    def test_mode_xor_rx_one_slave_down(self):
        """
        Verify that receive packets correctly in the XOR(stacked) mode when
        bringing any one slave of the bonding device link down.
        """
        slave_down_port_limit = 4
        if len(self.dut_ports) < slave_down_port_limit:
            msg = ("ports less than {0}, "
                   "ignore stacked one slave down check").format(
                                                        slave_down_port_limit)
            self.logger.warning(msg)
            return
        self.xor_check_stacked_rx_one_slave_down()

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
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
DPDK Test suite.
Test support of dpdk-procinfo tool feature
'''

import os
import re
import time
import traceback
from functools import reduce

from scapy.sendrecv import sendp

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.utils import create_mask as dts_create_mask


class TestEthtoolStats(TestCase):

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    def d_a_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        output = self.dut.alt_session.send_expect(*_cmd)
        output2 = self.dut.alt_session.session.get_session_before(1)
        return output + os.linesep + output2

    def send_packet(self, pkt_config, src_intf):
        for pkt_type in list(pkt_config.keys()):
            pkt = Packet(pkt_type=pkt_type)
            # set packet every layer's input parameters
            if 'layer_configs' in list(pkt_config[pkt_type].keys()):
                pkt_configs = pkt_config[pkt_type]['layer_configs']
                if pkt_configs:
                    for layer in list(pkt_configs.keys()):
                        pkt.config_layer(layer, pkt_configs[layer])
            pkt.send_pkt(crb=self.tester, tx_port=src_intf, count=1)
            time.sleep(1)

    def traffic(self):
        # make sure interface in link up status
        src_intf, src_mac = self.link_topo
        cmd = "ifconfig {0} up".format(src_intf)
        self.d_a_con(cmd)
        # send out packet
        for frame_size in self.frame_sizes:
            headers_size = sum(
                [HEADER_SIZE[x] for x in ['eth', 'ip', 'udp']])
            payload_size = frame_size - headers_size
            config_layers = {
                'ether': {'src': src_mac},
                'raw':   {'payload': ['58'] * payload_size}}
            pkt_config = {'UDP': {'layer_configs': config_layers}}
            self.send_packet(pkt_config, src_intf)

    def init_testpmd(self):
        self.testpmd = PmdOutput(self.dut)
        self.is_pmd_on = False

    def start_testpmd(self):
        self.testpmd.start_testpmd('1S/2C/1T', param='--port-topology=loop')
        self.is_pmd_on = True
        time.sleep(2)

    def set_testpmd(self):
        cmds = [
            'set fwd io',
            'clear port xstats all',
            'start']
        [self.testpmd.execute_cmd(cmd) for cmd in cmds]
        time.sleep(2)

    def close_testpmd(self):
        if not self.is_pmd_on:
            return
        self.testpmd.quit()
        self.is_pmd_on = False

    def get_pmd_xstat_data(self):
        ''' get testpmd nic extended statistics '''
        cmd = 'show port xstats all'
        output = self.testpmd.execute_cmd(cmd)
        if "statistics" not in output:
            self.logger.error(output)
            raise Exception("failed to get port extended statistics data")
        data_str = output.splitlines()
        port_xstat = {}
        cur_port = None
        pat = r".*extended statistics for port (\d+).*"
        for line in data_str:
            if not line.strip():
                continue
            if "statistics" in line:
                result = re.findall(pat, line.strip())
                if len(result):
                    cur_port = result[0]
            elif cur_port is not None and ": " in line:
                if cur_port not in port_xstat:
                    port_xstat[cur_port] = {}
                result = line.strip().split(": ")
                if len(result) == 2 and result[0]:
                    name, value = result
                    port_xstat[cur_port][name] = value
                else:
                    raise Exception("invalid data")

        return port_xstat

    def clear_pmd_ports_stat(self):
        options = ["--xstats-reset ", "--stats-reset "]
        for option in options:
            cmd = self.dpdk_proc_info + " %s" % option
            self.d_a_con(cmd)
            time.sleep(1)

    def init_proc_info(self):
        ports_count = len(self.dut_ports)
        ports_mask = reduce(lambda x, y: x | y,
                            [0x1 << x for x in range(ports_count)])
        app_name = self.dut.apps_name['proc-info'].split('/')[-1]
        self.query_tool = os.path.join(
            self.target_dir, self.target, 'app', app_name + '--file-prefix=%s' % self.prefix)
        self.dpdk_proc_info = "%s -v -- -p %s" % (self.query_tool, ports_mask)

    def parse_proc_info_xstat_output(self, msg):
        if "statistics" not in msg:
            self.logger.error(msg)
            raise VerifyFailure("get port statistics data failed")

        port_xstat = {}
        cur_port = None
        pat = ".*for port (\d)+ .*"
        data_str = msg.splitlines()
        for line in data_str:
            if not line.strip():
                continue
            if "statistics" in line:
                result = re.findall(pat, line.strip())
                if len(result):
                    cur_port = result[0]
            elif cur_port is not None and ": " in line:
                if cur_port not in port_xstat:
                    port_xstat[cur_port] = {}
                result = line.strip().split(": ")
                if len(result) == 2 and result[0]:
                    name, value = result
                    port_xstat[cur_port][name] = value
                else:
                    raise VerifyFailure("invalid data")

        return port_xstat

    def query_dpdk_xstat_all(self, option="xstats"):
        cmd = self.dpdk_proc_info + " --%s" % (option)
        output = self.d_a_con(cmd)
        infos = self.parse_proc_info_xstat_output(output)
        if not infos:
            msg = 'get xstat data failed'
            raise VerifyFailure(msg)
        return infos

    def get_xstat_statistic_id(self, sub_option):
        option = "xstats-name"
        execept_msgs = []
        cmd = self.dpdk_proc_info + " --%s %s" % (option, sub_option)
        msg = self.d_a_con(cmd)
        sub_stat_data = self.parse_proc_info_xstat_output(msg)
        if sub_option not in msg or not len(sub_stat_data):
            execept_msgs.append([option, msg])
        else:
            for port in sub_stat_data:
                if sub_option not in sub_stat_data[port]:
                    msg = "{0} {1} data doesn't existed".format(
                        port, sub_option)
                    self.logger.error(msg)
                    continue
                if not port:
                    msg1 = "port {0} [{1}]".format(port, sub_option)
                    execept_msgs.append([msg1, msg2])
                    continue
        return sub_stat_data, execept_msgs

    def check_single_stats_result(self, sub_stat_data, all_xstat_data):
        execept_msgs = []
        for port, infos in list(sub_stat_data.items()):
            for item in infos:
                if not port or \
                   port not in all_xstat_data or \
                   item not in all_xstat_data[port] or \
                   sub_stat_data[port][item] != all_xstat_data[port][item]:
                    msg1 = "port {0} [{1}]".format(port, item)
                    msg2 = "expect {0} ".format(all_xstat_data[port][item]) + \
                           "show {0}".format(sub_stat_data[port][item])
                    execept_msgs.append([msg1, msg2])
                    continue
                msg2 = "expect {0} ".format(all_xstat_data[port][item]) + \
                       "show {0}".format(sub_stat_data[port][item])
                self.logger.info(msg2)
        return execept_msgs

    def get_xstat_single_statistic(self, stat, all_xstat_data):
        option = "xstats-id"
        execept_msgs = []
        for id in list(stat.values()):
            cmd = self.dpdk_proc_info + " --%s %s" % (option, id)
            msg = self.d_a_con(cmd)
            sub_stat_data = self.parse_proc_info_xstat_output(msg)
            if not sub_stat_data or not len(sub_stat_data):
                execept_msgs.append([option, msg])
            else:
                execept_msgs += self.check_single_stats_result(
                    sub_stat_data, all_xstat_data)
            if len(execept_msgs):
                for msgs in execept_msgs:
                    self.logger.error(msgs[0])
                    self.logger.info(msgs[1])
                raise VerifyFailure("query data exception ")

        self.logger.info("all port is correct")

        time.sleep(1)

    def check_xstat_command_list(self):
        output = self.d_a_con(self.query_tool)
        expected_command = [
            "xstats-reset",
            "xstats-name NAME",
            "xstats-ids IDLIST",
            "xstats-reset"]
        pat = ".*--(.*):.*"
        handle = re.compile(pat)
        result = handle.findall(output)
        if not result or len(result) == 0:
            cmds = " | ".join(expected_command)
            msg = "expected commands {0} have not been included".format(cmds)
            raise VerifyFailure(msg)
        missing_cmds = []
        for cmd in expected_command:
            if cmd not in result:
                missing_cmds.append(cmd)

        if len(missing_cmds):
            msg = " | ".join(missing_cmds) + " have not been included"
            raise VerifyFailure(msg)

        cmds = " | ".join(expected_command)
        msg = "expected commands {0} have been included".format(cmds)
        self.logger.info(msg)

    def check_xstat_reset_status(self):
        all_xstat_data = self.query_dpdk_xstat_all()
        execept_msgs = []
        for port in all_xstat_data:
            stats_info = all_xstat_data[port]
            for stat_name, value in list(stats_info.items()):
                if int(value) != 0:
                    msg = "port {0} <{1}> [{2}] has not been reset"
                    execept_msgs.append(msg.format(port, stat_name, value))
        if len(execept_msgs):
            self.logger.info(os.linesep.join(execept_msgs))
            raise VerifyFailure("xstat-reset failed")

        self.logger.info("xstat-reset success !")

    def check_xstat_id_cmd(self, all_xstat_data):
        execept_msgs = []
        option = "xstats-id"
        sub_option = reduce(lambda x, y: str(x) + "," + str(y),
                            list(range(len(list(all_xstat_data['0'].keys())))))
        cmd = self.dpdk_proc_info + " --%s %s" % (option, sub_option)
        msg = self.d_a_con(cmd)
        sub_stat_data = self.parse_proc_info_xstat_output(msg)
        if not sub_stat_data or not len(sub_stat_data):
            execept_msgs.append([option, msg])
        else:
            for port, infos in list(sub_stat_data.items()):
                for item in infos:
                    if not port or \
                       port not in all_xstat_data or \
                       item not in all_xstat_data[port]:
                        msg1 = "port {0} get [{1}] failed".format(
                            port, item)
                        execept_msgs.append([msg1])
                        continue
        if len(execept_msgs):
            for msgs in execept_msgs:
                self.logger.error(msgs[0])
            raise VerifyFailure("query data exception ")

        self.logger.info("all ports stat id can get")
        time.sleep(1)

    def check_xstat_name_cmd(self, all_xstat_data):
        option = "xstats-name"
        _sub_options = list(all_xstat_data['0'].keys())
        execept_msgs = []
        for sub_option in _sub_options:
            cmd = self.dpdk_proc_info + " --%s %s" % (option, sub_option)
            msg = self.d_a_con(cmd)
            sub_stat_data = self.parse_proc_info_xstat_output(msg)
            if sub_option not in msg or not len(sub_stat_data):
                execept_msgs.append([option, msg])
            else:
                for port in sub_stat_data:
                    if sub_option not in sub_stat_data[port]:
                        msg = "{0} {1} data doesn't existed".format(
                            port, sub_option)
                        self.logger.error(msg)
                        continue
                    if not port or \
                       port not in all_xstat_data or \
                       sub_option not in all_xstat_data[port]:
                        msg1 = "port {0} [{1}]".format(port, sub_option)
                        execept_msgs.append([msg1])
                        continue
        if len(execept_msgs):
            for msgs in execept_msgs:
                self.logger.error(msgs[0])
                self.logger.info(msgs[1])
            raise VerifyFailure("query data exception ")

        self.logger.info("all port's stat value can get")

    def check_xstat_statistic_integrity(self, sub_options_ex=None):
        all_xstat_data = self.query_dpdk_xstat_all()
        self.check_xstat_id_cmd(all_xstat_data)
        self.check_xstat_name_cmd(all_xstat_data)

    def check_xstat_single_statistic(self, sub_options_ex=None):
        all_xstat_data = self.get_pmd_xstat_data()
        self.logger.info("total stat names [%d]" % len(all_xstat_data['0']))
        for stat_name in list(all_xstat_data['0'].keys()):
            # firstly, get statistic name.
            stats, execept_msgs = self.get_xstat_statistic_id(stat_name)
            if len(execept_msgs):
                for msgs in execept_msgs:
                    self.logger.error(msgs[0])
                    self.logger.info(msgs[1])
                continue
            self.logger.info(stat_name)
            self.get_xstat_single_statistic(stats['0'], all_xstat_data)

    def verify_xstat_command_options(self):
        ''' test xstat command set integrity '''
        except_content = None
        try:
            self.start_testpmd()
            self.set_testpmd()
            self.check_xstat_command_list()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_testpmd()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_xstat_reset(self):
        ''' test xstat-reset command '''
        except_content = None
        try:
            self.start_testpmd()
            self.set_testpmd()
            self.traffic()
            self.clear_pmd_ports_stat()
            self.check_xstat_reset_status()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_testpmd()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_xstat_integrity(self):
        ''' test xstat command '''
        except_content = None
        try:
            self.start_testpmd()
            self.set_testpmd()
            self.check_xstat_statistic_integrity()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_testpmd()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_xstat_single_statistic(self):
        except_content = None
        try:
            self.start_testpmd()
            self.set_testpmd()
            self.clear_pmd_ports_stat()
            self.traffic()
            self.check_xstat_single_statistic()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_testpmd()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def preset_test_environment(self):
        self.is_pmd_on = None
        # get link port pairs
        port_num = 0
        local_port = self.tester.get_local_port(port_num)
        self.link_topo = [
            self.tester.get_interface(local_port),
            self.tester.get_mac(local_port)]
        # set packet sizes for testing different type
        self.frame_sizes = [64, 72, 128, 256, 512, 1024]
        # init binary
        self.init_testpmd()
        self.init_proc_info()
    #
    # Test cases.
    #

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, 'Insufficient ports')
        self.prefix = "dpdk_" + self.dut.prefix_subfix
        self.preset_test_environment()

    def set_up(self):
        pass

    def tear_down(self):
        pass

    def tear_down_all(self):
        pass

    def test_xstat(self):
        ''' test xstat command set integrity '''
        self.verify_xstat_command_options()

    def test_xstat_integrity(self):
        ''' test xstat date types '''
        self.verify_xstat_integrity()

    def test_xstat_reset(self):
        ''' test xstat-reset command '''
        self.verify_xstat_reset()

    def test_xstat_single_statistic(self):
        ''' test xstat single data type '''
        self.verify_xstat_single_statistic()

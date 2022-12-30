# BSD LICENSE
#
# Copyright(c) 2022 Intel Corporation. All rights reserved.
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
Multi-process Test.
"""

import copy
import os
import random
import re
import time
import traceback
from collections import OrderedDict

import framework.utils as utils
from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, check_supported_nic
from framework.utils import GREEN, RED

from .rte_flow_common import FdirProcessing as fdirprocess
from .rte_flow_common import RssProcessing as rssprocess

executions = []


class TestMultiprocessIavf(TestCase):

    support_nic = ["ICE_100G-E810C_QSFP", "ICE_25G-E810C_SFP", "ICE_25G-E810_XXV_SFP"]

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Multiprocess prerequisites.
        Requirements:
            OS is not freeBSD
            DUT core number >= 4
            multi_process build pass
        """
        # self.verify('bsdapp' not in self.target, "Multiprocess not support freebsd")

        self.verify(len(self.dut.get_all_cores()) >= 4, "Not enough Cores")
        self.dut_ports = self.dut.get_ports()
        self.pkt = Packet()
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        extra_option = "-Dexamples='multi_process/client_server_mp/mp_server,multi_process/client_server_mp/mp_client,multi_process/simple_mp,multi_process/symmetric_mp'"
        self.dut.build_install_dpdk(target=self.target, extra_options=extra_option)
        self.app_mp_client = self.dut.apps_name["mp_client"]
        self.app_mp_server = self.dut.apps_name["mp_server"]
        self.app_simple_mp = self.dut.apps_name["simple_mp"]
        self.app_symmetric_mp = self.dut.apps_name["symmetric_mp"]

        executions.append({"nprocs": 1, "cores": "1S/1C/1T", "pps": 0})
        executions.append({"nprocs": 2, "cores": "1S/1C/2T", "pps": 0})
        executions.append({"nprocs": 2, "cores": "1S/2C/1T", "pps": 0})
        executions.append({"nprocs": 4, "cores": "1S/2C/2T", "pps": 0})
        executions.append({"nprocs": 4, "cores": "1S/4C/1T", "pps": 0})
        executions.append({"nprocs": 8, "cores": "1S/4C/2T", "pps": 0})

        self.dport_info0 = self.dut.ports_info[self.dut_ports[0]]
        self.dport_ifaces = self.dport_info0["intf"]
        self.create_vfs()
        self.port_pci_list = []
        for vf_port in self.sriov_vfs_port:
            self.port_pci_list.append(vf_port.pci)

        self.eal_para = self.dut.create_eal_parameters(
            cores="1S/2C/1T", ports=self.port_pci_list
        )
        # start new session to run secondary
        self.session_secondary = self.dut.new_session()

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

        self.tester_ifaces = [
            self.tester.get_interface(self.dut.ports_map[port])
            for port in self.dut_ports
        ]
        self.rxq = 1
        self.session_list = []
        self.logfmt = "*" * 20

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def create_vfs(self):
        self.dut.bind_interfaces_linux(self.kdriver)
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], 2)
        self.sriov_vfs_port = self.dut.ports_info[self.dut_ports[0]]["vfs_port"]
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.drivername)
            self.dut.send_expect("ifconfig {} up".format(self.dport_ifaces), "# ")
            self.dut.send_expect(
                "ip link set {} vf 0 mac {}".format(
                    self.dport_ifaces, "00:11:22:33:44:55"
                ),
                "# ",
            )
        except Exception as e:
            self.destroy_iavf()
            raise Exception(e)

    def destroy_iavf(self):
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
        for port in self.sriov_vfs_port:
            port.bind_driver(self.drivername)

    def launch_multi_testpmd(self, proc_type, queue_num, process_num, **kwargs):
        self.session_list = [
            self.dut.new_session("process_{}".format(i)) for i in range(process_num)
        ]
        self.pmd_output_list = [
            PmdOutput(self.dut, self.session_list[i]) for i in range(process_num)
        ]
        self.dut.init_reserved_core()
        proc_type_list = []
        self.out_list = []
        if isinstance(proc_type, list):
            proc_type_list = copy.deepcopy(proc_type)
            proc_type = proc_type_list[0]
        for i in range(process_num):
            cores = self.dut.get_reserved_core("2C", socket=0)
            if i != 0 and proc_type_list:
                proc_type = proc_type_list[1]
            eal_param = "--proc-type={} -a {} --log-level=ice,7".format(
                proc_type, self.sriov_vfs_port[0].pci
            )
            param = "--rxq={0} --txq={0} --num-procs={1} --proc-id={2}".format(
                queue_num, process_num, i
            )
            if kwargs.get("options") is not None:
                param = "".join([param, kwargs.get("options")])
            out = self.pmd_output_list[i].start_testpmd(
                cores=cores,
                eal_param=eal_param,
                param=param,
                timeout=kwargs.get("timeout", 20),
            )
            self.out_list.append(out)
            self.pmd_output_list[i].execute_cmd("set fwd rxonly")
            self.pmd_output_list[i].execute_cmd("set verbose 1")
            self.pmd_output_list[i].execute_cmd("start")
            self.pmd_output_list[i].execute_cmd("clear port stats all")

    def get_pkt_statistic_process(self, out, **kwargs):
        """
        :param out: information received by testpmd process after sending packets and port statistics
        :return: forward statistic dict, eg: {'rx-packets':1, 'tx-packets:0, 'tx-dropped':1}
        """
        p = re.compile(
            r"Forward\s+Stats\s+for\s+RX\s+Port=\s+{}/Queue=([\s\d+]\d+)\s+.*\n.*RX-packets:\s+(\d+)\s+TX-packets:\s+(\d+)\s+TX-dropped:\s+(\d+)\s".format(
                kwargs.get("port_id")
            )
        )
        item_name = ["rx-packets", "tx-packets", "tx-dropped"]
        statistic = p.findall(out)
        if statistic:
            rx_pkt_total, tx_pkt_total, tx_drop_total = 0, 0, 0
            queue_set = set()
            for item in statistic:
                queue, rx_pkt, tx_pkt, tx_drop = map(int, item)
                queue_set.add(queue)
                rx_pkt_total += rx_pkt
                tx_pkt_total += tx_pkt
                tx_drop_total += tx_drop
            static_dict = {
                k: v
                for k, v in zip(item_name, [rx_pkt_total, tx_pkt_total, tx_drop_total])
            }
            static_dict["queue"] = queue_set
            return static_dict
        else:
            raise Exception("got wrong output, not match pattern {}".format(p.pattern))

    def random_packet(self, pkt_num):
        pkt = Packet()
        pkt.generate_random_pkts(
            pktnum=pkt_num,
            dstmac="00:11:22:33:44:55",
        )
        pkt.send_pkt(crb=self.tester, tx_port=self.tester_ifaces[0], count=1)

    def specify_packet(self, que_num):
        # create rule to set queue as one of each process queues
        rule_str = "flow create 0 ingress pattern eth / ipv4 src is 192.168.{0}.3  / end actions queue index {0} / end"
        rules = [rule_str.format(i) for i in range(que_num)]
        fdirprocess(
            self, self.pmd_output_list[0], self.tester_ifaces, rxq=que_num
        ).create_rule(rules)
        # send 1 packet for each queue,the number of packets should be received by each process is (queue_num/proc_num)
        pkt = Packet()
        pkt_num = que_num
        self.logger.info("packet num:{}".format(pkt_num))
        packets = [
            'Ether(dst="00:11:22:33:44:55") / IP(src="192.168.{0}.3", dst="192.168.0.21") / Raw("x" * 80)'.format(
                i
            )
            for i in range(pkt_num)
        ]
        pkt.update_pkt(packets)
        pkt.send_pkt(crb=self.tester, tx_port=self.tester_ifaces[0], count=1)

    def _multiprocess_data_pass(self, case):
        que_num, proc_num = case.get("queue_num"), case.get("proc_num")
        pkt_num = case.setdefault("pkt_num", que_num)
        step = int(que_num / proc_num)
        proc_queue = [set(range(i, i + step)) for i in range(0, que_num, step)]
        queue_dict = {
            k: v
            for k, v in zip(
                ["process_{}".format(i) for i in range(que_num)], proc_queue
            )
        }
        # start testpmd multi-process
        self.launch_multi_testpmd(
            proc_type=case.get("proc_type"), queue_num=que_num, process_num=proc_num
        )
        # send random or specify packets
        packet_func = getattr(self, case.get("packet_type") + "_packet")
        packet_func(pkt_num)
        # get output for each process
        process_static = {}
        for i in range(len(self.pmd_output_list)):
            out = self.pmd_output_list[i].execute_cmd("stop")
            static = self.get_pkt_statistic_process(out, port_id=0)
            process_static["process_{}".format(i)] = static
        self.logger.info("process output static:{}".format(process_static))
        # check whether each process receives packet, and ecah process receives packets with the corresponding queue
        for k, v in process_static.items():
            self.verify(
                v.get("rx-packets") > 0,
                "fail:process:{} does not receive packet".format(k),
            )
            self.verify(
                v.get("queue").issubset(queue_dict.get(k)),
                "fail: {} is not a subset of {}, "
                "process should use its own queues".format(
                    v.get("queue"), queue_dict.get(k)
                ),
            )
        self.logger.info("pass:each process receives packets and uses its own queue")
        # check whether the sum of packets received by all processes is equal to the number of packets sent
        received_pkts = sum(
            int(v.get("rx-packets", 0)) for v in process_static.values()
        )
        self.verify(
            received_pkts == pkt_num,
            "the number of packets received is not equal to packets sent,"
            "send packet:{}, received packet:{}".format(pkt_num, received_pkts),
        )
        self.logger.info(
            "pass:the number of packets received is {}, equal to packets sent".format(
                received_pkts
            )
        )

    def check_rss(self, out, **kwargs):
        """
        check whether the packet directed by rss or not according to the specified parameters
        :param out: information received by testpmd after sending packets and port statistics
        :param kwargs: some specified parameters, such as: rxq, stats
        :return: queue value list
        usage:
            check_rss(out, rxq=rxq, stats=stats)
        """
        self.logger.info("{0} check rss {0}".format(self.logfmt))
        rxq = kwargs.get("rxq")
        p = re.compile("RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)")
        pkt_info = p.findall(out)
        self.verify(
            pkt_info,
            "no information matching the pattern was found,pattern:{}".format(
                p.pattern
            ),
        )
        pkt_queue = set([int(i[1], 16) for i in pkt_info])
        if kwargs.get("stats"):
            self.verify(
                all([int(i[0], 16) % rxq == int(i[1], 16) for i in pkt_info]),
                "some pkt not directed by rss.",
            )
            self.logger.info((GREEN("pass: all pkts directed by rss")))
        else:
            self.verify(
                not any([int(i[0], 16) % rxq == int(i[1], 16) for i in pkt_info]),
                "some pkt directed by rss, expect not directed by rss",
            )
            self.logger.info((GREEN("pass: no pkt directed by rss")))
        return pkt_queue

    def check_mark_id(self, out, check_param, **kwargs):
        """
        verify that the mark ID matches the expected value
        :param out: information received by testpmd after sending packets
        :param check_param: check item name and value, eg
                            "check_param": {"port_id": 0, "mark_id": 1}
        :param kwargs: some specified parameters,eg: stats
        :return: None
        usage:
            check_mark_id(out, check_param, stats=stats)
        """
        self.logger.info("{0} check mark id {0}".format(self.logfmt))
        fdir_scanner = re.compile("FDIR matched ID=(0x\w+)")
        all_mark = fdir_scanner.findall(out)
        stats = kwargs.get("stats")
        if stats:
            mark_list = set(int(i, 16) for i in all_mark)
            self.verify(
                all([i == check_param["mark_id"] for i in mark_list]) and mark_list,
                "failed: some packet mark id of {} not match expect {}".format(
                    mark_list, check_param["mark_id"]
                ),
            )
            self.logger.info((GREEN("pass: all packets mark id are matched ")))
        else:
            # for mismatch packet,verify no mark id in output of received packet
            self.verify(
                not all_mark, "mark id {} in output, expect no mark id".format(all_mark)
            )
            self.logger.info((GREEN("pass: no mark id in output")))

    def check_drop(self, out, **kwargs):
        """
        check the drop number of packets according to the specified parameters
        :param out: information received by testpmd after sending packets and port statistics
        :param kwargs: some specified parameters, such as: pkt_num, port_id, stats
        :return: None
        usage:
            chek_drop(out, pkt_num=pkt_num, port_id=portid, stats=stats)
        """
        self.logger.info("{0} check drop {0}".format(self.logfmt))
        pkt_num = kwargs.get("pkt_num")
        stats = kwargs.get("stats")
        res = self.get_pkt_statistic(out, **kwargs)
        self.verify(
            pkt_num == res["rx-total"],
            "failed: get wrong amount of packet {}, expected {}".format(
                res["rx-total"], pkt_num
            ),
        )
        drop_packet_num = res["rx-dropped"]
        if stats:
            self.verify(
                drop_packet_num == pkt_num,
                "failed: {} packet dropped,expect {} dropped".format(
                    drop_packet_num, pkt_num
                ),
            )
            self.logger.info(
                (
                    GREEN(
                        "pass: drop packet number {} is matched".format(drop_packet_num)
                    )
                )
            )
        else:
            self.verify(
                drop_packet_num == 0 and res["rx-packets"] == pkt_num,
                "failed: {} packet dropped, expect 0 packet dropped".format(
                    drop_packet_num
                ),
            )
            self.logger.info(
                (
                    GREEN(
                        "pass: drop packet number {} is matched".format(drop_packet_num)
                    )
                )
            )

    @staticmethod
    def get_pkt_statistic(out, **kwargs):
        """
        :param out: information received by testpmd after sending packets and port statistics
        :return: rx statistic dict, eg: {'rx-packets':1, 'rx-dropped':0, 'rx-total':1}
        """
        p = re.compile(
            r"Forward\sstatistics\s+for\s+port\s+{}\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s(\d+)\s+RX-total:\s(\d+)\s".format(
                kwargs.get("port_id")
            )
        )
        item_name = ["rx-packets", "rx-dropped", "rx-total"]
        statistic = p.findall(out)
        if statistic:
            static_dict = {
                k: v for k, v in zip(item_name, list(map(int, list(statistic[0]))))
            }
            return static_dict
        else:
            raise Exception(
                "got wrong output, not match pattern {}".format(p.pattern).replace(
                    "\\\\", "\\"
                )
            )

    def send_pkt_get_output(
        self, instance_obj, pkts, port_id=0, count=1, interval=0, get_stats=False
    ):
        instance_obj.pmd_output.execute_cmd("clear port stats all")
        tx_port = self.tester_ifaces[port_id]
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        if not isinstance(pkts, list):
            pkts = [pkts]
        self.pkt.update_pkt(pkts)
        self.pkt.send_pkt(
            crb=self.tester,
            tx_port=tx_port,
            count=count,
            interval=interval,
        )
        out1 = instance_obj.pmd_output.get_output(timeout=1)
        if get_stats:
            out2 = instance_obj.pmd_output.execute_cmd("show port stats all")
            instance_obj.pmd_output.execute_cmd("stop")
        else:
            out2 = instance_obj.pmd_output.execute_cmd("stop")
        instance_obj.pmd_output.execute_cmd("start")
        return "".join([out1, out2])

    def check_pkt_num(self, out, **kwargs):
        """
        check number of received packets matches the expected value
        :param out: information received by testpmd after sending packets and port statistics
        :param kwargs: some specified parameters, such as: pkt_num, port_id
        :return: rx statistic dict
        """
        self.logger.info(
            "{0} check pkt num for port:{1} {0}".format(
                self.logfmt, kwargs.get("port_id")
            )
        )
        pkt_num = kwargs.get("pkt_num")
        res = self.get_pkt_statistic(out, **kwargs)
        res_num = res["rx-packets"]
        self.verify(
            res_num == pkt_num,
            "fail: got wrong number of packets, expect pakcet number {}, got {}".format(
                pkt_num, res_num
            ),
        )
        self.logger.info(
            (GREEN("pass: pkt num is {} same as expected".format(pkt_num)))
        )
        return res

    def check_queue(self, out, check_param, **kwargs):
        """
        verify that queue value matches the expected value
        :param out: information received by testpmd after sending packets and port statistics
        :param check_param: check item name and value, eg
                            "check_param": {"port_id": 0, "queue": 2}
        :param kwargs: some specified parameters, such as: pkt_num, port_id, stats
        :return:
        """
        self.logger.info("{0} check queue {0}".format(self.logfmt))
        queue = check_param["queue"]
        if isinstance(check_param["queue"], int):
            queue = [queue]
        patt = re.compile(
            r"port\s+{}/queue(.+?):\s+received\s+(\d+)\s+packets".format(
                kwargs.get("port_id")
            )
        )
        res = patt.findall(out)
        if res:
            pkt_queue = set([int(i[0]) for i in res])
            if kwargs.get("stats"):
                self.verify(
                    all(q in queue for q in pkt_queue),
                    "fail: queue id not matched, expect queue {}, got {}".format(
                        queue, pkt_queue
                    ),
                )
                self.logger.info((GREEN("pass: queue id {} matched".format(pkt_queue))))
            else:
                try:
                    self.verify(
                        not any(q in queue for q in pkt_queue),
                        "fail: queue id should not matched, {} should not in {}".format(
                            pkt_queue, queue
                        ),
                    )
                    self.logger.info(
                        (GREEN("pass: queue id {} not matched".format(pkt_queue)))
                    )
                except VerifyFailure:
                    self.logger.info(
                        "queue id {} contains the queue {} specified in rule, so need to check"
                        " whether the packet directed by rss or not".format(
                            pkt_queue, queue
                        )
                    )
                    # for mismatch packet the 'stats' parameter is False, need to change to True
                    kwargs["stats"] = True
                    self.check_rss(out, **kwargs)

        else:
            raise Exception("got wrong output, not match pattern")

    def check_with_param(self, out, pkt_num, check_param, stats=True):
        """
        according to the key and value of the check parameter,
        perform the corresponding verification in the out information
        :param out: information received by testpmd after sending packets and port statistics
        :param pkt_num: number of packets sent
        :param check_param: check item name and value, eg:
                            "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
                            "check_param": {"port_id": 0, "drop": 1}
        :param stats: effective status of rule, True or False, default is True
        :return:
        usage:
            check_with_param(out, pkt_num, check_param, stats)
            check_with_param(out, pkt_num, check_param=check_param)
        """
        rxq = check_param.get("rxq")
        port_id = (
            check_param["port_id"] if check_param.get("port_id") is not None else 0
        )
        match_flag = True
        """
        check_dict shows the supported check items,the key is item name and value represent the check priority,
        the smaller the value, the higher the priority, priority default value is 999. if need to add new check item,
        please add it to the dict and implement the corresponding method and named as 'check_itemname',eg: check_queue
        """
        self.matched_queue = []
        default_pri = 999
        check_dict = {
            "queue": default_pri,
            "drop": default_pri,
            "mark_id": 1,
            "rss": default_pri,
        }
        params = {"port_id": port_id, "rxq": rxq, "pkt_num": pkt_num, "stats": stats}
        # sort check_param order by priority, from high to low, set priority as 999 if key not in check_dict
        check_param = OrderedDict(
            sorted(
                check_param.items(),
                key=lambda item: check_dict.get(item[0], default_pri),
            )
        )
        if not check_param.get("drop"):
            self.check_pkt_num(out, **params)
        for k in check_param:
            parameter = copy.deepcopy(params)
            if k not in check_dict:
                continue
            func_name = "check_{}".format(k)
            try:
                func = getattr(self, func_name)
            except AttributeError:
                emsg = "{},this func is not implemented, please check!".format(
                    traceback.format_exc()
                )
                raise Exception(emsg)
            else:
                # for mismatch packet, if the check item is 'rss',should also verify the packets are distributed by rss
                if k == "rss" and not stats:
                    parameter["stats"] = True
                    match_flag = False
                res = func(out=out, check_param=check_param, **parameter)
                if k == "rss" and match_flag:
                    self.matched_queue.append(res)

    def destroy_rule(self, instance_obj, port_id=0, rule_id=None):
        rule_id = 0 if rule_id is None else rule_id
        if not isinstance(rule_id, list):
            rule_id = [rule_id]
        for i in rule_id:
            out = instance_obj.pmd_output.execute_cmd(
                "flow destroy {} rule {}".format(port_id, i)
            )
            p = re.compile(r"Flow rule #(\d+) destroyed")
            m = p.search(out)
            self.verify(m, "flow rule {} delete failed".format(rule_id))

    def multiprocess_flow_data(self, case, **pmd_param):
        que_num, proc_num = pmd_param.get("queue_num"), pmd_param.get("proc_num")
        # start testpmd multi-process
        self.launch_multi_testpmd(
            proc_type=pmd_param.get("proc_type"),
            queue_num=que_num,
            process_num=proc_num,
        )
        self.pmd_output_list[0].execute_cmd("flow flush 0")
        check_param = case["check_param"]
        check_param["rxq"] = pmd_param.get("queue_num")
        if check_param.get("rss"):
            [pmd.execute_cmd("port config all rss all") for pmd in self.pmd_output_list]
        fdir_pro = fdirprocess(
            self,
            self.pmd_output_list[0],
            self.tester_ifaces,
            rxq=pmd_param.get("queue_num"),
        )
        fdir_pro.create_rule(case.get("rule"))
        # send match and mismatch packet
        packets = [case.get("packet")["match"], case.get("packet")["mismatch"]]
        for i in range(2):
            out1 = self.send_pkt_get_output(fdir_pro, packets[i])
            patt = re.compile(
                r"port\s+{}/queue(.+?):\s+received\s+(\d+)\s+packets".format(
                    check_param.get("port_id")
                )
            )
            if patt.findall(out1) and check_param.get("rss"):
                self.logger.info(
                    "check whether the packets received by the primary process are distributed by RSS"
                )
                self.check_rss(out1, stats=True, **check_param)
            for proc_pmd in self.pmd_output_list[1:]:
                out2 = proc_pmd.get_output(timeout=1)
                out3 = proc_pmd.execute_cmd("stop")
                out1 = "".join([out1, out2, out3])
                proc_pmd.execute_cmd("start")
                if patt.findall(out2) and check_param.get("rss"):
                    self.logger.info(
                        "check whether the packets received by the secondary process are distributed by RSS"
                    )
                    self.check_rss(out2, stats=True, **check_param)
            pkt_num = len(packets[i])
            self.check_with_param(
                out1,
                pkt_num=pkt_num,
                check_param=check_param,
                stats=True if i == 0 else False,
            )

    def _handle_test(self, tests, instance_obj, port_id=0):
        for test in tests:
            if "send_packet" in test:
                out = self.send_pkt_get_output(
                    instance_obj, test["send_packet"], port_id
                )
                for proc_pmd in self.pmd_output_list[1:]:
                    out1 = proc_pmd.get_output(timeout=1)
                    out = "".join([out, out1])
            if "action" in test:
                instance_obj.handle_actions(out, test["action"])

    def multiprocess_rss_data(self, case, **pmd_param):
        que_num, proc_num = pmd_param.get("queue_num"), pmd_param.get("proc_num")
        # start testpmd multi-process
        self.launch_multi_testpmd(
            proc_type=pmd_param.get("proc_type"),
            queue_num=que_num,
            process_num=proc_num,
            options=pmd_param.get("options", None),
        )
        self.pmd_output_list[0].execute_cmd("flow flush 0")
        rss_pro = rssprocess(
            self,
            self.pmd_output_list[0],
            self.tester_ifaces,
            rxq=pmd_param.get("queue_num"),
        )
        rss_pro.error_msgs = []
        # handle tests
        tests = case["test"]
        port_id = case["port_id"]
        self.logger.info("------------handle test--------------")
        # validate rule
        rule = case.get("rule", None)
        if rule:
            rss_pro.validate_rule(rule=rule)
            rule_ids = rss_pro.create_rule(rule=rule)
            rss_pro.check_rule(rule_list=rule_ids)
        self._handle_test(tests, rss_pro, port_id)
        # handle post-test
        if "post-test" in case:
            self.logger.info("------------handle post-test--------------")
            self.destroy_rule(rss_pro, port_id=port_id, rule_id=rule_ids)
            rss_pro.check_rule(port_id=port_id, stats=False)
            self._handle_test(case["post-test"], rss_pro, port_id)

        if rss_pro.error_msgs:
            self.verify(
                False,
                " ".join([errs.replace("'", " ") for errs in rss_pro.error_msgs[:500]]),
            )

    def rte_flow(self, case_list, func_name, **kwargs):
        """
        main flow of case:
            1. iterate the case list and do the below steps:
                a. get the subcase name and init dict to save result
                b. call method by func name to execute case step
                c. record case result and err msg if case failed
                d. clear flow rule
            2. calculate the case passing rate according to the result dict
            3. record case result and pass rate in the case log file
            4. verify whether the case pass rate is equal to 100, if not, mark the case as failed and raise the err msg
        :param case_list: case list, each item is a subcase of case
        :param func_name: hadle case method name, eg:
                        'flow_rule_operate': a method of 'FlowRuleProcessing' class,
                        used to handle flow rule related suites,such as fdir and switch_filter
                        'handle_rss_distribute_cases': a method of 'RssProcessing' class,
                        used to handle rss related suites
        :return:
        usage:
        for flow rule related:
            rte_flow(caselist, flow_rule_operate)
        for rss related:
            rte_flow(caselist, handle_rss_distribute_cases)
        """
        if not isinstance(case_list, list):
            case_list = [case_list]
        test_results = dict()
        for case in case_list:
            case_name = case.get("sub_casename")
            test_results[case_name] = {}
            try:
                self.logger.info("{0} case_name:{1} {0}".format("*" * 20, case_name))
                func_name(case, **kwargs)
            except Exception:
                test_results[case_name]["result"] = "failed"
                test_results[case_name]["err"] = re.sub(
                    r"['\r\n]", "", str(traceback.format_exc(limit=1))
                ).replace("\\\\", "\\")
                self.logger.info(
                    (
                        RED(
                            "case failed:{}, err:{}".format(
                                case_name, traceback.format_exc()
                            )
                        )
                    )
                )
            else:
                test_results[case_name]["result"] = "passed"
                self.logger.info((GREEN("case passed: {}".format(case_name))))
            finally:
                self.pmd_output_list[0].execute_cmd("flow flush 0")
                for sess in self.session_list:
                    self.dut.close_session(sess)
        pass_rate = (
            round(
                sum(1 for k in test_results if "passed" in test_results[k]["result"])
                / len(test_results),
                4,
            )
            * 100
        )
        self.logger.info(
            [
                "{}:{}".format(sub_name, test_results[sub_name]["result"])
                for sub_name in test_results
            ]
        )
        self.logger.info("pass rate is: {}".format(pass_rate))
        msg = [
            "subcase_name:{}:{},err:{}".format(
                name, test_results[name].get("result"), test_results[name].get("err")
            )
            for name in test_results.keys()
            if "failed" in test_results[name]["result"]
        ]
        self.verify(
            int(pass_rate) == 100,
            "some subcases failed, detail as below:{}".format(msg),
        )

    def test_multiprocess_simple_mpbasicoperation(self):
        """
        Basic operation.
        """
        # Send message from secondary to primary
        cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)
        coremask = utils.create_mask(cores)
        self.dut.send_expect(
            self.app_simple_mp + " %s --proc-type=primary" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        self.session_secondary.send_expect(
            self.app_simple_mp + " %s --proc-type=secondary" % (self.eal_para),
            "Finished Process Init",
            100,
        )

        self.session_secondary.send_expect("send hello_primary", ">")
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")
        self.verify(
            "Received 'hello_primary'" in out, "Message not received on primary process"
        )
        # Send message from primary to secondary
        cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)
        coremask = utils.create_mask(cores)
        self.session_secondary.send_expect(
            self.app_simple_mp + " %s --proc-type=primary " % (self.eal_para),
            "Finished Process Init",
            100,
        )
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        self.dut.send_expect(
            self.app_simple_mp + " %s --proc-type=secondary" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        self.session_secondary.send_expect("send hello_secondary", ">")
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")

        self.verify(
            "Received 'hello_secondary'" in out,
            "Message not received on primary process",
        )

    def test_multiprocess_simple_mploadtest(self):
        """
        Load test of Simple MP application.
        """

        cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)
        coremask = utils.create_mask(cores)
        self.session_secondary.send_expect(
            self.app_simple_mp + " %s --proc-type=primary" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        self.dut.send_expect(
            self.app_simple_mp + " %s --proc-type=secondary" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        stringsSent = 0
        for line in open("/usr/share/dict/words", "r").readlines():
            line = line.split("\n")[0]
            self.dut.send_expect("send %s" % line, ">")
            stringsSent += 1
            if stringsSent == 3:
                break

        time.sleep(5)
        self.dut.send_expect("quit", "# ")
        self.session_secondary.send_expect("quit", "# ")

    def test_multiprocess_simple_mpapplicationstartup(self):
        """
        Test use of Auto for Application Startup.
        """

        # Send message from secondary to primary (auto process type)
        cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)
        coremask = utils.create_mask(cores)
        out = self.dut.send_expect(
            self.app_simple_mp + " %s --proc-type=auto " % (self.eal_para),
            "Finished Process Init",
            100,
        )
        self.verify(
            "EAL: Auto-detected process type: PRIMARY" in out,
            "The type of process (PRIMARY) was not detected properly",
        )
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        out = self.session_secondary.send_expect(
            self.app_simple_mp + " %s --proc-type=auto" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        self.verify(
            "EAL: Auto-detected process type: SECONDARY" in out,
            "The type of process (SECONDARY) was not detected properly",
        )

        self.session_secondary.send_expect("send hello_primary", ">")
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")
        self.verify(
            "Received 'hello_primary'" in out, "Message not received on primary process"
        )

        # Send message from primary to secondary (auto process type)
        cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)
        coremask = utils.create_mask(cores)
        out = self.session_secondary.send_expect(
            self.app_simple_mp + " %s --proc-type=auto" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        self.verify(
            "EAL: Auto-detected process type: PRIMARY" in out,
            "The type of process (PRIMARY) was not detected properly",
        )
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        out = self.dut.send_expect(
            self.app_simple_mp + " %s --proc-type=auto" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        self.verify(
            "EAL: Auto-detected process type: SECONDARY" in out,
            "The type of process (SECONDARY) was not detected properly",
        )
        self.session_secondary.send_expect("send hello_secondary", ">", 100)
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")

        self.verify(
            "Received 'hello_secondary'" in out,
            "Message not received on primary process",
        )

    def test_multiprocess_simple_mpnoflag(self):
        """
        Multiple processes without "--proc-type" flag.
        """

        cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)
        coremask = utils.create_mask(cores)
        self.session_secondary.send_expect(
            self.app_simple_mp + " %s -m 64" % (self.eal_para),
            "Finished Process Init",
            100,
        )
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        out = self.dut.send_expect(
            self.app_simple_mp + " %s" % (self.eal_para), "# ", 100
        )

        self.verify(
            "Is another primary process running" in out,
            "No other primary process detected",
        )

        self.session_secondary.send_expect("quit", "# ")

    def test_multiprocess_symmetric_mp_packet(self):
        # run multiple symmetric_mp process
        portMask = utils.create_mask(self.dut_ports)
        # launch symmetric_mp, process num is 2
        proc_num = 2
        session_list = [
            self.dut.new_session("process_{}".format(i)) for i in range(proc_num)
        ]
        port_param = ""
        for port_pci in self.port_pci_list:
            port_param += " -a {}".format(port_pci)
        for i in range(proc_num):
            session_list[i].send_expect(
                self.app_symmetric_mp
                + " -l {} -n 4 --proc-type=auto {} -- -p {} --num-procs={} --proc-id={}".format(
                    i + 1, port_param, portMask, proc_num, i
                ),
                "Finished Process Init",
            )
        # send packets
        packet_num = random.randint(20, 256)
        self.logger.info("packet num:{}".format(packet_num))
        self.random_packet(packet_num)
        res = []
        for session_obj in session_list:
            try:
                out = session_obj.send_command("^C")
            except Exception as e:
                self.logger.err("Error occured:{}".format(traceback.format_exc(e)))
            finally:
                session_obj.close()
            rx_num = re.search(r"Port 0: RX - (?P<RX>\d+)", out)
            rx_nums = int(rx_num.group("RX"))
            self.verify(
                rx_nums > 0,
                "fail: {} received packets shoud greater than 0, actual is {}".format(
                    session_obj.name, rx_nums
                ),
            )
            res.append(rx_nums)
        rx_total = sum(res)
        self.logger.info("RX total:{}, send packet:{}".format(rx_total, packet_num))
        self.verify(
            rx_total >= packet_num,
            "some packet not received by symmetric_mp, "
            "number of RX total should greater than or equal to send packet",
        )

    def test_multiprocess_server_client_mp_packet(self):
        # run multiple client_server_mp process
        portMask = utils.create_mask(self.dut_ports)
        # launch client_server_mp, client process num is 2
        proc_num = 2
        session_list = [
            self.dut.new_session("process_{}".format(i)) for i in range(proc_num + 1)
        ]
        server_session = session_list[-1]
        # start server
        server_session.send_expect(
            self.app_mp_server
            + " -l 1,2 -n 4 -- -p {} -n {}".format(portMask, proc_num),
            "Finished Process Init",
        )
        # start client
        for i in range(proc_num):
            self.dut.init_reserved_core()
            session_list[i].send_expect(
                self.app_mp_client
                + " -l {} -n 4 --proc-type=auto -- -n {}".format(i + 3, i),
                "Finished Process Init",
            )
        # send packets
        packet_num = random.randint(20, 256)
        self.logger.info("packet num:{}".format(packet_num))
        self.random_packet(packet_num)
        out = server_session.get_session_before(timeout=5)
        for session_obj in session_list:
            try:
                session_obj.send_command("^C")
            except Exception as e:
                self.logger.err("Error occured:{}".format(traceback.format_exc(e)))
            finally:
                session_obj.close()
        res = re.search(
            r"Port \d+\s+-\s+rx:\s+(?P<rx>\d+)\s+tx:.*PORTS", out, re.DOTALL
        )
        rx_num = re.findall(r"Client\s+\d\s+-\s+rx:\s+(\d+)", res.group(0))
        rx_num.sort(reverse=True)
        for i in range(proc_num):
            self.verify(
                int(rx_num[i]) > 0,
                "fail: client_{} received packets shoud greater than 0, "
                "actual is {}".format(i, int(rx_num[i])),
            )
        rx_total = sum(int(rx) for rx in rx_num)
        self.logger.info("rx total:{}, send packet:{}".format(rx_total, packet_num))
        self.verify(
            rx_total >= packet_num,
            "some packet not received by server_client process,"
            "number of RX total should greater than or equal to send packet.",
        )

    # test testpmd multi-process
    @check_supported_nic(support_nic)
    def test_multiprocess_auto_process_type_detected(self):
        # start 2 process
        self.launch_multi_testpmd("auto", 8, 2)
        # get output of each process and check the detected process type is correctly
        process_type = ["PRIMARY", "SECONDARY"]
        for i in range(2):
            self.verify(
                "Auto-detected process type: {}".format(process_type[i])
                in self.out_list[i],
                "the process type is not correctly, expect {}".format(process_type[i]),
            )
            self.logger.info(
                "pass: Auto-detected {} process type correctly".format(process_type[i])
            )

    @check_supported_nic(support_nic)
    def test_multiprocess_negative_2_primary_process(self):
        # start 2 primary process
        try:
            self.launch_multi_testpmd(["primary", "primary"], 8, 2, timeout=10)
        except Exception as e:
            # check second process start failed
            self.verify(
                "Is another primary process running?" in e.output,
                "fail: More than one primary process was started, only one should be started!",
            )
            self.logger.info(
                "pass: only one primary process start successfully, match the expect"
            )
            return
        self.verify(False, "fail: 2 primary process launch succeed, expect launch fail")

    @check_supported_nic(support_nic)
    def test_multiprocess_negative_exceed_process_num(self):
        """
        If the specified number of processes is exceeded, starting the process will fail
        """
        # start 2 process
        proc_type, queue_num, process_num = "auto", 8, 2
        self.launch_multi_testpmd(proc_type, queue_num, process_num)
        # start a process with 'proc-id=2', should start failed
        pmd_2 = PmdOutput(self.dut, self.dut.new_session("process_2"))
        self.dut.init_reserved_core()
        cores = self.dut.get_reserved_core("2C", socket=1)
        eal_param = "--proc-type={} -a {} --log-level=ice,7".format(
            "auto", self.sriov_vfs_port[0].pci
        )
        param = "--rxq={0} --txq={0} --num-procs={1} --proc-id={2}".format(
            queue_num, process_num, 2
        )
        try:
            pmd_2.start_testpmd(
                cores=cores, eal_param=eal_param, param=param, timeout=10
            )
        except Exception as e:
            p = re.compile(
                r"The\s+multi-process\s+option\s+'proc-id\(\d+\)'\s+should\s+be\s+less\s+than\s+'num-procs\(\d+\)'"
            )
            res = p.search(e.output)
            self.verify(
                res,
                "fail: 'multi-process proc-id should be less than num-process' should in output",
            )
            self.logger.info(
                "pass: exceed the specified number, process launch failed as expected"
            )
            return
        self.verify(
            False,
            "fail: exceed the specified number, process launch succeed, expect launch fail",
        )

    @check_supported_nic(support_nic)
    def test_multiprocess_proc_type_random_packet(self):
        case_list = [
            {
                "sub_casename": "proc_type_auto_4_process",
                "queue_num": 16,
                "proc_num": 4,
                "proc_type": "auto",
                "packet_type": "random",
                "pkt_num": 30,
            },
            {
                "sub_casename": "proc_type_primary_secondary_2_process",
                "queue_num": 4,
                "proc_num": 2,
                "proc_type": ["primary", "secondary"],
                "packet_type": "random",
                "pkt_num": 20,
            },
        ]
        self.rte_flow(case_list, self._multiprocess_data_pass)

    @check_supported_nic(support_nic)
    def test_multiprocess_proc_type_specify_packet(self):
        case_list = [
            {
                "sub_casename": "proc_type_auto_2_process",
                "queue_num": 8,
                "proc_num": 2,
                "proc_type": "auto",
                "packet_type": "specify",
            },
            {
                "sub_casename": "proc_type_primary_secondary_3_process",
                "queue_num": 6,
                "proc_num": 3,
                "proc_type": ["primary", "secondary"],
                "packet_type": "specify",
            },
        ]
        self.rte_flow(case_list, self._multiprocess_data_pass)

    @check_supported_nic(support_nic)
    def test_multiprocess_with_fdir_rule(self):
        pmd_param = {
            "queue_num": 64,
            "proc_num": 2,
            "proc_type": "auto",
        }
        MAC_IPV4_PAY = {
            "match": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)'
            ],
            "mismatch": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.1.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1, ttl=2, tos=4) / Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=3, tos=4) / Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=9) / Raw("x" * 80)',
            ],
        }
        mac_ipv4_pay_queue_index = {
            "sub_casename": "mac_ipv4_pay_queue_index",
            "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 6 / mark id 4 / end",
            "packet": MAC_IPV4_PAY,
            "check_param": {"port_id": 0, "queue": 6, "mark_id": 4},
        }
        mac_ipv4_pay_drop = {
            "sub_casename": "mac_ipv4_pay_drop",
            "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / mark / end",
            "packet": MAC_IPV4_PAY,
            "check_param": {"port_id": 0, "drop": True},
        }
        mac_ipv4_pay_rss_queues = {
            "sub_casename": "mac_ipv4_pay_rss_queues",
            "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 10 11 end / mark / end",
            "packet": MAC_IPV4_PAY,
            "check_param": {"port_id": 0, "queue": [10, 11]},
        }
        mac_ipv4_pay_mark_rss = {
            "sub_casename": "mac_ipv4_pay_mark_rss",
            "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end",
            "packet": MAC_IPV4_PAY,
            "check_param": {"port_id": 0, "mark_id": 0, "rss": True},
        }
        case_list = [
            mac_ipv4_pay_queue_index,
            mac_ipv4_pay_drop,
            mac_ipv4_pay_rss_queues,
            mac_ipv4_pay_mark_rss,
        ]
        self.rte_flow(case_list, self.multiprocess_flow_data, **pmd_param)

    @check_supported_nic(support_nic)
    def test_multiprocess_with_rss_toeplitz(self):
        pmd_param = {
            "queue_num": 32,
            "proc_num": 2,
            "proc_type": "auto",
            "options": " --disable-rss --rxd=384 --txd=384",
        }
        mac_ipv4_tcp_toeplitz_basic_pkt = {
            "ipv4-tcp": [
                'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            ],
        }
        mac_ipv4_tcp_l2_src = {
            "sub_casename": "mac_ipv4_tcp_l2_src",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E1", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l2_dst = {
            "sub_casename": "mac_ipv4_tcp_l2_dst",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E1", dst="00:11:22:33:44:55")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l2src_l2dst = {
            "sub_casename": "mac_ipv4_tcp_l2src_l2dst",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E1", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
            ],
        }
        mac_ipv4_tcp_l3_src = {
            "sub_casename": "mac_ipv4_tcp_l3_src",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l3_dst = {
            "sub_casename": "mac_ipv4_tcp_l3_dst",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l3src_l4src = {
            "sub_casename": "mac_ipv4_tcp_l3src_l4src",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l3src_l4dst = {
            "sub_casename": "mac_ipv4_tcp_l3src_l4dst",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l3dst_l4src = {
            "sub_casename": "mac_ipv4_tcp_l3dst_l4src",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l3dst_l4dst = {
            "sub_casename": "mac_ipv4_tcp_l3dst_l4dst",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l4_src = {
            "sub_casename": "mac_ipv4_tcp_l4_src",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_l4_dst = {
            "sub_casename": "mac_ipv4_tcp_l4_dst",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_all = {
            "sub_casename": "mac_ipv4_tcp_all",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="00:11:22:33:44:55", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }
        mac_ipv4_tcp_ipv4 = {
            "sub_casename": "mac_ipv4_tcp_ipv4",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": mac_ipv4_tcp_toeplitz_basic_pkt["ipv4-tcp"],
                    "action": "save_hash",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_different",
                },
                {
                    "send_packet": 'Ether(src="68:05:CA:BB:26:E0", dst="00:11:22:33:44:55")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
                    "action": "check_hash_same",
                },
            ],
        }

        case_list = [
            mac_ipv4_tcp_l2_src,
            mac_ipv4_tcp_l2_dst,
            mac_ipv4_tcp_l2src_l2dst,
            mac_ipv4_tcp_l3_src,
            mac_ipv4_tcp_l3_dst,
            mac_ipv4_tcp_l3src_l4src,
            mac_ipv4_tcp_l3src_l4dst,
            mac_ipv4_tcp_l3dst_l4src,
            mac_ipv4_tcp_l3dst_l4dst,
            mac_ipv4_tcp_l4_src,
            mac_ipv4_tcp_l4_dst,
            mac_ipv4_tcp_all,
            mac_ipv4_tcp_ipv4,
        ]
        self.rte_flow(case_list, self.multiprocess_rss_data, **pmd_param)

    @check_supported_nic(support_nic)
    def test_multiprocess_with_rss_symmetric(self):
        pmd_param = {
            "queue_num": 16,
            "proc_num": 2,
            "proc_type": "auto",
            "symmetric": True,
        }
        packets = [
            'Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
        ]
        mac_ipv4_symmetric = {
            "sub_casename": "mac_ipv4_all",
            "port_id": 0,
            "rule": "flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
            "test": [
                {
                    "send_packet": packets[0],
                    "action": {"save_hash": "ipv4-nonfrag"},
                },
                {
                    "send_packet": packets[1],
                    "action": {"check_hash_same": "ipv4-nonfrag"},
                },
                {
                    "send_packet": packets[2],
                    "action": {"save_hash": "ipv4-tcp"},
                },
                {
                    "send_packet": packets[3],
                    "action": {"check_hash_same": "ipv4-tcp"},
                },
            ],
            "post-test": [
                {
                    "send_packet": packets[0],
                    "action": {"save_or_no_hash": "ipv4-nonfrag-post"},
                },
                {
                    "send_packet": packets[1],
                    "action": {"check_no_hash_or_different": "ipv4-nonfrag-post"},
                },
                {
                    "send_packet": packets[2],
                    "action": {"save_or_no_hash": "ipv4-tcp-post"},
                },
                {
                    "send_packet": packets[3],
                    "action": {"check_no_hash_or_different": "ipv4-tcp-post"},
                },
            ],
        }
        self.rte_flow(mac_ipv4_symmetric, self.multiprocess_rss_data, **pmd_param)

    def test_multiprocess_negative_action(self):
        """
        Test Case: test_multiprocess_negative_action

        """
        # start testpmd multi-process
        self.launch_multi_testpmd(
            proc_type="auto",
            queue_num=4,
            process_num=2,
        )
        for pmd_output in self.pmd_output_list:
            pmd_output.execute_cmd("stop")
        # set primary process port stop
        try:
            self.pmd_output_list[0].execute_cmd("port stop 0")
        except Exception as ex:
            out = ex.output
            self.logger.error(out)
            self.verify(
                "core dump" not in out, "Core dump occurred in the primary process!!!"
            )
        for pmd_output in self.pmd_output_list:
            pmd_output.quit()
        # start testpmd multi-process
        self.launch_multi_testpmd(
            proc_type="auto",
            queue_num=4,
            process_num=2,
        )
        for pmd_output in self.pmd_output_list:
            pmd_output.execute_cmd("stop")
        # reset port in secondary process
        try:
            self.pmd_output_list[1].execute_cmd("port stop 0")
            self.pmd_output_list[1].execute_cmd("port reset 0")
        except Exception as ex:
            out = ex.output
            self.logger.error(out)
            self.verify(
                "core dump" not in out, "Core dump occurred in the second process!!!"
            )

    def set_fields(self):
        """set ip protocol field behavior"""
        fields_config = {
            "ip": {
                "src": {"range": 64, "action": "inc"},
                "dst": {"range": 64, "action": "inc"},
            },
        }

        return fields_config

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.session_list:
            for sess in self.session_list:
                self.dut.close_session(sess)
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.destroy_iavf()

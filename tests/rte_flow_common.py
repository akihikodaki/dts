# BSD LICENSE
#
# Copyright(c) 2019-2020 Intel Corporation. All rights reserved.
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

import json
import re
import time

from framework.packet import Packet
from framework.utils import GREEN, RED

TXQ_RXQ_NUMBER = 16

# switch filter common functions
def get_suite_config(test_case):
    """
    get the suite config from $DTS_CFG_FOLDER/suite.cfg.
    """
    suite_config = {}
    if "ice_driver_file_location" in test_case.get_suite_cfg():
        ice_driver_file_location = test_case.get_suite_cfg()["ice_driver_file_location"]
        suite_config["ice_driver_file_location"] = ice_driver_file_location
    if "iavf_driver_file_location" in test_case.get_suite_cfg():
        iavf_driver_file_location = test_case.get_suite_cfg()[
            "iavf_driver_file_location"
        ]
        suite_config["iavf_driver_file_location"] = iavf_driver_file_location
    if "os_default_package_file_location" in test_case.get_suite_cfg():
        os_default_package_file_location = test_case.get_suite_cfg()[
            "os_default_package_file_location"
        ]
        suite_config[
            "os_default_package_file_location"
        ] = os_default_package_file_location
    if "comms_package_file_location" in test_case.get_suite_cfg():
        comms_package_file_location = test_case.get_suite_cfg()[
            "comms_package_file_location"
        ]
        suite_config["comms_package_file_location"] = comms_package_file_location
    if "package_file_location" in test_case.get_suite_cfg():
        package_file_location = test_case.get_suite_cfg()["package_file_location"]
        suite_config["package_file_location"] = package_file_location
    return suite_config


def get_port_rx_packets_number(out, port_num):
    """
    get the port rx packets number.
    """
    p = re.compile(
        "Forward\sstatistics\s+for\s+port\s+%s\s+.*\n.*RX-packets:\s(\d+)\s+" % port_num
    )
    m = p.search(out)
    pkt_num = 0
    if m:
        pkt_num = int(m.group(1))
    return pkt_num


def get_queue_rx_packets_number(out, port_num, queue_id):
    """
    get the queue rx packets number.
    """
    p = re.compile(
        "Forward\sStats\s+for\s+RX\s+Port=\s*%d/Queue=\s*%d\s+.*\n.*RX-packets:\s(\d+)\s+"
        % (port_num, queue_id)
    )
    m = p.search(out)
    pkt_num = 0
    if m:
        pkt_num = int(m.group(1))
    return pkt_num


def check_output_log_in_queue(out, func_param, expect_results):
    """
    check if the expect queue received the expected number packets.
    """
    # parse input parameters
    expect_port = func_param["expect_port"]
    expect_queue = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    pkt_num = get_queue_rx_packets_number(out, expect_port, expect_queue)
    log_msg = ""
    # check the result
    if pkt_num == expect_pkts:
        return True, log_msg
    else:
        log_msg = "Port= %d/Queue= %d receive %d packets" % (
            expect_port,
            expect_queue,
            pkt_num,
        )
        return False, log_msg


def check_output_log_queue_region(out, func_param, expect_results):
    """
    Check if the expect queues received the expected number packets.
    """
    # parse input parameters
    expect_port = func_param["expect_port"]
    expect_queues = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    packet_sumnum = 0
    for queue_id in expect_queues:
        pkt_num = get_queue_rx_packets_number(out, expect_port, queue_id)
        packet_sumnum += pkt_num

    # check the result
    log_msg = ""
    if packet_sumnum == expect_pkts:
        return True, log_msg
    else:
        log_msg = "queue region: Not all packets are received in expect_queues"
        return False, log_msg


def check_output_log_queue_region_mismatched(out, func_param, expect_results):
    """
    when the action is queue region, check the expect port received the expect
    number packets, while the corresponding queues not receive any packets.
    """
    # parse input parameters
    expect_port = func_param["expect_port"]
    expect_queues = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    log_msg = ""
    # check expect_port received expect number packets
    pkt_num = get_port_rx_packets_number(out, expect_port)
    if pkt_num != expect_pkts:
        log_msg = (
            "queue region mismatched: port %d receive %d packets, not receive %d packet"
            % (expect_port, pkt_num, expect_pkts)
        )
        return False, log_msg
    else:
        # check expect queues not received packets
        packet_sumnum = 0
        for queue_id in expect_queues:
            pkt_num = get_queue_rx_packets_number(out, expect_port, queue_id)
            packet_sumnum += pkt_num

        log_msg = ""
        if packet_sumnum == 0:
            return True, log_msg
        else:
            log_msg = (
                "queue region mismatched: expect queues should receive 0 packets, but it received %d packets"
                % packet_sumnum
            )
            return False, log_msg


def check_output_log_in_queue_mismatched(out, func_param, expect_results):
    """
    when the action is to queue, check the expect port received the expect
    number packets, while the corresponding queue not receive any packets.
    """
    # parse input parameters
    expect_port = func_param["expect_port"]
    expect_queue = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    log_msg = ""
    # check expect_port received expect number packets
    pkt_num = get_port_rx_packets_number(out, expect_port)
    if pkt_num != expect_pkts:
        log_msg = "mismatched: port %d receive %d packets, not receive %d packet" % (
            expect_port,
            pkt_num,
            expect_pkts,
        )
        return False, log_msg
    else:
        # check expect queue not received packets
        pkt_num = get_queue_rx_packets_number(out, expect_port, expect_queue)
        log_msg = ""
        if pkt_num == 0:
            return True, log_msg
        else:
            log_msg = (
                "mismatched: expect queue Port= %d/Queue= %d should receive 0 packets, but it received %d packets"
                % (expect_port, expect_queue, pkt_num)
            )
            return False, log_msg


def check_output_log_drop(out, func_param, expect_results):
    """
    check the expect port not receive any packets.
    """
    # parse input parameters
    expect_port = func_param["expect_port"]
    # check expect_port not received the packets
    pkt_num = get_port_rx_packets_number(out, expect_port)

    log_msg = ""
    if pkt_num == 0:
        return True, log_msg
    else:
        log_msg = "Port %d packets not dropped, received %d packets" % (
            expect_port,
            pkt_num,
        )
        return False, log_msg


def check_output_log_drop_mismatched(out, func_param, expect_results):
    """
    check the expect port received the mismatched packets.
    """
    # parse input parameters
    expect_port = func_param["expect_port"]
    expect_pkts = expect_results["expect_pkts"]

    log_msg = ""
    # check expect_port received expect number packets
    pkt_num = get_port_rx_packets_number(out, expect_port)
    if pkt_num == expect_pkts:
        return True, log_msg
    else:
        log_msg = (
            "drop mismatched: port %d receive %d packets, should receive %d packet"
            % (expect_port, pkt_num, expect_pkts)
        )
        return False, log_msg


def check_vf_rx_packets_number(out, func_param, expect_results, need_verify=True):
    """
    check the vf receives the correct number packets
    """
    expect_port = func_param["expect_port"]
    expect_pkts = expect_results["expect_pkts"]

    if isinstance(expect_port, list):
        results = []
        for i in range(0, len(expect_port)):
            pkt_num = get_port_rx_packets_number(out, expect_port[i])
            results.append(pkt_num)
        if need_verify:
            verify(
                results == expect_pkts,
                "failed: packets number not correct. expect %s, result %s"
                % (expect_pkts, results),
            )
        else:
            return results
    else:
        pkt_num = get_port_rx_packets_number(out, expect_port)
        if need_verify:
            verify(
                pkt_num == expect_pkts,
                "failed: packets number not correct. expect %s, result %s"
                % (expect_pkts, pkt_num),
            )
        else:
            return pkt_num


def check_vf_rx_tx_packets_number(
    out, rx_func_param, rx_expect_results, tx_func_param, tx_expect_results
):
    """
    check the vf receives and forwards the correct number packets
    """
    rx_expect_port = rx_func_param["expect_port"]
    rx_expect_pkts = rx_expect_results["expect_pkts"]
    tx_expect_port = tx_func_param["expect_port"]
    tx_expect_pkts = tx_expect_results["expect_pkts"]

    # check port receives and forwards the correct number packets
    if isinstance(rx_expect_port, list):
        results_rx_packets = []
        results_tx_packets = []
        for i in range(0, len(rx_expect_port)):
            p = re.compile(
                "Forward\sstatistics\s+for\s+port\s+%d\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s\d+\s+RX-total:\s\d+\s+.*\n.*TX-packets:\s(\d+)\s+TX-dropped:\s\d+\s+"
                % rx_expect_port[i]
            )
            pkt_li = p.findall(out)
            results = list(map(int, list(pkt_li[0])))
            results_rx_packets.append(results[0])
            results_tx_packets.append(results[1])
        verify(
            results_rx_packets == rx_expect_pkts
            and results_tx_packets == tx_expect_pkts,
            "failed: packets number not correct. expect_rx %s, result_rx %s, expect_tx %s, results_tx %s"
            % (rx_expect_pkts, results_rx_packets, tx_expect_pkts, results_tx_packets),
        )
    else:
        p = re.compile(
            "Forward\sstatistics\s+for\s+port\s+%d\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s\d+\s+RX-total:\s\d+\s+.*\n.*TX-packets:\s(\d+)\s+TX-dropped:\s\d+\s+"
            % rx_expect_port
        )
        pkt_li = p.findall(out)
        results = list(map(int, list(pkt_li[0])))
        verify(
            results[0] == rx_expect_pkts and results[1] == tx_expect_pkts,
            "failed: packets number not correct. expect_rx %s, result_rx %s, expect_tx %s, result_tx %s"
            % (rx_expect_pkts, results[0], tx_expect_pkts, results[1]),
        )

    # check no packets are dropped for all ports
    p = re.compile(
        "Accumulated\sforward\sstatistics\s+for\s+all\s+ports.*\n.*RX-packets:\s\d+\s+RX-dropped:\s\d+\s+RX-total:\s\d+\s+.*\n.*TX-packets:\s\d+\s+TX-dropped:\s(\d+)\s+"
    )
    pkt_li = p.findall(out)
    results_dropped = int(pkt_li[0])
    verify(results_dropped == 0, "failed: dropped packets should be 0.")


def check_kernel_vf_rx_packets_number(out_vfs, expect_results):
    """
    check the kernel vf receives the correct number packets by command ifconfig
    """
    p = re.compile(r"RX\s+packets\s?(\d+)")
    results = []
    for out in out_vfs:
        m = p.search(out)
        if m:
            pkt_num = int(m.group(1))
            results.append(pkt_num)
        else:
            results.append(False)
    verify(
        results == expect_results,
        "failed: packets number not correct. expect %s, result %s"
        % (expect_results, results),
    )


def check_rule_in_list_by_id(out, rule_num, only_last=True):
    """
    check if the rule with ID "rule_num" is in list, after
    executing the command "flow list 0".
    """
    p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
    m = p.search(out)
    if not m:
        return False
    out_lines = out.splitlines()
    if only_last:
        last_rule = out_lines[len(out_lines) - 1]
        last_rule_list = last_rule.split("\t")
        rule_id = int(last_rule_list[0])
        if rule_id == rule_num:
            return True
        else:
            return False
    else:
        # check the list for the rule
        for i in range(len(out_lines)):
            if "ID" in out_lines[i]:
                rules_list = out_lines[i + 1 :]
                break
        for per_rule in rules_list:
            per_rule_list = per_rule.split("\t")
            per_rule_id = int(per_rule_list[0])
            if per_rule_id == rule_num:
                return True
        return False


# fdir common functions
def verify(passed, description):
    if not passed:
        raise AssertionError(description)


def check_queue(out, check_param, stats=True):
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    queue = check_param["queue"]
    p = re.compile(r"port\s+%s/queue(.+?):\s+received\s+(\d+)\s+packets" % port_id)
    res = p.findall(out)
    if res:
        pkt_queue = set([int(i[0]) for i in res])
        if stats:
            if isinstance(queue, int):
                verify(
                    all(q == queue for q in pkt_queue),
                    "fail: queue id not matched, expect queue %s, got %s"
                    % (queue, pkt_queue),
                )
                print((GREEN("pass: queue id %s matched" % pkt_queue)))
            elif isinstance(queue, list):
                verify(
                    all(q in queue for q in pkt_queue),
                    "fail: queue id not matched, expect queue %s, got %s"
                    % (queue, pkt_queue),
                )
                print((GREEN("pass: queue id %s matched" % pkt_queue)))
            else:
                raise Exception("wrong queue value, expect int or list")
        else:
            if isinstance(queue, int):
                verify(
                    not any(q == queue for q in pkt_queue),
                    "fail: queue id should not matched, expect queue %s, got %s"
                    % (queue, pkt_queue),
                )
                print((GREEN("pass: queue id %s not matched" % pkt_queue)))
            elif isinstance(queue, list):
                verify(
                    not any(q in queue for q in pkt_queue),
                    "fail: each queue in %s should not in queue %s"
                    % (pkt_queue, queue),
                )
                print((GREEN("pass: queue id %s not matched" % pkt_queue)))
            else:
                raise Exception("wrong action value, expect queue_index or queue_group")
        return pkt_queue
    else:
        raise Exception("got wrong output, not match pattern %s" % p.pattern)


def check_drop(out, pkt_num, check_param, stats=True):
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    p = re.compile(
        "Forward\sstatistics\s+for\s+port\s+%s\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s(\d+)\s+RX-total:\s(\d+)\s"
        % port_id
    )
    title_li = ["rx-packets", "rx-dropped", "rx-total"]
    pkt_li = p.findall(out)
    if pkt_li:
        res = {k: v for k, v in zip(title_li, list(map(int, list(pkt_li[0]))))}
        verify(
            pkt_num == res["rx-total"],
            "failed: get wrong amount of packet %d, expected %d"
            % (res["rx-total"], pkt_num),
        )
        if stats:
            verify(
                res["rx-dropped"] == pkt_num,
                "failed: dropped packets number %s not match" % res["rx-dropped"],
            )
        else:
            verify(
                res["rx-dropped"] == 0 and res["rx-packets"] == pkt_num,
                "failed: dropped packets number should be 0",
            )
    else:
        raise Exception("got wrong output, not match pattern %s" % p.pattern)


def check_mark(out, pkt_num, check_param, stats=True):
    mark_id = check_param.get("mark_id")
    queue = check_param.get("queue")
    rss_flag = check_param.get("rss")
    rxq = check_param["rxq"] if check_param.get("rxq") is not None else 64
    drop_flag = check_param.get("drop")
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    fdir_scanner = re.compile("FDIR matched ID=(0x\w+)")
    fdir_flag = fdir_scanner.search(out)
    pkt_queue = None
    if stats:
        if drop_flag is None:
            p = re.compile(
                r"port\s+%s/queue(.+?):\s+received\s+(\d+)\s+packets" % port_id
            )
            res = p.findall(out)
            if res:
                pkt_li = [int(i[1]) for i in res]
                res_num = sum(pkt_li)
                verify(
                    res_num == pkt_num,
                    "fail: got wrong number of packets, expect pakcet number %s, got %s."
                    % (pkt_num, res_num),
                )
            else:
                raise Exception("got wrong output, not match pattern %s" % p.pattern)
            if mark_id is not None:
                mark_list = set(
                    int(i, TXQ_RXQ_NUMBER) for i in fdir_scanner.findall(out)
                )
                verify(
                    all([i == check_param["mark_id"] for i in mark_list]) and mark_list,
                    "failed: some packet mark id of %s not match" % mark_list,
                )
            else:
                verify(not fdir_flag, "output should not include mark id")
            if queue is not None:
                check_queue(out, check_param, stats)
            if rss_flag:
                pkt_queue = verify_directed_by_rss(out, rxq, stats=True)
        else:
            check_drop(out, pkt_num, check_param, stats)
            verify(not fdir_flag, "should has no mark_id in %s" % out)
    else:
        if drop_flag is None:
            pkt_queue = verify_directed_by_rss(out, rxq, stats=True)
        else:
            check_drop(out, pkt_num, check_param, stats)
        verify(not fdir_flag, "should has no mark_id in %s" % out)
    return pkt_queue


def verify_directed_by_rss(out, rxq=64, stats=True):
    p = re.compile("RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)")
    pkt_info = p.findall(out)
    pkt_queue = set([int(i[1], TXQ_RXQ_NUMBER) for i in pkt_info])
    if stats:
        verify(
            all(
                [
                    int(i[0], TXQ_RXQ_NUMBER) % rxq == int(i[1], TXQ_RXQ_NUMBER)
                    for i in pkt_info
                ]
            ),
            "some pkt not directed by rss.",
        )
    else:
        verify(
            not any(
                [
                    int(i[0], TXQ_RXQ_NUMBER) % rxq == int(i[1], TXQ_RXQ_NUMBER)
                    for i in pkt_info
                ]
            ),
            "some pkt directed by rss",
        )
    return pkt_queue


# IAVF fdir common functions
def check_iavf_fdir_queue(out, pkt_num, check_param, stats=True):
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    queue = check_param["queue"]
    p = re.compile(
        r"Forward Stats for RX Port=\s?%s/Queue=(\s?\d+)\s.*\n.*RX-packets:(\s?\d+)\s+TX-packets"
        % port_id
    )
    res = p.findall(out)
    if res:
        res_queue = [int(i[0]) for i in res]
        pkt_li = [int(i[1]) for i in res]
        res_num = sum(pkt_li)
        verify(
            res_num == pkt_num,
            "fail: got wrong number of packets, expect pakcet number %s, got %s."
            % (pkt_num, res_num),
        )
        if stats:
            if isinstance(queue, int):
                verify(
                    all(q == queue for q in res_queue),
                    "fail: queue id not matched, expect queue %s, got %s"
                    % (queue, res_queue),
                )
                print((GREEN("pass: queue id %s matched" % res_queue)))
            elif isinstance(queue, list):
                verify(
                    all(q in queue for q in res_queue),
                    "fail: queue id not matched, expect queue %s, got %s"
                    % (queue, res_queue),
                )
                print((GREEN("pass: queue id %s matched" % res_queue)))
            else:
                raise Exception("wrong queue value, expect int or list")
        else:
            if isinstance(queue, int):
                verify_iavf_fdir_directed_by_rss(out, rxq=TXQ_RXQ_NUMBER, stats=True)
                print((GREEN("pass: queue id %s not matched" % res_queue)))
            elif isinstance(queue, list):
                verify_iavf_fdir_directed_by_rss(out, rxq=TXQ_RXQ_NUMBER, stats=True)
                print((GREEN("pass: queue id %s not matched" % res_queue)))
            else:
                raise Exception("wrong action value, expect queue_index or queue_group")
    else:
        raise Exception("got wrong output, not match pattern %s" % p.pattern)


def verify_iavf_fdir_directed_by_rss(out, rxq=TXQ_RXQ_NUMBER, stats=True):
    p = re.compile("RSS hash=(0x\w+) - RSS queue=(0x\w+)")
    pkt_info = p.findall(out)
    if stats:
        for i in pkt_info:
            verify(
                (int(i[0], TXQ_RXQ_NUMBER) % rxq == int(i[1], TXQ_RXQ_NUMBER)),
                "some packets are not directed by RSS",
            )
            print(
                GREEN(
                    "pass: queue id %s is redirected by RSS hash value %s"
                    % (i[1], i[0])
                )
            )
    else:
        for i in pkt_info:
            verify(
                (int(i[0], TXQ_RXQ_NUMBER) % rxq != int(i[1], TXQ_RXQ_NUMBER)),
                "some packets are not directed by RSS",
            )


def check_iavf_fdir_passthru(out, pkt_num, check_param, stats=True):
    # check the actual queue is distributed by RSS
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    p = re.compile("port\s*%s/queue\s?[0-9]+" % port_id)
    pkt_li = p.findall(out)
    verify(
        pkt_num == len(pkt_li),
        "fail: got wrong number of packets, expect pakcet number %s, got %s."
        % (pkt_num, len(pkt_li)),
    )
    p = re.compile("RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)")
    pkt_hash = p.findall(out)
    verify(
        pkt_num == len(pkt_hash),
        "fail: got wrong number of passthru packets, expect passthru packet number %s, got %s."
        % (pkt_num, len(pkt_hash)),
    )
    verify_iavf_fdir_directed_by_rss(out, rxq=TXQ_RXQ_NUMBER, stats=True)


def check_iavf_fdir_mark(out, pkt_num, check_param, stats=True):
    mark_scanner = "FDIR matched ID=(0x\w+)"
    res = re.findall(mark_scanner, out)
    print(out)
    if stats:
        if check_param.get("drop") is not None:
            check_drop(out, pkt_num, check_param, stats)
            verify(not res, "should has no mark_id in %s" % res)
        elif check_param.get("mark_id") is not None:
            mark_list = [i for i in res]
            print("mark list is: ", mark_list)
            verify(len(res) == pkt_num, "get wrong number of packet with mark_id")
            if isinstance(check_param.get("mark_id"), list):
                result = [
                    int(m, TXQ_RXQ_NUMBER) in check_param.get("mark_id")
                    for m in mark_list
                ]
                verify(
                    all(result), "fail: some packet mark id of %s not match" % mark_list
                )
                print((GREEN("pass: mark id %s matched" % mark_list)))
            elif isinstance(check_param.get("mark_id"), int):
                verify(
                    all(
                        [int(i, TXQ_RXQ_NUMBER) == check_param["mark_id"] for i in res]
                    ),
                    "failed: some packet mark id of %s not match" % mark_list,
                )
            else:
                raise Exception("wrong mark value, expect int or list")

            if check_param.get("queue") is not None:
                check_iavf_fdir_queue(out, pkt_num, check_param, stats)
            elif check_param.get("passthru") is not None:
                check_iavf_fdir_passthru(out, pkt_num, check_param, stats)
        else:
            if check_param.get("queue") is not None:
                check_iavf_fdir_queue(out, pkt_num, check_param, stats)
            elif check_param.get("passthru") is not None:
                check_iavf_fdir_passthru(out, pkt_num, check_param, stats)
            verify(not res, "should has no mark_id in %s" % res)
    else:
        if check_param.get("queue") is not None:
            check_iavf_fdir_queue(out, pkt_num, check_param, stats)
        elif check_param.get("drop") is not None:
            check_drop(out, pkt_num, check_param, stats)
        elif check_param.get("passthru") is not None:
            check_iavf_fdir_passthru(out, pkt_num, check_param, stats)
        verify(not res, "should has no mark_id in %s" % res)


# rss common functions
def check_packets_of_each_queue(out):
    """
    check each queue has receive packets
    """
    out = out.split("Forward statistics for port 0")[0]
    lines = out.split("\r\n")
    queue_flag = 0

    for line in lines:
        line = line.strip()
        if "Forward Stats" in line.strip():
            result_scanner = r"RX Port= \d+/Queue=\s?([0-9]+)"
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(line)
            queue_num = m.group(1)
            if queue_num is not None:
                queue_flag = queue_flag + 1

    if queue_flag != 1:
        log_msg = "packets goes to %s different queues" % queue_flag
        return True, log_msg
    else:
        log_msg = "packets not goes to different queues"
        return False, log_msg


def check_symmetric_queue(out):
    """
    check each packets in which queue
    """
    queue_list = re.findall("RSS queue=(\S*)", out)
    m = len(queue_list)
    log_msg = ""
    for i in range(m - 1):
        if queue_list[i] == queue_list[i + 1]:
            return True, log_msg
        else:
            log_msg = "packets not in same queue and cause to fail"
            return False, log_msg


def check_simplexor_queue(out):
    """
    check each packets in which queue
    """
    queue_list = re.findall("RSS queue=(\S*)", out)
    m = len(queue_list)
    log_msg = ""
    for i in range(m - 1):
        if queue_list[i] == queue_list[i + 1]:
            return True, log_msg
        else:
            log_msg = "packets not in same queue and cause to fail"
            return False, log_msg


def check_rx_tx_packets_match(out, count):
    rx_stats = int(re.findall("RX-total:\s+(\d*)", out)[0])
    if rx_stats == count:
        return True, "The Rx packets has matched to the Tx packets"
    else:
        return False, "rx and tx packets error!"


def get_queue_id(line1):
    try:
        result = re.search(r"RX Port=\s*\d*/Queue=\s*(\d*)", line1)
        return result.group(1)
    except:
        return -1


def get_rxpackets(line2):
    try:
        result = re.search(r"RX-packets:\s*(\d*)", line2)
        return result.group(1)
    except:
        return -1


def find_queueid_rxpackets_list(id, q_rx_list):
    for item in q_rx_list:
        if int(item[0]) == id:
            return int(item[1])
    return 0


def check_iavf_packets_rss_queue(out, count, rss_match=True):
    """
    check each queue has receive packets
    """
    out = out.split("Forward statistics for port 0")[0]
    lines = out.split("\r\n")
    queue_flag = 0
    packet_sumnum = 0

    for line in lines:
        line = line.strip()
        if "Forward Stats" in line.strip():
            result_scanner = r"RX Port= \d+/Queue=\s?([0-9]+)"
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(line)
            queue_num = m.group(1)
            if queue_num is not None:
                queue_flag = queue_flag + 1

        elif line.strip().startswith("RX-packets"):
            result_scanner = r"RX-packets:\s?([0-9]+)"
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(line)
            packet_num = m.group(1)
            if len(packet_num) != 0:
                packet_sumnum = packet_sumnum + int(packet_num)

    if rss_match:
        if queue_flag == TXQ_RXQ_NUMBER and packet_sumnum == count:
            log_msg = "Packets has send to %s queues" % queue_flag
            return True, log_msg
        else:
            log_msg = "Packets not send to different queues"
            return False, log_msg
    else:
        if queue_flag == 1 and packet_sumnum == count:
            log_msg = "Packets not match rule"
            return True, log_msg
        else:
            log_msg = "Packets send to different queues"
            return False, log_msg


def check_pf_rss_queue(out, count):
    """
    check each queue has receive packets
    """
    lines = out.split("\r\n")
    queue_num = []
    packet_sumnum = 0

    for line in lines:
        line = line.strip()
        if "_packets" in line.strip():
            result_scanner = r"rx_queue_\d+_packets:\s?(\d+)"
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(line)
            queue_pkg = m.group(1)
            queue_num.append(queue_pkg)
            packet_sumnum = packet_sumnum + int(queue_pkg)

    if packet_sumnum == count and len(queue_num) == 10:
        return True
    else:
        return False


def send_ipfragment_pkt(test_case, pkts, tx_port):
    if isinstance(pkts, str):
        pkts = [pkts]
    for i in range(len(pkts)):
        test_case.tester.scapy_session.send_expect(
            'p=eval("{}")'.format(pkts[i]), ">>> "
        )
        if "IPv6ExtHdrFragment" in pkts[i]:
            test_case.tester.scapy_session.send_expect("pkts=fragment6(p, 500)", ">>> ")
        else:
            test_case.tester.scapy_session.send_expect(
                "pkts=fragment(p, fragsize=500)", ">>> "
            )
        test_case.tester.scapy_session.send_expect(
            'sendp(pkts, iface="{}")'.format(tx_port), ">>> "
        )


class RssProcessing(object):
    def __init__(self, test_case, pmd_output, tester_ifaces, rxq, ipfrag_flag=False):
        self.test_case = test_case
        self.pmd_output = pmd_output
        self.tester_ifaces = tester_ifaces
        self.rxq = rxq
        self.logger = test_case.logger
        self.pkt = Packet()
        self.verify = self.test_case.verify
        self.pass_flag = "passed"
        self.fail_flag = "failed"
        self.current_saved_hash = ""
        self.hash_records = {}
        self.handle_output_methods = {
            "save_hash": self.save_hash,
            "save_or_no_hash": self.save_or_no_hash,
            "check_hash_different": self.check_hash_different,
            "check_no_hash_or_different": self.check_no_hash_or_different,
            "check_hash_same": self.check_hash_same,
            "check_no_hash": self.check_no_hash,
        }
        self.error_msgs = []
        self.ipfrag_flag = ipfrag_flag

    def save_hash(self, out, key="", port_id=0):
        hashes, rss_distribute = self.get_hash_verify_rss_distribute(out, port_id)
        if len(key) != 0:
            self.hash_records[key] = hashes
        self.current_saved_hash = hashes
        if not rss_distribute:
            error_msg = "the packet do not distribute by rss"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)

    def save_or_no_hash(self, out, key="", port_id=0):
        hashes, queues = self.get_hash_and_queues(out, port_id)
        if len(hashes) == 0:
            self.logger.info("There no hash value passed as expected")
            if set(queues) != {"0x0"}:
                error_msg = "received queues should all be 0, but are {}".format(queues)
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)
            return
        if len(key) != 0:
            self.hash_records[key] = hashes
        self.current_saved_hash = hashes
        if not self.verify_rss_distribute(hashes, queues):
            error_msg = "the packet do not distribute by rss"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)

    def check_hash_different(self, out, key="", port_id=0):
        hashes, rss_distribute = self.get_hash_verify_rss_distribute(out, port_id)
        if len(key) == 0:
            for item in hashes:
                if item in self.current_saved_hash:
                    error_msg = (
                        "hash value {} should be different "
                        "with current saved hash {}".format(
                            item, self.current_saved_hash
                        )
                    )
                    self.logger.error(error_msg)
                    self.error_msgs.append(error_msg)
        else:
            for item in hashes:
                if item in self.hash_records[key]:
                    error_msg = (
                        "hash value {} should be different "
                        "with {} {}".format(item, key, self.hash_records[key])
                    )
                    self.logger.error(error_msg)
                    self.error_msgs.append(error_msg)
        if not rss_distribute:
            error_msg = "the packet do not distribute by rss"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)

    def check_no_hash(self, out, port_id=0):
        hashes, queues = self.get_hash_and_queues(out, port_id)
        if len(hashes) != 0:
            error_msg = "hash value {} should be empty".format(hashes)
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)
        elif set(queues) != {"0x0"}:
            error_msg = "received queues should all be 0, but are {}".format(queues)
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)

    def check_no_hash_or_different(self, out, key="", port_id=0):
        hashes, queues = self.get_hash_and_queues(out, port_id)
        if len(hashes) == 0:
            self.logger.info("There no hash value passed as expected")
            if set(queues) != {"0x0"}:
                error_msg = "received queues should all be 0, but are {}".format(queues)
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)
            return
        if len(key) == 0:
            if hashes == self.current_saved_hash:
                error_msg = (
                    "hash value {} should be different "
                    "with current saved hash {}".format(hashes, self.current_saved_hash)
                )
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)
        else:
            if hashes == self.hash_records[key]:
                error_msg = "hash value {} should be different " "with {} {}".format(
                    hashes, key, self.hash_records[key]
                )
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)

    def check_hash_same(self, out, key="", port_id=0):
        hashes, rss_distribute = self.get_hash_verify_rss_distribute(out, port_id)
        if len(key) == 0:
            if hashes != self.current_saved_hash:
                error_msg = (
                    "hash value {} should be same "
                    "with current saved hash {}".format(hashes, self.current_saved_hash)
                )
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)
        else:
            for hash in hashes:
                if hash not in self.hash_records[key]:
                    error_msg = "hash value {} should be same " "with {} {}".format(
                        hashes, key, self.hash_records[key]
                    )
                    self.logger.error(error_msg)
                    self.error_msgs.append(error_msg)
        if not rss_distribute:
            error_msg = "the packet do not distribute by rss"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)

    def check_hash_same_or_no_hash(self, out, key="", port_id=0):
        hashes, rss_distribute = self.get_hash_verify_rss_distribute(out, port_id)
        if len(hashes) != 0:
            error_msg = "hash value {} should be empty".format(hashes)
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)
            return
        elif set(rss_distribute) != {"0x0"}:
            error_msg = "received queues should all be 0, but are {}".format(
                rss_distribute
            )
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)
            return
        if len(key) == 0:
            if hashes != self.current_saved_hash:
                error_msg = (
                    "hash value {} should be same "
                    "with current saved hash {}".format(hashes, self.current_saved_hash)
                )
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)
        else:
            if hashes != self.hash_records[key]:
                error_msg = "hash value {} should be same " "with {} {}".format(
                    hashes, key, self.hash_records[key]
                )
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)
        if not rss_distribute:
            error_msg = "the packet do not distribute by rss"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)

    def verify_rss_distribute(self, hashes, queues):
        if len(hashes) != len(queues):
            self.logger.warning(
                "hash length {} != queue length {}".format(hashes, queues)
            )
            return False
        for i in range(len(hashes)):
            if int(hashes[i], 16) % self.rxq != int(queues[i], 16):
                self.logger.warning(
                    "hash values {} mod total queues {} != queue {}".format(
                        hashes[i], self.rxq, queues[i]
                    )
                )
                return False
        return True

    def get_hash_verify_rss_distribute(self, out, port_id=0):
        hashes, queues = self.get_hash_and_queues(out, port_id)
        if len(hashes) == 0:
            return [], False
        return hashes, self.verify_rss_distribute(hashes, queues)

    def get_hash_and_queues(self, out, port_id=0):
        hash_pattern = re.compile(
            "port\s%s/queue\s\d+:\sreceived\s\d+\spackets.+?\n.*RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)"
            % port_id
        )
        hash_infos = hash_pattern.findall(out)
        self.logger.info("hash_infos: {}".format(hash_infos))
        if len(hash_infos) == 0:
            queue_pattern = re.compile("Receive\squeue=(\w+)")
            queues = queue_pattern.findall(out)
            return [], queues
        # hashes = [int(hash_info[0], 16) for hash_info in hash_infos]
        hashes = [hash_info[0].strip() for hash_info in hash_infos]
        queues = [hash_info[1].strip() for hash_info in hash_infos]
        return hashes, queues

    def send_pkt_get_output(self, pkts, port_id=0, count=1, interval=0):
        tx_port = self.tester_ifaces[0] if port_id == 0 else self.tester_ifaces[1]
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        if self.ipfrag_flag == True:
            count = 2
            send_ipfragment_pkt(self.test_case, pkts, tx_port)
        else:
            self.pkt.update_pkt(pkts)
            self.pkt.send_pkt(
                crb=self.test_case.tester,
                tx_port=tx_port,
                count=count,
                interval=interval,
            )
        out = self.pmd_output.get_output(timeout=1)
        pkt_pattern = (
            "port\s%d/queue\s\d+:\sreceived\s(\d+)\spackets.+?\n.*length=\d{2,}\s"
            % port_id
        )
        reveived_data = re.findall(pkt_pattern, out)
        reveived_pkts = sum(map(int, [i[0] for i in reveived_data]))
        if isinstance(pkts, list):
            self.verify(
                reveived_pkts == len(pkts) * count,
                "expect received %d pkts, but get %d instead"
                % (len(pkts) * count, reveived_pkts),
            )
        else:
            self.verify(
                reveived_pkts == 1 * count,
                "expect received %d pkts, but get %d instead"
                % (1 * count, reveived_pkts),
            )
        return out

    def send_pkt_get_hash_queues(self, pkts, port_id=0, count=1, interval=0):
        output = self.send_pkt_get_output(pkts, port_id, count, interval)
        hashes, queues = self.get_hash_and_queues(output, port_id)
        return hashes, queues

    def create_rule(self, rule: (list, str), check_stats=True, msg=None):
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = list()
        if isinstance(rule, list):
            for i in rule:
                out = self.pmd_output.execute_cmd(i, timeout=1)
                if msg:
                    self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if msg:
                self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(
                all(rule_list), "some rules create failed, result %s" % rule_list
            )
        elif not check_stats:
            self.verify(
                not any(rule_list),
                "all rules should create failed, result %s" % rule_list,
            )
        return rule_list

    def validate_rule(self, rule, check_stats=True, check_msg=None):
        flag = "Flow rule validated"
        if isinstance(rule, str):
            if "create" in rule:
                rule = rule.replace("create", "validate")
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if check_stats:
                self.verify(
                    flag in out.strip(),
                    "rule %s validated failed, result %s" % (rule, out),
                )
            else:
                if check_msg:
                    self.verify(
                        flag not in out.strip() and check_msg in out.strip(),
                        "rule %s validate should failed with msg: %s, but result %s"
                        % (rule, check_msg, out),
                    )
                else:
                    self.verify(
                        flag not in out.strip(),
                        "rule %s validate should failed, result %s" % (rule, out),
                    )
        elif isinstance(rule, list):
            for r in rule:
                if "create" in r:
                    r = r.replace("create", "validate")
                out = self.pmd_output.execute_cmd(r, timeout=1)
                if check_stats:
                    self.verify(
                        flag in out.strip(),
                        "rule %s validated failed, result %s" % (r, out),
                    )
                else:
                    if not check_msg:
                        self.verify(
                            flag not in out.strip(),
                            "rule %s validate should failed, result %s" % (r, out),
                        )
                    else:
                        self.verify(
                            flag not in out.strip() and check_msg in out.strip(),
                            "rule %s should validate failed with msg: %s, but result %s"
                            % (r, check_msg, out),
                        )

    def check_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.pmd_output.execute_cmd("flow list %s" % port_id)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        matched = p.search(out)
        if stats:
            self.verify(matched, "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p2 = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = list(filter(bool, list(map(p2.match, li))))
                result = [i.group(1) for i in res]
                self.verify(
                    set(rule_list).issubset(set(result)),
                    "check rule list failed. expect %s, result %s"
                    % (rule_list, result),
                )
        else:
            if matched:
                if rule_list:
                    res_li = [
                        i.split()[0].strip()
                        for i in out.splitlines()
                        if re.match("\d", i)
                    ]
                    self.verify(
                        not set(rule_list).issubset(res_li),
                        "rule specified should not in result.",
                    )
                else:
                    raise Exception("expect no rule listed")
            else:
                self.verify(not matched, "flow rule on port %s is existed" % port_id)

    def destroy_rule(self, port_id=0, rule_id=None):
        if rule_id is None:
            rule_id = 0
        if isinstance(rule_id, list):
            for i in rule_id:
                out = self.test_case.dut.send_command(
                    "flow destroy %s rule %s" % (port_id, i), timeout=1
                )
                p = re.compile(r"Flow rule #(\d+) destroyed")
                m = p.search(out)
                self.verify(m, "flow rule %s delete failed" % rule_id)
        else:
            out = self.test_case.dut.send_command(
                "flow destroy %s rule %s" % (port_id, rule_id), timeout=1
            )
            p = re.compile(r"Flow rule #(\d+) destroyed")
            m = p.search(out)
            self.verify(m, "flow rule %s delete failed" % rule_id)

    def handle_actions(self, output, actions, port_id=0):
        if isinstance(actions, dict) or isinstance(actions, str):
            actions = [actions]
        for action in actions:  # [{}]
            self.logger.info("action: {}\n".format(action))
            if isinstance(action, str):
                if action in self.handle_output_methods:
                    self.handle_output_methods[action](output, port_id=port_id)
            else:
                for method in action:  # {'save': ''}
                    if method in self.handle_output_methods:
                        if method == "check_no_hash":
                            self.check_no_hash(output, port_id=port_id)
                        else:
                            self.handle_output_methods[method](
                                output, action[method], port_id=port_id
                            )

    def handle_tests(self, tests, port_id=0):
        out = ""
        for test in tests:
            if "send_packet" in test:
                out = self.send_pkt_get_output(test["send_packet"], port_id)
            if "action" in test:
                self.handle_actions(out, test["action"])

    def handle_rss_case(self, case_info):
        # clear hash_records before each sub case
        self.hash_records = {}
        self.error_msgs = []
        self.current_saved_hash = ""
        sub_case_name = case_info.get("sub_casename")
        self.logger.info(
            "===================Test sub case: {}================".format(sub_case_name)
        )
        port_id = case_info.get("port_id") if case_info.get("port_id") else 0
        rules = case_info.get("rule") if case_info.get("rule") else []
        rule_ids = []
        if "pre-test" in case_info:
            self.logger.info("------------handle pre-test--------------")
            self.handle_tests(case_info["pre-test"], port_id)

        # handle tests
        tests = case_info["test"]
        self.logger.info("------------handle test--------------")
        # validate rule
        if rules:
            self.validate_rule(rule=rules, check_stats=True)
            rule_ids = self.create_rule(rule=case_info["rule"], check_stats=True)
            self.check_rule(port_id=port_id, rule_list=rule_ids)
        self.handle_tests(tests, port_id)

        # handle post-test
        if "post-test" in case_info:
            self.logger.info("------------handle post-test--------------")
            self.destroy_rule(port_id=port_id, rule_id=rule_ids)
            self.check_rule(port_id=port_id, stats=False)
            self.handle_tests(case_info["post-test"], port_id)
        if self.error_msgs:
            self.verify(False, str(self.error_msgs[:500]))

    def handle_rss_distribute_cases(self, cases_info):
        sub_cases_result = dict()
        if not isinstance(cases_info, list):
            cases_info = [cases_info]

        for case_info in cases_info:
            try:
                # self.handle_rss_distribute_case(case_info=case_info)
                self.handle_rss_case(case_info=case_info)
            except Exception as e:
                self.logger.warning(
                    "sub_case %s failed: %s" % (case_info["sub_casename"], e)
                )
                sub_cases_result[case_info["sub_casename"]] = self.fail_flag
            else:
                self.logger.info("sub_case %s passed" % case_info["sub_casename"])
                sub_cases_result[case_info["sub_casename"]] = self.pass_flag
            finally:
                self.pmd_output.execute_cmd("flow flush 0")
        pass_rate = (
            round(
                list(sub_cases_result.values()).count(self.pass_flag)
                / len(sub_cases_result),
                4,
            )
            * 100
        )
        self.logger.info(sub_cases_result)
        # self.logger.info('%s pass rate is: %s' % (self.test_case.running_case, pass_rate))
        self.logger.info("pass rate is: %s" % pass_rate)
        self.verify(pass_rate == 100.00, "some subcases failed")

    @staticmethod
    def get_ipv6_template_by_ipv4(template):
        if isinstance(template, dict):
            template = [template]
        ipv6_template = [
            eval(
                str(element)
                .replace("eth / ipv4", "eth / ipv6")
                .replace("IP()", "IPv6()")
                .replace("mac_ipv4", "mac_ipv6")
            )
            for element in template
        ]
        return ipv6_template

    @staticmethod
    def get_ipv6_template_by_ipv4_gtpogre(template):
        if isinstance(template, dict):
            template = [template]
        ipv6_template = [
            eval(
                str(element)
                .replace("eth / ipv4", "eth / ipv6")
                .replace(
                    "IP(proto=0x2F)/GRE(proto=0x0800)/IP()",
                    "IPv6(nh=0x2F)/GRE(proto=0x86DD)/IPv6()",
                )
                .replace("mac_ipv4", "mac_ipv6")
            )
            for element in template
        ]
        return ipv6_template


class FdirProcessing(object):
    def __init__(self, test_case, pmd_output, tester_ifaces, rxq, ipfrag_flag=False):
        self.test_case = test_case
        self.pmd_output = pmd_output
        self.tester_ifaces = tester_ifaces
        self.logger = test_case.logger
        self.pkt = Packet()
        self.rxq = rxq
        self.verify = self.test_case.verify
        self.ipfrag_flag = ipfrag_flag

    def send_pkt_get_output(self, pkts, port_id=0, count=1, interval=0, drop=False):
        tx_port = self.tester_ifaces[0] if port_id == 0 else self.tester_ifaces[1]
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        if drop:
            self.pmd_output.execute_cmd("clear port stats all")
            time.sleep(1)
            if self.ipfrag_flag == True:
                send_ipfragment_pkt(self.test_case, pkts, tx_port)
            else:
                self.pkt.update_pkt(pkts)
                self.pkt.send_pkt(
                    crb=self.test_case.tester,
                    tx_port=tx_port,
                    count=count,
                    interval=interval,
                )
            out = self.pmd_output.execute_cmd("stop")
            self.pmd_output.execute_cmd("start")
            return out
        else:
            if self.ipfrag_flag == True:
                count = 2
                send_ipfragment_pkt(self.test_case, pkts, tx_port)
            else:
                self.pkt.update_pkt(pkts)
                self.pkt.send_pkt(
                    crb=self.test_case.tester,
                    tx_port=tx_port,
                    count=count,
                    interval=interval,
                )
            out = self.pmd_output.get_output(timeout=1)
        pkt_pattern = (
            "port\s%d/queue\s\d+:\sreceived\s(\d+)\spackets.+?\n.*length=\d{2,}\s"
            % port_id
        )
        reveived_data = re.findall(pkt_pattern, out)
        reveived_pkts = sum(map(int, [i[0] for i in reveived_data]))
        if isinstance(pkts, list):
            self.verify(
                reveived_pkts == len(pkts) * count,
                "expect received %d pkts, but get %d instead"
                % (len(pkts) * count, reveived_pkts),
            )
        else:
            self.verify(
                reveived_pkts == 1 * count,
                "expect received %d pkts, but get %d instead"
                % (1 * count, reveived_pkts),
            )
        return out

    def check_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.pmd_output.execute_cmd("flow list %s" % port_id)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        matched = p.search(out)
        if stats:
            self.verify(matched, "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p2 = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = list(filter(bool, list(map(p2.match, li))))
                result = [i.group(1) for i in res]
                self.verify(
                    set(rule_list).issubset(set(result)),
                    "check rule list failed. expect %s, result %s"
                    % (rule_list, result),
                )
        else:
            if matched:
                if rule_list:
                    res_li = [
                        i.split()[0].strip()
                        for i in out.splitlines()
                        if re.match("\d", i)
                    ]
                    self.verify(
                        not set(rule_list).issubset(res_li),
                        "rule specified should not in result.",
                    )
                else:
                    raise Exception("expect no rule listed")
            else:
                self.verify(not matched, "flow rule on port %s is existed" % port_id)

    def destroy_rule(self, port_id=0, rule_id=None):
        if rule_id is None:
            rule_id = 0
        if isinstance(rule_id, list):
            for i in rule_id:
                out = self.test_case.dut.send_command(
                    "flow destroy %s rule %s" % (port_id, i), timeout=1
                )
                p = re.compile(r"Flow rule #(\d+) destroyed")
                m = p.search(out)
                self.verify(m, "flow rule %s delete failed" % rule_id)
        else:
            out = self.test_case.dut.send_command(
                "flow destroy %s rule %s" % (port_id, rule_id), timeout=1
            )
            p = re.compile(r"Flow rule #(\d+) destroyed")
            m = p.search(out)
            self.verify(m, "flow rule %s delete failed" % rule_id)

    def create_rule(self, rule: (list, str), check_stats=True, msg=None):
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = list()
        if isinstance(rule, list):
            for i in rule:
                out = self.pmd_output.execute_cmd(i, timeout=1)
                if msg:
                    self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if msg:
                self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(
                all(rule_list), "some rules create failed, result %s" % rule_list
            )
        elif not check_stats:
            self.verify(
                not any(rule_list),
                "all rules should create failed, result %s" % rule_list,
            )
        return rule_list

    def validate_rule(self, rule, check_stats=True, check_msg=None):
        flag = "Flow rule validated"
        if isinstance(rule, str):
            if "create" in rule:
                rule = rule.replace("create", "validate")
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if check_stats:
                self.verify(
                    flag in out.strip(),
                    "rule %s validated failed, result %s" % (rule, out),
                )
            else:
                if check_msg:
                    self.verify(
                        flag not in out.strip() and check_msg in out.strip(),
                        "rule %s validate should failed with msg: %s, but result %s"
                        % (rule, check_msg, out),
                    )
                else:
                    self.verify(
                        flag not in out.strip(),
                        "rule %s validate should failed, result %s" % (rule, out),
                    )
        elif isinstance(rule, list):
            for r in rule:
                if "create" in r:
                    r = r.replace("create", "validate")
                out = self.pmd_output.execute_cmd(r, timeout=1)
                if check_stats:
                    self.verify(
                        flag in out.strip(),
                        "rule %s validated failed, result %s" % (r, out),
                    )
                else:
                    if not check_msg:
                        self.verify(
                            flag not in out.strip(),
                            "rule %s validate should failed, result %s" % (r, out),
                        )
                    else:
                        self.verify(
                            flag not in out.strip() and check_msg in out.strip(),
                            "rule %s should validate failed with msg: %s, but result %s"
                            % (r, check_msg, out),
                        )

    def flow_director_validate(self, vectors):
        """
        FDIR test: validate/create rule, check match pkts and unmatched pkts, destroy rule...

        :param vectors: test vectors
        """
        test_results = dict()
        for tv in vectors:
            try:
                self.logger.info(
                    "====================sub_case: {}=========================".format(
                        tv["name"]
                    )
                )
                port_id = (
                    tv["check_param"]["port_id"]
                    if tv["check_param"].get("port_id") is not None
                    else 0
                )
                drop = tv["check_param"].get("drop")
                # create rule
                self.test_case.dut.send_expect(
                    "flow flush %d" % port_id, "testpmd> ", 120
                )
                rule_rss = []
                if "tv_mac_ipv4_frag_fdir" in tv["name"]:
                    rule_rss = self.create_rule(
                        "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end"
                    )
                elif "tv_mac_ipv6_frag_fdir" in tv["name"]:
                    rule_rss = self.create_rule(
                        "flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end"
                    )
                rule_li = self.create_rule(tv["rule"])
                # send and check match packets
                out1 = self.send_pkt_get_output(
                    pkts=tv["scapy_str"]["matched"], port_id=port_id, drop=drop
                )
                matched_queue = check_mark(
                    out1,
                    pkt_num=len(tv["scapy_str"]["matched"]) * 2
                    if self.ipfrag_flag
                    else len(tv["scapy_str"]["matched"]),
                    check_param=tv["check_param"],
                )

                # send and check unmatched packets
                out2 = self.send_pkt_get_output(
                    pkts=tv["scapy_str"]["unmatched"], port_id=port_id, drop=drop
                )
                check_mark(
                    out2,
                    pkt_num=len(tv["scapy_str"]["unmatched"]) * 2
                    if self.ipfrag_flag
                    else len(tv["scapy_str"]["unmatched"]),
                    check_param=tv["check_param"],
                    stats=False,
                )

                # list and destroy rule
                self.check_rule(port_id=tv["check_param"]["port_id"], rule_list=rule_li)
                self.destroy_rule(rule_id=rule_li, port_id=port_id)
                # send matched packet
                out3 = self.send_pkt_get_output(
                    pkts=tv["scapy_str"]["matched"], port_id=port_id, drop=drop
                )
                matched_queue2 = check_mark(
                    out3,
                    pkt_num=len(tv["scapy_str"]["matched"]) * 2
                    if self.ipfrag_flag
                    else len(tv["scapy_str"]["matched"]),
                    check_param=tv["check_param"],
                    stats=False,
                )
                if tv["check_param"].get("rss"):
                    self.verify(
                        matched_queue == matched_queue2 and None not in matched_queue,
                        "send twice matched packet, received in deferent queues",
                    )
                # check not rule exists
                if rule_rss:
                    self.check_rule(
                        port_id=tv["check_param"]["port_id"], rule_list=rule_rss
                    )
                else:
                    self.check_rule(port_id=port_id, stats=False)
                test_results[tv["name"]] = True
                self.logger.info((GREEN("case passed: %s" % tv["name"])))
            except Exception as e:
                self.logger.warning((RED(e)))
                self.test_case.dut.send_command("flow flush 0", timeout=1)
                test_results[tv["name"]] = False
                self.logger.info((GREEN("case failed: %s" % tv["name"])))
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed".format(failed_cases))

    def send_pkt_get_out(self, pkts, port_id=0, count=1, interval=0):
        tx_port = self.tester_ifaces[0] if port_id == 0 else self.tester_ifaces[1]
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("clear port stats all")
        self.pkt.update_pkt(pkts)
        self.pkt.send_pkt(
            crb=self.test_case.tester, tx_port=tx_port, count=count, interval=interval
        )

        out1 = self.pmd_output.get_output(timeout=1)
        out2 = self.pmd_output.execute_cmd("stop")
        return out1 + out2

    def check_rx_packets(self, out, check_param, expect_pkt, stats=True):
        queue = check_param["queue"]
        p = "Forward\s+statistics\s+for\s+port\s+0.*\n.*?RX-packets:\s(\d+)\s+"
        if queue == "null":
            pkt_num = re.search(p, out).group(1)
            if stats:
                self.verify(
                    int(pkt_num) == 0,
                    "receive %s packets, expect receive 0 packets" % pkt_num,
                )
            else:
                self.verify(
                    int(pkt_num) == expect_pkt,
                    "receive {} packets, expect receive {} packets".format(
                        pkt_num, expect_pkt
                    ),
                )
        else:
            check_queue(out, check_param, stats=stats)

    def handle_priority_cases(self, vectors):
        rule = vectors["rule"]
        packets = vectors["packet"]
        check_param = vectors["check_param"]
        self.validate_rule(rule)
        rule_list = self.create_rule(rule)
        self.check_rule(rule_list=rule_list)
        out = self.send_pkt_get_out(packets["matched"])
        self.check_rx_packets(out, check_param["check_0"], len(packets["matched"]))
        out = self.send_pkt_get_out(packets["mismatched"])
        self.check_rx_packets(
            out, check_param["check_0"], len(packets["mismatched"]), stats=False
        )

        # destroy rule with priority 0
        self.destroy_rule(rule_id=rule_list[0])
        self.check_rule(rule_list=rule_list[1:])
        out = self.send_pkt_get_out(packets["matched"])
        self.check_rx_packets(out, check_param["check_1"], len(packets["matched"]))
        out = self.send_pkt_get_out(packets["mismatched"])
        self.check_rx_packets(
            out, check_param["check_0"], len(packets["mismatched"]), stats=False
        )
        self.check_rx_packets(
            out, check_param["check_1"], len(packets["mismatched"]), stats=False
        )

        # destroy rule with priority 1
        rule_id = self.create_rule(rule[0])
        self.destroy_rule(rule_id=rule_list[1])
        self.check_rule(rule_list=rule_id)
        out = self.send_pkt_get_out(packets["matched"])
        self.check_rx_packets(out, check_param["check_0"], len(packets["matched"]))
        out = self.send_pkt_get_out(packets["mismatched"])
        self.check_rx_packets(
            out, check_param["check_0"], len(packets["mismatched"]), stats=False
        )

        # destroy all rule
        self.destroy_rule(rule_id=rule_id)
        out = self.send_pkt_get_out(packets["matched"])
        self.check_rx_packets(
            out, check_param["check_0"], len(packets["matched"]), stats=False
        )
        self.check_rx_packets(
            out, check_param["check_1"], len(packets["matched"]), stats=False
        )

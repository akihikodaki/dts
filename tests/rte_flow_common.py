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

import json
import time
import re
from utils import GREEN, RED

CVL_TXQ_RXQ_NUMBER = 16

# switch filter common functions
def get_suite_config(test_case):
    """
    get the suite config from conf/suite.cfg.
    """
    suite_config = {}
    if "ice_driver_file_location" in test_case.get_suite_cfg():
        ice_driver_file_location = test_case.get_suite_cfg()["ice_driver_file_location"]
        suite_config["ice_driver_file_location"] = ice_driver_file_location
    if "os_default_package_file_location" in test_case.get_suite_cfg():
        os_default_package_file_location = test_case.get_suite_cfg()["os_default_package_file_location"]
        suite_config["os_default_package_file_location"] = os_default_package_file_location
    if "comms_package_file_location" in test_case.get_suite_cfg():
        comms_package_file_location = test_case.get_suite_cfg()["comms_package_file_location"]
        suite_config["comms_package_file_location"] = comms_package_file_location
    if "package_file_location" in test_case.get_suite_cfg():
        package_file_location = test_case.get_suite_cfg()["package_file_location"]
        suite_config["package_file_location"] = package_file_location
    return suite_config

def get_rx_packet_number(out,match_string):
    """
    get the rx packets number.
    """
    out_lines=out.splitlines()
    pkt_num =0
    for i in range(len(out_lines)):
        if  match_string in out_lines[i]:
            result_scanner = r'RX-packets:\s?(\d+)'
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(out_lines[i+1])
            pkt_num = int(m.group(1))
            break
    return pkt_num

def get_port_rx_packets_number(out,port_num):
    """
    get the port rx packets number.
    """
    match_string="---------------------- Forward statistics for port %d" % port_num
    pkt_num = get_rx_packet_number(out,match_string)
    return pkt_num

def get_queue_rx_packets_number(out, port_num, queue_id):
    """
    get the queue rx packets number.
    """
    match_string="------- Forward Stats for RX Port= %d/Queue= %d" % (port_num, queue_id)
    pkt_num = get_rx_packet_number(out,match_string)
    return pkt_num

def check_output_log_in_queue(out, func_param, expect_results):
    """
    check if the expect queue received the expected number packets.
    """
    #parse input parameters
    expect_port = func_param["expect_port"]
    expect_queue = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    pkt_num = get_queue_rx_packets_number(out,expect_port,expect_queue)
    log_msg = ""
    #check the result
    if pkt_num == expect_pkts:
        return True, log_msg
    else:
        log_msg = "Port= %d/Queue= %d receive %d packets" % (expect_port, expect_queue, pkt_num)
        return False, log_msg

def check_output_log_queue_region(out, func_param, expect_results):
    """
    Check if the expect queues received the expected number packets.
    """
    #parse input parameters
    expect_port = func_param["expect_port"]
    expect_queues = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    packet_sumnum = 0
    for queue_id in expect_queues:
        pkt_num = get_queue_rx_packets_number(out, expect_port, queue_id)
        packet_sumnum += pkt_num

    #check the result
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
    #parse input parameters
    expect_port = func_param["expect_port"]
    expect_queues = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    log_msg = ""
    #check expect_port received expect number packets
    pkt_num = get_port_rx_packets_number(out, expect_port)
    if pkt_num != expect_pkts:
        log_msg = "queue region mismatched: port %d receive %d packets, not receive %d packet" % (expect_port, pkt_num, expect_pkts)
        return False, log_msg
    else:
        #check expect queues not received packets
        packet_sumnum = 0
        for queue_id in expect_queues:
            pkt_num = get_queue_rx_packets_number(out, expect_port, queue_id)
            packet_sumnum += pkt_num

        log_msg = ""
        if packet_sumnum == 0:
            return True, log_msg
        else:
            log_msg = "queue region mismatched: expect queues should receive 0 packets, but it received %d packets" % packet_sumnum
            return False, log_msg

def check_output_log_in_queue_mismatched(out, func_param, expect_results):
    """
    when the action is to queue, check the expect port received the expect
    number packets, while the corresponding queue not receive any packets.
    """
    #parse input parameters
    expect_port = func_param["expect_port"]
    expect_queue = func_param["expect_queues"]
    expect_pkts = expect_results["expect_pkts"]

    log_msg = ""
    #check expect_port received expect number packets
    pkt_num = get_port_rx_packets_number(out, expect_port)
    if pkt_num != expect_pkts:
        log_msg = "mismatched: port %d receive %d packets, not receive %d packet" % (expect_port, pkt_num, expect_pkts)
        return False, log_msg
    else:
        #check expect queue not received packets
        pkt_num = get_queue_rx_packets_number(out, expect_port, expect_queue)
        log_msg = ""
        if pkt_num == 0:
            return True, log_msg
        else:
            log_msg = "mismatched: expect queue Port= %d/Queue= %d should receive 0 packets, but it received %d packets" % (expect_port, expect_queue, pkt_num)
            return False, log_msg

def check_output_log_drop(out, func_param, expect_results):
    """
    check the expect port not receive any packets.
    """
    #parse input parameters
    expect_port = func_param["expect_port"]
    #check expect_port not received the packets
    pkt_num = get_port_rx_packets_number(out, expect_port)

    log_msg = ""
    if pkt_num == 0:
        return True, log_msg
    else:
        log_msg = "Port %d packets not dropped, received %d packets" % (expect_port, pkt_num)
        return False, log_msg

def check_output_log_drop_mismatched(out, func_param, expect_results):
    """
    check the expect port received the mismatched packets.
    """
    #parse input parameters
    expect_port = func_param["expect_port"]
    expect_pkts = expect_results["expect_pkts"]

    log_msg = ""
    #check expect_port received expect number packets
    pkt_num = get_port_rx_packets_number(out, expect_port)
    if pkt_num == expect_pkts:
        return True, log_msg
    else:
        log_msg = "drop mismatched: port %d receive %d packets, should receive %d packet" % (expect_port, pkt_num, expect_pkts)
        return False, log_msg

def check_vf_rx_packets_number(out, func_param, expect_results, need_verify=True):
    """
    check the vf receives the correct number packets
    """
    expect_port = func_param["expect_port"]
    expect_pkts = expect_results["expect_pkts"]

    if isinstance(expect_port, list):
        results = []
        for i in range(0,len(expect_port)):
            pkt_num = get_port_rx_packets_number(out, expect_port[i])
            results.append(pkt_num)
        if need_verify:
            verify(results == expect_pkts, "failed: packets number not correct. expect %s, result %s" % (expect_pkts, results))
        else:
            return results
    else:
        pkt_num = get_port_rx_packets_number(out, expect_port)
        if need_verify:
            verify(pkt_num == expect_pkts, "failed: packets number not correct. expect %s, result %s" % (expect_pkts, pkt_num))
        else:
            return pkt_num

def check_vf_rx_tx_packets_number(out, rx_func_param, rx_expect_results, tx_func_param, tx_expect_results):
    """
    check the vf receives and forwards the correct number packets
    """
    rx_expect_port = rx_func_param["expect_port"]
    rx_expect_pkts = rx_expect_results["expect_pkts"]
    tx_expect_port = tx_func_param["expect_port"]
    tx_expect_pkts = tx_expect_results["expect_pkts"]

    #check port receives and forwards the correct number packets
    if isinstance(rx_expect_port, list):
        results_rx_packets = []
        results_tx_packets = []
        for i in range(0,len(rx_expect_port)):
            p = re.compile(
                'Forward\sstatistics\s+for\s+port\s+%d\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s\d+\s+RX-total:\s\d+\s+.*\n.*TX-packets:\s(\d+)\s+TX-dropped:\s\d+\s+' % rx_expect_port[i])
            pkt_li = p.findall(out)
            results = list(map(int, list(pkt_li[0])))
            results_rx_packets.append(results[0])
            results_tx_packets.append(results[1])
        verify(results_rx_packets == rx_expect_pkts and results_tx_packets == tx_expect_pkts, "failed: packets number not correct. expect_rx %s, result_rx %s, expect_tx %s, results_tx %s" % (rx_expect_pkts, results_rx_packets, tx_expect_pkts, results_tx_packets))
    else:
        p = re.compile(
                'Forward\sstatistics\s+for\s+port\s+%d\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s\d+\s+RX-total:\s\d+\s+.*\n.*TX-packets:\s(\d+)\s+TX-dropped:\s\d+\s+' % rx_expect_port)
        pkt_li = p.findall(out)
        results = list(map(int, list(pkt_li[0])))
        verify(results[0] == rx_expect_pkts and results[1] == tx_expect_pkts, "failed: packets number not correct. expect_rx %s, result_rx %s, expect_tx %s, result_tx %s" % (rx_expect_pkts, results[0], tx_expect_pkts, results[1]))

    #check no packets are dropped for all ports
    p = re.compile(
                'Accumulated\sforward\sstatistics\s+for\s+all\s+ports.*\n.*RX-packets:\s\d+\s+RX-dropped:\s\d+\s+RX-total:\s\d+\s+.*\n.*TX-packets:\s\d+\s+TX-dropped:\s(\d+)\s+')
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
    verify(results == expect_results, "failed: packets number not correct. expect %s, result %s" % (expect_results, results))

def check_rule_in_list_by_id(out, rule_num, only_last=True):
    """
    check if the rule with ID "rule_num" is in list, after
    executing the command "flow list 0".
    """
    p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
    m = p.search(out)
    if not m:
        return False
    out_lines=out.splitlines()
    if only_last:
        last_rule = out_lines[len(out_lines)-1]
        last_rule_list = last_rule.split('\t')
        rule_id = int(last_rule_list[0])
        if rule_id == rule_num:
            return True
        else:
            return False
    else:
        #check the list for the rule
        for i in range(len(out_lines)):
            if "ID" in out_lines[i]:
                rules_list = out_lines[i+1:]
                break
        for per_rule in rules_list:
            per_rule_list = per_rule.split('\t')
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
                verify(all(q == queue for q in pkt_queue),
                       "fail: queue id not matched, expect queue %s, got %s" % (queue, pkt_queue))
                print((GREEN("pass: queue id %s matched" % pkt_queue)))
            elif isinstance(queue, list):
                verify(all(q in queue for q in pkt_queue),
                       "fail: queue id not matched, expect queue %s, got %s" % (queue, pkt_queue))
                print((GREEN("pass: queue id %s matched" % pkt_queue)))
            else:
                raise Exception("wrong queue value, expect int or list")
        else:
            if isinstance(queue, int):
                verify(not any(q == queue for q in pkt_queue),
                       "fail: queue id should not matched, expect queue %s, got %s" % (queue, pkt_queue))
                print((GREEN("pass: queue id %s not matched" % pkt_queue)))
            elif isinstance(queue, list):
                verify(not any(q in queue for q in pkt_queue),
                       "fail: each queue in %s should not in queue %s" % (pkt_queue, queue))
                print((GREEN("pass: queue id %s not matched" % pkt_queue)))
            else:
                raise Exception("wrong action value, expect queue_index or queue_group")
        return pkt_queue
    else:
        raise Exception("got wrong output, not match pattern %s" % p.pattern)


def check_drop(out, pkt_num, check_param, stats=True):
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    p = re.compile(
        'Forward\sstatistics\s+for\s+port\s+%s\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s(\d+)\s+RX-total:\s(\d+)\s' % port_id)
    title_li = ["rx-packets", "rx-dropped", "rx-total"]
    pkt_li = p.findall(out)
    if pkt_li:
        res = {k: v for k, v in zip(title_li, list(map(int, list(pkt_li[0]))))}
        verify(pkt_num == res["rx-total"],
               "failed: get wrong amount of packet %d, expected %d" % (res["rx-total"], pkt_num))
        if stats:
            verify(res["rx-dropped"] == pkt_num, "failed: dropped packets number %s not match" % res["rx-dropped"])
        else:
            verify(res["rx-dropped"] == 0 and res["rx-packets"] == pkt_num,
                   "failed: dropped packets number should be 0")
    else:
        raise Exception("got wrong output, not match pattern %s" % p.pattern)


def check_mark(out, pkt_num, check_param, stats=True):
    mark_id = check_param.get("mark_id")
    queue = check_param.get("queue")
    rss_flag = check_param.get("rss")
    rxq = check_param['rxq'] if check_param.get("rxq") is not None else 64
    drop_flag = check_param.get("drop")
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    fdir_scanner = re.compile("FDIR matched ID=(0x\w+)")
    fdir_flag = fdir_scanner.search(out)
    pkt_queue = None
    if stats:
        if drop_flag is None:
            p = re.compile(r"port\s+%s/queue(.+?):\s+received\s+(\d+)\s+packets" % port_id)
            res = p.findall(out)
            if res:
                pkt_li = [int(i[1]) for i in res]
                res_num = sum(pkt_li)
                verify(res_num == pkt_num,
                       "fail: got wrong number of packets, expect pakcet number %s, got %s." % (pkt_num, res_num))
            else:
                raise Exception("got wrong output, not match pattern %s" % p.pattern)
            if mark_id is not None:
                mark_list = set(int(i, CVL_TXQ_RXQ_NUMBER) for i in fdir_scanner.findall(out))
                verify(all([i == check_param["mark_id"] for i in mark_list]),
                       "failed: some packet mark id of %s not match" % mark_list)
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
    p = re.compile('RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)')
    pkt_info = p.findall(out)
    pkt_queue = set([int(i[1], CVL_TXQ_RXQ_NUMBER) for i in pkt_info])
    if stats:
        verify(all([int(i[0], CVL_TXQ_RXQ_NUMBER) % rxq == int(i[1], CVL_TXQ_RXQ_NUMBER) for i in pkt_info]), 'some pkt not directed by rss.')
    else:
        verify(not any([int(i[0], CVL_TXQ_RXQ_NUMBER) % rxq == int(i[1], CVL_TXQ_RXQ_NUMBER) for i in pkt_info]), 'some pkt directed by rss')
    return pkt_queue


# IAVF fdir common functions
def check_iavf_fdir_queue(out, pkt_num, check_param, stats=True):
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    queue = check_param["queue"]
    p = re.compile(
        r"Forward Stats for RX Port=\s?%s/Queue=(\s?\d+)\s.*\n.*RX-packets:(\s?\d+)\s+TX-packets" % port_id)
    res = p.findall(out)
    if res:
        res_queue = [int(i[0]) for i in res]
        pkt_li = [int(i[1]) for i in res]
        res_num = sum(pkt_li)
        verify(res_num == pkt_num, "fail: got wrong number of packets, expect pakcet number %s, got %s." % (pkt_num, res_num))
        if stats:
            if isinstance(queue, int):
                verify(all(q == queue for q in res_queue), "fail: queue id not matched, expect queue %s, got %s" % (queue, res_queue))
                print((GREEN("pass: queue id %s matched" % res_queue)))
            elif isinstance(queue, list):
                verify(all(q in queue for q in res_queue), "fail: queue id not matched, expect queue %s, got %s" % (queue, res_queue))
                print((GREEN("pass: queue id %s matched" % res_queue)))
            else:
                raise Exception("wrong queue value, expect int or list")
        else:
            if isinstance(queue, int):
                verify(not any(q == queue for q in res_queue), "fail: queue id should not matched, expect queue %s, got %s" % (queue, res_queue))
                print((GREEN("pass: queue id %s not matched" % res_queue)))
            elif isinstance(queue, list):
                verify_iavf_fdir_directed_by_rss(out, rxq=CVL_TXQ_RXQ_NUMBER, stats=True)
                print((GREEN("pass: queue id %s not matched" % res_queue)))
            else:
                raise Exception("wrong action value, expect queue_index or queue_group")
    else:
        raise Exception("got wrong output, not match pattern %s" % p.pattern)

def verify_iavf_fdir_directed_by_rss(out, rxq=CVL_TXQ_RXQ_NUMBER, stats=True):
    p = re.compile("RSS hash=(0x\w+) - RSS queue=(0x\w+)")
    pkt_info = p.findall(out)
    if stats:
        for i in pkt_info:
            verify((int(i[0],CVL_TXQ_RXQ_NUMBER) % rxq == int(i[1],CVL_TXQ_RXQ_NUMBER)), "some packets are not directed by RSS")
            print(GREEN("pass: queue id %s is redirected by RSS hash value %s" % (i[1], i[0])))
    else:
        for i in pkt_info:
            verify((int(i[0],CVL_TXQ_RXQ_NUMBER) % rxq != int(i[1],CVL_TXQ_RXQ_NUMBER)), "some packets are not directed by RSS")

def check_iavf_fdir_passthru(out, pkt_num, check_param, stats=True):
    # check the actual queue is distributed by RSS
    port_id = check_param["port_id"] if check_param.get("port_id") is not None else 0
    p = re.compile('port\s*%s/queue\s?[0-9]+' % port_id)
    pkt_li = p.findall(out)
    verify(pkt_num == len(pkt_li), "fail: got wrong number of packets, expect pakcet number %s, got %s." % (pkt_num, len(pkt_li)))
    p = re.compile('RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)')
    pkt_hash = p.findall(out)
    verify(pkt_num == len(pkt_hash), "fail: got wrong number of passthru packets, expect passthru packet number %s, got %s." % (pkt_num, len(pkt_hash)))
    verify_iavf_fdir_directed_by_rss(out, rxq=CVL_TXQ_RXQ_NUMBER, stats=True)

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
            verify(all([int(i, CVL_TXQ_RXQ_NUMBER) == check_param["mark_id"] for i in res]),
                        "failed: some packet mark id of %s not match" % mark_list)
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
    queue_list = re.findall('RSS queue=(\S*)', out)
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
    queue_list = re.findall('RSS queue=(\S*)', out)
    m = len(queue_list)
    log_msg = ""
    for i in range(m - 1):
        if queue_list[i] == queue_list[i + 1]:
           return True, log_msg
        else:
           log_msg = "packets not in same queue and cause to fail"
           return False, log_msg

def check_rx_tx_packets_match(out, count):
    rx_stats = int(re.findall('RX-total:\s+(\d*)', out)[0])
    if rx_stats == count :
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
        if (int(item[0]) == id):
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
        if queue_flag == CVL_TXQ_RXQ_NUMBER and packet_sumnum == count:
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

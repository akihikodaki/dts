# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2020 Intel Corporation
#

"""
DPDK Test suite.
l3fwd-power test suite.
"""
import json
import os
import re
import textwrap
import time
import traceback
from copy import deepcopy
from pprint import pformat

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.utils import create_mask as dts_create_mask


class TestPowerTelemetry(TestCase):
    output_path = "/tmp"

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = (
            "/root" + self.dut.base_dir[1:]
            if self.dut.base_dir.startswith("~")
            else self.dut.base_dir
        )
        return target_dir

    def d_con(self, cmd):
        _cmd = [cmd, "# ", 10] if isinstance(cmd, str) else cmd
        return self.dut.send_expect(*_cmd)

    def d_a_con(self, cmd):
        _cmd = [cmd, "# ", 10] if isinstance(cmd, str) else cmd
        return self.dut.alt_session.send_expect(*_cmd)

    def get_pkt_len(self, pkt_type, frame_size=64):
        headers_size = sum([HEADER_SIZE[x] for x in ["eth", "ip", pkt_type]])
        pktlen = frame_size - headers_size
        return pktlen

    def config_stream(self, dmac):
        pkt_config = {
            "type": "UDP",
            "pkt_layers": {
                "ether": {"dst": dmac},
                "raw": {"payload": ["58"] * self.get_pkt_len("udp")},
            },
        }
        values = pkt_config
        pkt_type = values.get("type")
        pkt_layers = values.get("pkt_layers")
        pkt = Packet(pkt_type=pkt_type)
        for layer in list(pkt_layers.keys()):
            pkt.config_layer(layer, pkt_layers[layer])
        return pkt.pktgen.pkt

    def add_stream_to_pktgen(self, option):
        stream_ids = []
        topos = [[0, 0]]
        for txport, rxport in topos:
            _option = deepcopy(option)
            dmac = self.dut.get_mac_address(self.dut_ports[txport])
            pkt = self.config_stream(dmac)
            _option["pcap"] = pkt
            stream_id = self.tester.pktgen.add_stream(txport, rxport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
        return stream_ids

    def run_traffic(self, option):
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # set stream into pktgen
        stream_option = {
            "stream_config": {
                "txmode": {},
                "transmit_mode": TRANSMIT_CONT,
                "rate": float(100),
            }
        }
        stream_ids = self.add_stream_to_pktgen(stream_option)
        # run pktgen traffic
        traffic_opt = option.get("traffic_opt")
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)
        self.logger.debug(pformat(traffic_opt))
        self.logger.debug(pformat(result))

        return result

    def prepare_binary(self, name):
        example_dir = "examples/" + name
        out = self.dut.build_dpdk_apps("./" + example_dir)
        return os.path.join(self.target_dir, self.dut.apps_name[os.path.basename(name)])

    def get_cores_mask(self, config):
        ports_socket = self.dut.get_numa_id(self.dut.get_ports()[0])
        mask = dts_create_mask(self.dut.get_core_list(config, socket=ports_socket))
        return mask

    def init_l3fwd_power(self):
        self.l3fwd_power = self.prepare_binary("l3fwd-power")

    def start_l3fwd_power(self, core_config="1S/2C/1T"):
        core_mask, core = "0x6", 2
        option = (
            " "
            "-c {core_mask} "
            "-n {mem_channel} "
            "--telemetry "
            "-- "
            "--telemetry "
            "-p 0x1 "
            "-P "
            '--config="(0,0,{core})" '
        ).format(
            **{
                "core_mask": core_mask,
                "core": core,
                "mem_channel": self.dut.get_memory_channels(),
            }
        )
        prompt = "L3FWD_POWER: entering main telemetry loop"
        cmd = [" ".join([self.l3fwd_power, option]), prompt, 60]
        self.d_con(cmd)
        self.is_l3fwd_on = True

    def close_l3fwd_power(self):
        if not self.is_l3fwd_on:
            return
        cmd = "^C"
        self.d_con(cmd)

    def create_query_script(self):
        """
        usertools/dpdk-telemetry-client.py does not support save json data,
        this method is used to make sure testing robust.
        """
        script_content = textwrap.dedent(
            """
            #! /usr/bin/env python
            import argparse
            import time
            import json
            from dpdk_telemetry_client import Client, GLOBAL_METRICS_REQ, BUFFER_SIZE
            
            class ClientExd(Client):
                def __init__(self, json_file):
                    super(ClientExd, self).__init__()
                    self.json_file = json_file
                def save_date(self, data):
                    with open(self.json_file, 'w') as fp:
                        fp.write(data)
                def requestGlobalMetrics(self):
                    self.socket.client_fd.send(GLOBAL_METRICS_REQ)
                    data = self.socket.client_fd.recv(BUFFER_SIZE)
                    self.save_date(data)
            parser = argparse.ArgumentParser(description='telemetry')
            parser.add_argument('-f',
                                '--file',
                                nargs='*',
                                default=1,
                                help='message channel')
            parser.add_argument('-j',
                                '--json_file',
                                nargs='*',
                                default=None,
                                help='json_file option')
            args = parser.parse_args()
            file_path = args.file[0]
            client = ClientExd(args.json_file[0])
            client.getFilepath(file_path)
            client.register()
            client.requestGlobalMetrics()
            time.sleep(2)
            client.unregister()
            client.unregistered = 1
            print("Get metrics done")
        """
        )
        fileName = "query_tool.py"
        query_script = os.path.join(self.output_path, fileName)
        with open(query_script, "w") as fp:
            fp.write("#! /usr/bin/env python" + os.linesep + str(script_content))
        self.dut.session.copy_file_to(query_script, self.target_dir)
        script_file = os.path.join(self.target_dir, fileName)
        cmd = "chmod 777 {}".format(script_file)
        self.d_a_con(cmd)
        return script_file

    def init_telemetry(self):
        """transfer dpdk-telemetry-client.py to the correct python module"""
        cmds = [
            "rm -f {0}/dpdk_telemetry_client.py",
            (
                "cp -f {0}/usertools/dpdk-telemetry-client.py "
                "{0}/dpdk_telemetry_client.py"
            ),
            (
                "sed -i -e 's/class Client:/class Client(object):/g' "
                "{0}/dpdk_telemetry_client.py"
            ),
        ]
        cmd = ";".join(cmds).format(self.target_dir)
        self.d_a_con(cmd)
        self.query_tool = self.create_query_script()
        self.query_data = []

    def telemetry_query(self):
        json_name = "telemetry_data.json"
        json_file = os.path.join(self.target_dir, json_name)
        pipe = "/var/run/dpdk/default_client"
        cmd = "{0} -j {1} -f {2}".format(self.query_tool, json_file, pipe)
        output = self.d_a_con(cmd)
        msg = "failed to query metric data"
        self.verify("Get metrics done" in output, msg)
        dst_file = os.path.join(self.output_path, json_name)
        self.dut.session.copy_file_from(json_file, dst_file)
        msg = "failed to get {}".format(json_name)
        self.verify(os.path.exists(dst_file), msg)
        with open(dst_file, "r") as fp:
            try:
                query_data = json.load(fp, encoding="utf-8")
            except Exception as e:
                msg = "failed to load metrics json data"
                raise VerifyFailure(msg)
        self.logger.debug(pformat(query_data))
        metric_status = query_data.get("status_code")
        msg = ("failed to query metric data, " "return status <{}>").format(
            metric_status
        )
        self.verify("status ok" in metric_status.lower(), msg)

        return query_data.get("data")

    def telemetry_query_on_traffic(self):
        json_name = "telemetry_data_on_traffic.json"
        json_file = os.path.join(self.target_dir, json_name)
        pipe = "/var/run/dpdk/default_client"
        cmd = "{0} -j {1} -f {2}".format(self.query_tool, json_file, pipe)
        output = self.d_a_con(cmd)
        dst_file = os.path.join(self.output_path, json_name)
        self.dut.session.copy_file_from(json_file, dst_file)

    def parse_telemetry_query_on_traffic(self):
        json_name = "telemetry_data_on_traffic.json"
        dst_file = os.path.join(self.output_path, json_name)
        msg = "failed to get {}".format(json_name)
        self.verify(os.path.exists(dst_file), msg)
        with open(dst_file, "r") as fp:
            try:
                query_data = json.load(fp, encoding="utf-8")
            except Exception as e:
                msg = "failed to load metrics json data"
                raise VerifyFailure(msg)
        self.logger.debug(pformat(query_data))
        metric_status = query_data.get("status_code")
        msg = ("failed to query metric data, " "return status <{}>").format(
            metric_status
        )
        self.verify("status ok" in metric_status.lower(), msg)

        return query_data.get("data")

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_con("cat " + drv_file)
        if not output:
            msg = "unknown power driver"
            raise VerifyFailure(msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    def check_power_info_integrity(self, query_data):
        expected_keys = ["empty_poll", "full_poll", "busy_percent"]
        stats = query_data.get("stats")
        if not stats:
            msg = "telemetry failed to get data"
            raise VerifyFailure(msg)
        for key in expected_keys:
            for info in stats:
                name = info.get("name")
                value = info.get("value")
                if name == key and value is not None:
                    break
            else:
                msg = "telemetry failed to get data <{}>".format(key)
                raise VerifyFailure(msg)

    def check_busy_percent_result(self, data):
        data_on_traffic = data.get("on_traffic")
        data_traffic_stop = data.get("traffic_stop")
        key = "busy_percent"
        # busy_percent data on traffic should be non-zero number
        stats = data_on_traffic[0].get("stats")
        if not stats:
            msg = "telemetry failed to get data"
            raise VerifyFailure(msg)
        for info in stats:
            name = info.get("name")
            value = info.get("value")
            if name == key:
                break
        else:
            msg = "telemetry failed to get data <{}>".format(key)
            raise VerifyFailure(msg)
        if value is None or int(value) <= 0:
            msg = "<{}> should be non-zero number on traffic".format(key)
            self.logger.error(value)
            raise VerifyFailure(msg)
        # busy_percent data on traffic should be zero number
        stats = data_traffic_stop[0].get("stats")
        if not stats:
            msg = "telemetry failed to get data"
            raise VerifyFailure(msg)
        for info in stats:
            name = info.get("name")
            value = info.get("value")
            if name == key:
                break
        else:
            msg = "telemetry failed to get data <{}>".format(key)
            raise VerifyFailure(msg)
        if value is None or value > 0:
            msg = "<{}> should be zero after traffic stop".format(key)
            self.logger.error(value)
            raise VerifyFailure(msg)

    def verify_telemetry_power_info(self):
        """
        Check power related info reported by telemetry system
        """
        except_content = None
        try:
            self.start_l3fwd_power()
            data = self.telemetry_query()
            self.check_power_info_integrity(data[0])
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            msg = "test telemetry power info successful !!!"
            self.logger.info(msg)

    def verify_busy_percent(self):
        """
        Check busy_percent with different injected throughput
        """
        except_content = None
        try:
            self.start_l3fwd_power()
            duration = 20
            option = {
                "traffic_opt": {
                    "method": "throughput",
                    "duration": duration,
                    "interval": duration - 2,
                    "callback": self.telemetry_query_on_traffic,
                }
            }
            self.run_traffic(option)
            time.sleep(5)
            result = {
                "on_traffic": self.parse_telemetry_query_on_traffic(),
                "traffic_stop": self.telemetry_query(),
            }
            self.check_busy_percent_result(result)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            msg = "test busy percent successful !!!"
            self.logger.info(msg)

    def verify_power_driver(self):
        expected_drv = "acpi-cpufreq"
        power_drv = self.get_sys_power_driver()
        msg = "{0} should work with {1} driver on DUT".format(
            self.suite_name, expected_drv
        )
        self.verify(power_drv == expected_drv, msg)

    def preset_test_environment(self):
        self.is_l3fwd_on = None
        # init binary
        self.init_l3fwd_power()
        self.init_telemetry()

    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify_power_driver()
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        # prepare testing environment
        self.preset_test_environment()

    def tear_down_all(self):
        """Run after each test suite."""
        pass

    def set_up(self):
        """Run before each test case."""
        pass

    def tear_down(self):
        """Run after each test case."""
        self.dut.kill_all()

    def test_perf_telemetry_power_info(self):
        self.verify_telemetry_power_info()

    def test_perf_busy_percent(self):
        self.verify_busy_percent()

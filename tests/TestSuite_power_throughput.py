# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2020 Intel Corporation
#

"""
DPDK Test suite.
l3fwd-power test suite.
"""
import os
import time
import traceback
from ast import And
from copy import deepcopy
from pprint import pformat

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.utils import create_mask as dts_create_mask


class TestPowerThroughput(TestCase):
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

    def run_traffic(self, option, traffic_rate):
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # set stream into pktgen
        stream_option = {
            "stream_config": {
                "txmode": {},
                "transmit_mode": TRANSMIT_CONT,
                "rate": float(traffic_rate),
            }
        }
        stream_ids = self.add_stream_to_pktgen(stream_option)
        # run pktgen traffic
        traffic_opt = option.get("traffic_opt")
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)
        # self.tester.pktgen.measure(stream_ids, traffic_opt)
        # return result

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
            "-- "
            "--pmd-mgmt scale "
            "--max-empty-poll 128 "
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

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_con("cat " + drv_file)
        if not output:
            msg = "unknown power driver"
            raise VerifyFailure(msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    def query_cpu_freq(self):
        cmd = ";".join(
            ["cat /sys/devices/system/cpu/cpu{0}/cpufreq/scaling_cur_freq"]
        ).format(2)
        output = self.d_a_con(cmd)
        if not output:
            self.scaling_cur_freq = 0
        else:
            self.scaling_cur_freq = round(int(output))

    def get_turbo_max_freq_using_msr(self):
        cmd = "rdmsr -a 0x1ad"
        output = self.d_a_con(cmd)
        # extracting last 2 digits which holds the max freq hexa value
        max_freq_hexa_value = output[-2:]
        # Converting hexadecimal string to decimal
        turbo_max_msr_freq = int(max_freq_hexa_value, 16)
        # Converting to mhz
        turbo_max_msr_freq = turbo_max_msr_freq * 100
        return turbo_max_msr_freq

    def get_p1_freq_as_int(self):
        cmd = "cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq"
        output = self.d_a_con(cmd)
        if not output:
            return 0
        else:
            # Extracting first 4 digits as rest of them are decimal numbers
            output = int(str(output)[:4])
            # Since turbo is on and pstate disabled to extract p1 we need to
            # subtract 1 from the output value as 1 here signifies turbo on.
            # ie if p1 is 2300 the output will be 2301
            output = output - 1
            return output

    def check_core_scaling_high_traffic_results(self):
        cpu_p1_freq = self.get_p1_freq_as_int()
        # Extracting first 4 digits as rest of them are decimal numbers
        scaling_cur_freq_mhz = int(str(self.scaling_cur_freq)[:4])
        # scaling freq should be between turbo max(inclusive) and p1
        if (
            self.turbo_max_freq_mhz >= scaling_cur_freq_mhz
            and cpu_p1_freq < scaling_cur_freq_mhz
        ):
            self.msg = "Test core scaling max traffic successful !!!"
        else:
            self.msg = (
                "Test failed because current cpu freq({0} mhz) is not smaller "
                + "or equal to turbo max freq({1} mhz) and not higher than p1({2} mhz)"
            )
            self.msg = self.msg.format(
                scaling_cur_freq_mhz, self.turbo_max_freq_mhz, cpu_p1_freq
            )
            raise VerifyFailure(self.msg)

    def check_core_scaling_low_traffic_results(self):
        cpu_p1_freq = self.get_p1_freq_as_int()
        # Extracting first 4 digits as rest of them are decimal numbers
        scaling_cur_freq_mhz = int(str(self.scaling_cur_freq)[:4])
        # freq should be p1 or lower than p1
        if cpu_p1_freq >= scaling_cur_freq_mhz:
            self.msg = "Test core scaling low traffic successful !!!"
        else:
            self.msg = (
                "Test failed because current cpu freq({0} mhz) is not lower "
                + "or equal to p1({1} mhz)"
            )
            self.msg = self.msg.format(scaling_cur_freq_mhz, cpu_p1_freq)
            raise VerifyFailure(self.msg)

    def verify_core_scaling_high_traffic(self):
        """
        Check core scaling with max(rate:100) injected throughput
        """
        except_content = None
        try:
            self.start_l3fwd_power()
            duration = 10
            option = {
                "traffic_opt": {
                    "method": "throughput",
                    "interval": duration - 2,
                    "duration": duration,
                    "callback": self.query_cpu_freq,
                }
            }
            # set traffic rate
            traffic_rate = 100.0
            # run traffic with specified rate
            self.run_traffic(option, traffic_rate)
            time.sleep(5)
            # check test result
            # NOTE: using msr to get max turbo freq value because
            # in intel_pstate=disabled we can't get the exact value of max turbo
            # freq of core ie. if p1 is 2300 and we extract cpuinfo_max_freq
            #  we get 2301 that 1 at end indicates that turbo is on but
            # doesn't give max freq we can go on high traffic.
            self.turbo_max_freq_mhz = self.get_turbo_max_freq_using_msr()
            self.check_core_scaling_high_traffic_results()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            self.logger.info(self.msg)

    def verify_core_scaling_low_traffic(self):
        """
        Check core scaling with low(rate:5) injected throughput
        """
        except_content = None
        try:
            self.start_l3fwd_power()
            duration = 10
            option = {
                "traffic_opt": {
                    "method": "throughput",
                    "interval": duration - 2,
                    "duration": duration,
                    "callback": self.query_cpu_freq,
                }
            }
            traffic_rate = 5.0
            self.run_traffic(option, traffic_rate)
            time.sleep(5)
            # check test result
            self.turbo_max_freq_mhz = self.get_turbo_max_freq_using_msr()
            self.check_core_scaling_low_traffic_results()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            self.logger.info(self.msg)

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

    def test_perf_core_scaling_low_taffic(self):
        self.verify_core_scaling_low_traffic()

    def test_perf_core_scaling_high_taffic(self):
        self.verify_core_scaling_high_traffic()

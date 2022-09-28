# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

import json
import os
import re
import textwrap
import time
from pprint import pformat

from framework.pmd_output import PmdOutput

# import framework.dts as dts libs
from framework.test_case import TestCase


class TestTelemetry(TestCase):
    def create_query_script(self):
        """
        usertools/dpdk-telemetry-client.py is not user friendly(till 19.05).
        this method is used to make sure testing robust.
        """
        script_content = textwrap.dedent(
            """
            #! /usr/bin/env python
            import argparse
            import time
            import json
            from dpdk_telemetry_client import Client, DEFAULT_FP, METRICS_REQ, BUFFER_SIZE

            class ClientExd(Client):
                def __init__(self, json_file):
                    super(ClientExd, self).__init__()
                    self.json_file = json_file
                def save_date(self, data):
                    with open(self.json_file, 'w') as fp:
                        fp.write(data)
                def requestMetrics(self): # Requests metrics for given client
                    self.socket.client_fd.send(METRICS_REQ.encode())
                    data = self.socket.client_fd.recv(BUFFER_SIZE).decode()
                    return data
                def singleRequestMetrics(self):
                    data = self.requestMetrics()
                    self.save_date(data)
                def repeatedlyRequestMetrics(self, sleep_time=1, n_requests=2):
                    data_list = {}
                    for i in range(n_requests):
                        data_list[i] = self.requestMetrics()
                        time.sleep(sleep_time)
                    self.save_date(data_list)
            parser = argparse.ArgumentParser(description='dpdk telemetry tool')
            parser.add_argument('-c',
                                '--choice',
                                nargs='*',
                                default=1,
                                help='choice option')
            parser.add_argument('-n',
                                '--n_requests',
                                nargs='*',
                                default=1,
                                help='n requests option')
            parser.add_argument('-j',
                                '--json_file',
                                nargs='*',
                                default=None,
                                help='json file directory')
            print("Options Menu")
            args = parser.parse_args()
            if not args.choice or not len(args.choice):
                print("Error - Invalid request choice")
            else:
                file_path = DEFAULT_FP
                client = ClientExd(args.json_file[0])
                client.getFilepath(file_path)
                client.register()
                choice = int(args.choice[0])
                if choice == 1:
                    print("[1] Send for Metrics for all ports")
                    client.singleRequestMetrics()
                elif choice == 2:
                    print("[2] Send for Metrics for all ports recursively")
                    client.repeatedlyRequestMetrics(1)
                time.sleep(2)
                print("Unregister client")
                client.unregister()
                client.unregistered = 1
                print("Get metrics done")
        """
        )
        fileName = "query_tool.py"
        query_script = os.path.join(self.output_path, fileName)
        with open(query_script, "wb") as fp:
            fp.write(("#! /usr/bin/env python" + os.linesep + script_content).encode())
        self.dut.session.copy_file_to(query_script, self.target_dir)
        self.query_tool = ";".join(
            [
                "cd {}".format(self.target_dir),
                "chmod 777 {}".format(fileName),
                "python3 " + fileName,
            ]
        )

    def rename_dpdk_telemetry_tool(self):
        """
        transfer dpdk-telemetry-client.py to the available python module
        """
        new_name = "dpdk_telemetry_client.py"
        old_name = "dpdk-telemetry-client.py"
        cmds = [
            "rm -f {0}/{1}",
            "cp -f {0}/usertools/dpdk-telemetry-client.py {0}/{1}",
            "sed -i -e 's/class Client:/class Client(object):/g' {0}/{1}",
        ]
        cmd = ";".join(cmds).format(self.target_dir, new_name, old_name)
        self.d_a_console(cmd)
        self.create_query_script()

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = (
            "/root" + self.dut.base_dir[1:]
            if self.dut.base_dir.startswith("~")
            else self.dut.base_dir
        )
        return target_dir

    @property
    def output_path(self):
        suiteName = self.__class__.__name__[4:].lower()
        if self.logger.log_path.startswith(os.sep):
            output_path = os.path.join(self.logger.log_path, suiteName)
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            output_path = os.path.join(cur_path, self.logger.log_path, suiteName)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        return output_path

    def d_console(self, cmds):
        return self.execute_cmds(cmds, con_name="dut")

    def d_a_console(self, cmds):
        return self.execute_cmds(cmds, con_name="dut_alt")

    def get_console(self, name):
        if name == "dut":
            console = self.dut.send_expect
            msg_pipe = self.dut.get_session_output
        elif name == "dut_alt":
            console = self.dut.alt_session.send_expect
            msg_pipe = self.dut.alt_session.session.get_output_all
        else:
            msg = "{} not created".format(name)
            raise Exception(msg)
        return console, msg_pipe

    def execute_cmds(self, cmds, con_name="dut"):
        console, msg_pipe = self.get_console(con_name)
        if not cmds:
            return
        if isinstance(cmds, str):
            cmds = [cmds, "# ", 5]
        if not isinstance(cmds[0], list):
            cmds = [cmds]
        outputs = [] if len(cmds) > 1 else ""
        for item in cmds:
            expected_items = item[1]
            expected_str = expected_items or "# "
            try:
                timeout = int(item[2]) if len(item) == 3 else 5
                output = console(item[0], expected_str, timeout)
            except Exception as e:
                # self.check_process_status()
                msg = "execute '{0}' timeout".format(item[0])
                raise Exception(msg)
            time.sleep(1)
            if len(cmds) > 1:
                outputs.append(output)
            else:
                outputs = output
        return outputs

    def init_test_binary_files(self):
        # initialize testpmd
        self.testpmd_status = "close"
        self.testpmd = PmdOutput(self.dut)
        # prepare telemetry tool
        self.rename_dpdk_telemetry_tool()

    def get_allowlist(self, num=1, nic_types=2):
        self.used_ports = []
        if len(self.dut_ports) < 4 or len(self.nic_grp) < nic_types:
            self.used_ports = self.dut_ports
            return None
        pci_addrs = [
            pci_addr
            for pci_addrs in list(self.nic_grp.values())[:nic_types]
            for pci_addr in pci_addrs[:num]
        ]
        for index in self.dut_ports:
            info = self.dut.ports_info[index]
            if info["pci"] not in pci_addrs:
                continue
            self.used_ports.append(index)
        allow_list = " ".join(["-a " + pci_addr for pci_addr in pci_addrs])
        return allow_list

    def start_telemetry_server(self, allowlist=None):
        if self.testpmd_status != "close":
            return None
        # use dut first port's socket
        socket = self.dut.get_numa_id(0)
        config = "Default"
        eal_option = "--telemetry " + allowlist if allowlist else "--telemetry"
        output = self.testpmd.start_testpmd(config, eal_param=eal_option, socket=socket)
        self.testpmd_status = "running"
        self.testpmd.execute_cmd("start")
        if not self.change_flag:
            self.change_run_fileprefix(output)
        return output

    def close_telemetry_server(self):
        if self.testpmd_status == "close":
            return None
        self.testpmd.execute_cmd("stop")
        self.testpmd.quit()
        self.testpmd_status = "close"

    def get_all_xstat_data(self):
        """get nic extended statistics"""
        cmd = ["show port xstats all", "testpmd>"]
        output = self.d_console(cmd)
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
                    cur_port = int(result[0])
            elif cur_port is not None and ": " in line:
                if cur_port not in port_xstat:
                    port_xstat[cur_port] = {}
                result = line.strip().split(": ")
                if len(result) == 2 and result[0]:
                    name, value = result
                    port_xstat[cur_port][name] = int(value)
                else:
                    raise Exception("invalid data")

        return port_xstat

    def get_metric_data(self):
        json_name = "metric.json"
        json_file = os.path.join(self.target_dir, json_name)
        cmd = "{0} -c 1 -j {1}".format(self.query_tool, json_file)
        output = self.d_a_console(cmd)
        msg = "faile to query metric data"
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
                self.verify(False, msg)
        metric_status = query_data.get("status_code")
        msg = "failed to query metric data, return status <{}>".format(metric_status)
        self.verify("Status OK" in metric_status, msg)
        metric_data = {}
        for info in query_data.get("data"):
            port_index = info.get("port")
            stats = info.get("stats")
            metric_data[port_index] = {}
            for stat in stats:
                metric_data[port_index][stat.get("name")] = int(stat.get("value"))
        self.logger.debug(pformat(metric_data))
        return metric_data

    def check_telemetry_client_script(self):
        """
        check if dpdk-telemetry-client.py is available
        """
        output = self.start_telemetry_client()
        # check script select items
        expected_strs = [
            "Send for Metrics for all ports",
            "Send for Metrics for all ports recursively",
            "Send for global Metrics",
            "Unregister client",
        ]
        msg = "expected select items not existed"
        self.verify(all([item in output for item in expected_strs]), msg)
        cmd = ["1", ":", 10]
        output = self.dut_s_session.send_expect(*cmd)
        output = self.dut_s_session.session.get_output_all()
        cmd = ["4", "#", 5]
        output = self.dut_s_session.send_expect(*cmd)

    def start_telemetry_client(self):
        self.dut_s_session = self.dut.new_session()
        dpdk_tool = os.path.join(self.target_dir, "usertools/dpdk-telemetry-client.py")
        output = self.dut_s_session.send_expect("python3 " + dpdk_tool, ":", 5)
        return output

    def close_telemetry_client(self):
        cmd = "ps aux | grep -i '%s' | grep -v grep | awk {'print $2'}" % (
            "dpdk-telemetry-client.py"
        )
        out = self.d_a_console([cmd, "# ", 5])
        if out != "" and "[PEXPECT]" not in out:
            process_pid = out.splitlines()[0]
            cmd = ["kill -TERM {0}".format(process_pid), "# "]
            self.d_a_console(cmd)
        self.dut.close_session(self.dut_s_session)

    def check_metric_data(self):
        metric_data = self.get_metric_data()
        msg = "haven't get all ports metric data"
        self.verify(len(self.used_ports) == len(metric_data), msg)
        port_index_list = list(range(len(self.used_ports)))
        for port_index in metric_data:
            msg = "<{}> is not the expected port".format(port_index)
            self.verify(port_index is not None and port_index in port_index_list, msg)
        output = self.dut.get_session_output()
        self.verify("failed" not in output, output)
        # set rx/tx configuration by testpmd
        cmds = [["stop", "testpmd>", 15], ["clear port xstats all", "testpmd>", 15]]
        self.d_console(cmds)
        metric_data = self.get_metric_data()
        xstats = self.get_all_xstat_data()
        self.compare_data(metric_data, xstats)

    def compare_data(self, metric, xstat):
        error_msg = []
        # Ensure # of ports stats being returned == # of ports
        msg = "metric and xstat data are not the same"
        self.verify(len(metric) == len(xstat), msg)
        # check if parameters are the same
        for port_id in metric:
            if len(metric[0]) == len(xstat[0]):
                continue
            xstat_missed_paras = []
            for keyname in list(metric[0].keys()):
                if keyname in list(xstat[0].keys()):
                    continue
                xstat_missed_paras.append(keyname)
            metric_missed_paras = []
            for keyname in list(xstat[0].keys()):
                if keyname in list(metric[0].keys()):
                    continue
                metric_missed_paras.append(keyname)
            msg = os.linesep.join(
                [
                    "testpmd xstat missed parameters:: ",
                    pformat(xstat_missed_paras),
                    "telemetry metric missed parameters:: ",
                    pformat(metric_missed_paras),
                ]
            )
            error_msg.append(msg)
        # check if metric parameters and values are the same
        if metric != xstat:
            msg = "telemetry metric data is not the same as testpmd xstat data"
            error_msg.append(msg)
            msg_fmt = "port {} <{}>: metric is <{}>, xstat is is <{}>".format
            for port_index, info in list(metric.items()):
                for name, value in list(info.items()):
                    if value == xstat[port_index][str(name)]:
                        continue
                    error_msg.append(
                        msg_fmt(port_index, name, value, xstat[port_index][name])
                    )
        # check if metric parameters value should be zero
        # ensure extended NIC stats are 0
        is_clear = any([any(data.values()) for data in list(metric.values())])
        if is_clear:
            msg = "telemetry metric data are not default value"
            error_msg.append(msg)
            msg_fmt = "port {} <{}>: metric is <{}>".format
            for port_index, info in list(metric.items()):
                for name, value in list(info.items()):
                    if not value:
                        continue
                    error_msg.append(msg_fmt(port_index, name, value))
        # show exception check content
        if error_msg:
            self.logger.error(os.linesep.join(error_msg))
            self.verify(False, "telemetry metric data error")

    def get_ports_by_nic_type(self):
        nic_grp = {}
        for info in self.dut.ports_info:
            nic_type = info["type"]
            if nic_type not in nic_grp:
                nic_grp[nic_type] = []
            nic_grp[nic_type].append(info["pci"])
        return nic_grp

    #
    # test content
    #
    def get_file_prefix(self, out):
        m = re.search("socket /var/run/dpdk/(.+?)/", out)
        if m:
            self.file_prefix = m.group(1) if m.group(1) != "rte" else None

    def change_run_fileprefix(self, out):
        self.get_file_prefix(out)
        if self.file_prefix:
            cmd1 = 'sed -i \'s/self.socket.send_fd.connect("\/var\/run\/dpdk\/.*\/telemetry")/self.socket.send_fd.connect("\/var\/run\/dpdk\/{0}\/telemetry")/g\' {1}'.format(
                self.file_prefix,
                os.path.join(self.target_dir, "usertools/dpdk-telemetry-client.py"),
            )
            cmd2 = 'sed -i \'s/self.socket.send_fd.connect("\/var\/run\/dpdk\/.*\/telemetry")/self.socket.send_fd.connect("\/var\/run\/dpdk\/{0}\/telemetry")/g\' {1}'.format(
                self.file_prefix,
                os.path.join(self.target_dir, "dpdk_telemetry_client.py"),
            )
            self.d_a_console(cmd1)
            self.d_a_console(cmd2)
            self.change_flag = True

    def verify_basic_script(self):
        """
        verify dpdk-telemetry-client.py script
        """
        try:
            self.start_telemetry_server()
            time.sleep(1)
            self.check_telemetry_client_script()
            self.close_telemetry_client()
            self.close_telemetry_server()
        except Exception as e:
            self.close_telemetry_client()
            self.close_telemetry_server()
            raise Exception(e)

    def verify_basic_connection(self):
        try:
            self.start_telemetry_server()
            metric_data = self.get_metric_data()
            port_index_list = list(range(len(self.dut_ports)))
            msg = "haven't get all ports metric data"
            self.verify(len(self.dut_ports) == len(metric_data), msg)
            for port_index in metric_data:
                msg = "<{}> is not the expected port".format(port_index)
                self.verify(
                    port_index is not None and port_index in port_index_list, msg
                )
            output = self.dut.get_session_output()
            self.verify("failed" not in output, output)
            self.close_telemetry_server()
        except Exception as e:
            self.close_telemetry_server()
            raise Exception(e)

    def verify_same_nic_with_2ports(self):
        msg = os.linesep.join(["no enough ports", pformat(self.nic_grp)])
        self.verify(len(list(self.nic_grp.values())[0]) >= 2, msg)
        try:
            # check and verify error show on testpmd
            allowlist = self.get_allowlist(num=2, nic_types=1)
            self.start_telemetry_server(allowlist)
            # check telemetry metric data
            self.check_metric_data()
            self.close_telemetry_server()
        except Exception as e:
            self.close_telemetry_server()
            raise Exception(e)

    def verify_same_nic_with_4ports(self):
        msg = os.linesep.join(
            ["no enough ports, 4 ports at least", pformat(self.nic_grp)]
        )
        self.verify(len(list(self.nic_grp.values())[0]) >= 4, msg)
        try:
            self.used_ports = self.dut_ports
            self.start_telemetry_server()
            # check telemetry metric data
            self.check_metric_data()
            self.close_telemetry_server()
        except Exception as e:
            self.close_telemetry_server()
            raise Exception(e)

    def verify_different_nic_with_2ports(self):
        # check ports total number
        msg = os.linesep.join(
            ["no enough nic types, 2 nic types at least", pformat(self.nic_grp)]
        )
        self.verify(len(list(self.nic_grp.keys())) >= 2, msg)
        try:
            allowlist = self.get_allowlist()
            self.start_telemetry_server(allowlist)
            # check telemetry metric data
            self.check_metric_data()
            self.close_telemetry_server()
        except Exception as e:
            self.close_telemetry_server()
            raise Exception(e)

    def verify_different_nic_with_4ports(self):
        msg = os.linesep.join(
            ["no enough nic types, 2 nic types at least", pformat(self.nic_grp)]
        )
        self.verify(len(list(self.nic_grp.keys())) >= 2, msg)
        msg = os.linesep.join(
            ["no enough ports, 2 ports/nic type at least", pformat(self.nic_grp)]
        )
        self.verify(
            all(
                [
                    pci_addrs and len(pci_addrs) >= 2
                    for pci_addrs in list(self.nic_grp.values())
                ]
            ),
            msg,
        )

        try:
            self.used_ports = self.dut_ports
            self.start_telemetry_server()
            # check telemetry metric data
            self.check_metric_data()
            self.close_telemetry_server()
        except Exception as e:
            self.close_telemetry_server()
            raise Exception(e)

    def start_telemetry_server_and_get_module_eeprom(self, port_id):
        try:
            self.change_flag = True
            self.dut.bind_interfaces_linux(self.drivername)
            out = self.start_telemetry_server()
            self.tester.is_interface_up(self.tester_iface0)
            p = re.search("socket /var/run/dpdk/(.+?)/", out)
            self.start_dpdk_telemetry(p.group(1))
            module_eeprom_output = self.dut_telemetry.send_expect(
                "/ethdev/module_eeprom,{}".format(port_id), "--> "
            )
            self.close_telemetry_server()
            return module_eeprom_output
        except Exception as e:
            self.close_telemetry_server()
            raise Exception(e)

    def start_dpdk_telemetry(self, *args):
        self.dut_telemetry = self.dut.new_session()
        dpdk_tool = os.path.join(self.target_dir, "usertools/dpdk-telemetry.py")
        self.dut_telemetry.send_expect(
            "python3 " + dpdk_tool + " -f {}".format(args[0]), "--> ", 5
        )

    def verify_nic_laser_power_via_dpdk(self, laser_powers, *ports):
        for laser_power, port in zip(laser_powers, ports):
            laser_power_via_dpdk = self.get_nic_laser_power_via_dpdk(port)
            dpdk_float_values = self.get_float_laser_power_values(laser_power_via_dpdk)
            eth_float_values = self.get_float_laser_power_values(laser_power)
            test_flag = [
                abs(v_d - v_e) for v_d, v_e in zip(dpdk_float_values, eth_float_values)
            ]
            self.logger.info(
                "dpdk:{} eth:{}".format(dpdk_float_values, eth_float_values)
            )
            self.verify(
                [flag <= 0.1 for flag in test_flag],
                "dpdk:{} eth:{},get the incorrect laser power values".format(
                    dpdk_float_values, eth_float_values
                ),
            )

    def verify_laser_Power_in_different_optical_modules(self, laser_powers, *ports):
        laser_power_via_dpdk = self.get_nic_laser_power_via_dpdk(ports[-1])
        dpdk_float_values = self.get_float_laser_power_values(laser_power_via_dpdk)
        eth_float_values = self.get_float_laser_power_values(laser_powers[0])
        self.logger.info(
            "dpdk port 1: {}   eth port 0: {}".format(
                dpdk_float_values, eth_float_values
            )
        )
        test_flag = [
            abs(v_d - v_e) for v_d, v_e in zip(dpdk_float_values, eth_float_values)
        ]
        self.verify(
            [flag > 0.1 for flag in test_flag],
            "different optical modules should have different laser power values",
        )

    def verify_laser_Power_in_same_optical_modules(self, laser_powers, *ports):
        laser_power_via_dpdk = self.get_nic_laser_power_via_dpdk(ports[-1])
        dpdk_float_values = self.get_float_laser_power_values(laser_power_via_dpdk)
        eth_float_values = self.get_float_laser_power_values(laser_powers[0])
        self.logger.info(
            "dpdk port 1: {}   eth port 0: {}".format(
                dpdk_float_values, eth_float_values
            )
        )
        test_flag = [
            abs(v_d - v_e) for v_d, v_e in zip(dpdk_float_values, eth_float_values)
        ]
        self.verify(
            [flag <= 0.1 for flag in test_flag],
            "same optical modules should have same laser power values",
        )

    def get_float_laser_power_values(self, output):
        p = re.findall(r"(\d+\.\d+.)", output)
        float_list = list(map(float, p))
        return float_list

    def get_nic_laser_power_via_ethtool(self, intf):
        output = self.d_a_console(
            "ethtool -m {} | grep 'Laser output power'".format(intf)
        )
        rex_output = re.search(r"Laser output power\s+:.*", output)
        if not rex_output:
            return False
        return rex_output.group()

    def get_nic_laser_power_via_dpdk(self, port):
        out = self.start_telemetry_server_and_get_module_eeprom(port)
        laser_power_via_dpdk = self.get_nic_laser_power_via_dpdk_rex(out)
        return laser_power_via_dpdk

    def get_nic_laser_power_via_dpdk_rex(self, output):
        rex_output = re.search(r'"Laser output power":.*?dBm"', output)
        if not rex_output:
            return False
        return rex_output.group()

    def check_interface_link_up(self, intf):
        try:
            self.d_a_console("ifconfig {} up".format(intf))
            link = self.dut.is_interface_up(intf)
            self.verify(link, "link is down")
        except Exception as e:
            self.d_a_console("ifconfig {} up".format(intf))
        finally:
            time.sleep(3)

    def skip_unsupported_get_laser_power(self, *intfs):
        laser_power_list = []
        for intf in intfs:
            output = self.get_nic_laser_power_via_ethtool(intf)
            if not output:
                return False
            laser_power_list.append(output)
        return laser_power_list

    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run before each test suite
        """
        # get ports information
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf1_intf = self.dut.ports_info[self.dut_ports[1]]["intf"]
        self.tester_iface0 = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[0])
        )
        self.init_test_binary_files()
        self.nic_grp = self.get_ports_by_nic_type()
        self.used_ports = []
        self.change_flag = False

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.bind_interfaces_linux(self.drivername)

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.bind_interfaces_linux(self.drivername)

    def test_basic_connection(self):
        """
        basic connection for testpmd and telemetry client
        """
        self.verify_basic_script()
        self.verify_basic_connection()

    def test_same_nic_with_2ports(self):
        """
        Stats of 2 ports for testpmd and telemetry with same type nic
        """
        self.verify_same_nic_with_2ports()

    def test_read_nic_laser_power_via_dpdk(self):
        """
        read laser power, check testpmd show correct laser power
        """
        self.dut.bind_interfaces_linux(self.kdriver)
        self.check_interface_link_up(self.pf0_intf)
        laser_power_list = self.skip_unsupported_get_laser_power(self.pf0_intf)
        self.skip_case(laser_power_list, "The test need Optical module to support")
        self.verify_nic_laser_power_via_dpdk(laser_power_list, self.dut_ports[0])

    def test_check_laser_power_in_different_optical_modules(self):
        """
        set different optical modules in two ports and check the testpmd show different laser power
        """
        self.dut.bind_interfaces_linux(self.kdriver)
        [self.check_interface_link_up(i) for i in [self.pf0_intf, self.pf1_intf]]
        laser_power_list = self.skip_unsupported_get_laser_power(
            self.pf0_intf, self.pf1_intf
        )
        self.skip_case(laser_power_list, "The test need Optical module to support")
        float_list = [
            self.get_float_laser_power_values(laser_power)
            for laser_power in laser_power_list
        ]
        self.skip_case(
            abs(float_list[0][0] - float_list[1][0]) > 0.1
            and abs(float_list[0][1] - float_list[1][1]) > 0.1,
            "The test need different optical module in two ports",
        )
        self.verify_laser_Power_in_different_optical_modules(
            laser_power_list, self.dut_ports[0], self.dut_ports[1]
        )

    def test_check_laser_power_in_same_optical_modules(self):
        """
        set same optical modules in two ports and check the testpmd show same laser power
        """
        self.dut.bind_interfaces_linux(self.kdriver)
        [self.check_interface_link_up(i) for i in [self.pf0_intf, self.pf1_intf]]
        laser_power_list = self.skip_unsupported_get_laser_power(
            self.pf0_intf, self.pf1_intf
        )
        self.skip_case(laser_power_list, "The test need Optical module to support")
        float_list = [
            self.get_float_laser_power_values(laser_power)
            for laser_power in laser_power_list
        ]
        self.skip_case(
            abs(float_list[0][0] - float_list[1][0]) <= 0.1
            and abs(float_list[0][1] - float_list[1][1]) <= 0.1,
            "The test need same optical module in two ports",
        )
        self.verify_laser_Power_in_same_optical_modules(
            laser_power_list, self.dut_ports[0], self.dut_ports[1]
        )

# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2020 Intel Corporation
#

"""
DPDK Test suite.
Malicious driver event indication process test suite.
"""
import os
import re
import time
import traceback
from contextlib import contextmanager

import framework.utils as utils
from framework.exception import VerifyFailure
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestSuiteMaliciousDrvEventIndication(TestCase):
    def d_con(self, cmd):
        _cmd = [cmd, "# ", 10] if isinstance(cmd, str) else cmd
        return self.dut.send_expect(*_cmd)

    def d_a_con(self, cmd):
        _cmd = [cmd, "# ", 10] if isinstance(cmd, str) else cmd
        return self.dut.alt_session.send_expect(*_cmd)

    def vf_pmd_con(self, cmd):
        if not self.vf_pmd_session:
            return
        _cmd = [cmd, "# ", 10] if isinstance(cmd, str) else cmd
        output = self.vf_pmd_session.session.send_expect(*_cmd)
        return output

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = (
            "/root" + self.dut.base_dir[1:]
            if self.dut.base_dir.startswith("~")
            else self.dut.base_dir
        )
        return target_dir

    def preset_dpdk_compilation(self):
        cmd = (
            ";".join(
                [
                    "cd %s",
                    "rm -f app/test-pmd/bak_txonly.c",
                    "cp -f app/test-pmd/txonly.c app/test-pmd/bak_txonly.c",
                    "sed -i 's/nb_tx = rte_eth_tx_burst/for \(nb_pkt = 0; nb_pkt < nb_pkt_per_burst; nb_pkt\+\+\) "
                    "\{ pkts_burst\[nb_pkt\]->data_len = 15 ;\} nb_tx = rte_eth_tx_burst/g' app/test-pmd/txonly.c",
                ]
            )
            % self.target_dir
        )
        self.d_a_con(cmd)
        # rebuild dpdk source code
        self.dut.build_install_dpdk(self.target)

    @contextmanager
    def restore_dpdk_compilation(self):
        try:
            yield
        finally:
            cmd = ";".join(
                [
                    "cd {target}",
                    "rm -f app/test-pmd/txonly.c",
                    "cp -f app/test-pmd/bak_txonly.c app/test-pmd/txonly.c",
                ]
            ).format(
                **{
                    "target": self.target_dir,
                }
            )
            self.d_a_con(cmd)
            # rebuild dpdk source code
            self.dut.build_install_dpdk(self.target)

    def vf_create(self):
        port_id = 0
        port_obj = self.dut.ports_info[port_id]["port"]
        self.dut.generate_sriov_vfs_by_port(port_id, 1)
        pf_pci = port_obj.pci
        sriov_vfs_port = self.dut.ports_info[port_id].get("vfs_port")
        if not sriov_vfs_port:
            msg = "failed to create vf on dut port {}".format(pf_pci)
            raise VerifyFailure(msg)
        for port in sriov_vfs_port:
            port.bind_driver(driver=self.drivername)
        vf_mac = "00:12:34:56:78:01"
        self.vf_ports_info[port_id] = {
            "pf_pci": pf_pci,
            "vfs_pci": port_obj.get_sriov_vfs_pci(),
            "vf_mac": vf_mac,
        }
        time.sleep(1)

    def vf_destroy(self):
        if not self.vf_ports_info:
            return
        for port_id, _ in self.vf_ports_info.items():
            self.dut.destroy_sriov_vfs_by_port(port_id)
            port_obj = self.dut.ports_info[port_id]["port"]
            port_obj.bind_driver(self.drivername)
        self.vf_ports_info = None

    def init_pf_testpmd(self):
        self.pf_testpmd = os.path.join(self.target_dir, self.dut.apps_name["test-pmd"])

    def start_pf_testpmd(self):
        core_mask = utils.create_mask(self.pf_pmd_cores)
        cmd = (
            "{bin} "
            "-v "
            "-c {core_mask} "
            "-n {mem_channel} "
            "--file-prefix={prefix} "
            "{whitelist} "
            "-- -i "
        ).format(
            **{
                "bin": self.pf_testpmd,
                "core_mask": core_mask,
                "mem_channel": self.dut.get_memory_channels(),
                "whitelist": self.pf_pmd_whitelist,
                "prefix": "pf_pmd",
            }
        )
        self.d_con([cmd, "testpmd> ", 120])
        self.is_pf_pmd_on = True
        time.sleep(1)

    def close_pf_testpmd(self):
        if not self.is_pf_pmd_on:
            return
        self.d_con(["quit", "# ", 15])
        self.is_pf_pmd_on = False

    def get_pf_testpmd_reponse(self):
        output = self.dut.get_session_output(timeout=2)
        return output

    def init_vf_testpmd(self):
        self.vf_pmd_session_name = "vf_testpmd"
        self.vf_pmd_session = self.dut.create_session(self.vf_pmd_session_name)
        self.vf_pmdout = PmdOutput(self.dut, self.vf_pmd_session)

    def start_vf_testpmd(self):
        self.vf_pmdout.start_testpmd(
            self.vf_pmd_cores,
            eal_param="-v {}".format(self.vf_pmd_allowlst),
            prefix="vf_pmd",
        )
        self.is_vf_pmd_on = True
        cmds = [
            "set fwd txonly",
            "start",
        ]
        [self.vf_pmd_con([cmd, "testpmd> ", 15]) for cmd in cmds]
        time.sleep(1)

    def close_vf_testpmd(self):
        if not self.is_vf_pmd_on:
            return
        self.vf_pmd_con(["quit", "# ", 15])
        self.is_vf_pmd_on = False

    def get_vf_testpmd_reponse(self):
        if not self.vf_pmd_session:
            return ""
        output = self.vf_pmd_session.session.get_output_all()
        return output

    def check_event_is_detected(self):
        pf_output = self.get_pf_testpmd_reponse()
        expected_strs = [
            "malicious programming detected",
            "TX driver issue detected on PF",
            "TX driver issue detected on VF 0 1times",
        ]
        for expected_str in expected_strs:
            msg = "'{}' not display".format(expected_str)
            self.verify(expected_str in pf_output, msg)
        pat = "Malicious Driver Detection event 0x(\d+) on TX queue (\d+) PF number 0x(\d+) VF number 0x(\d+) device " + self.vf_ports_info[
            0
        ].get(
            "pf_pci"
        )
        result = re.findall(pat, pf_output)
        msg = "'Malicious Driver Detection event not detected"
        self.verify(result and len(result), msg)

    def check_event_counter_number(self, total):
        pf_output = self.get_pf_testpmd_reponse()
        expected_str = "TX driver issue detected on VF 0 {0}times".format(total)
        msg = "'{}' not display".format(expected_str)
        self.verify(expected_str in pf_output, msg)

    def verify_malicious_driver_event_detected(self):
        except_content = None
        try:
            self.start_pf_testpmd()
            self.start_vf_testpmd()
            self.check_event_is_detected()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_vf_testpmd()
            self.close_pf_testpmd()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_malicious_driver_event_counter_number(self):
        except_content = None
        try:
            self.start_pf_testpmd()
            total = 3
            for _ in range(total):
                self.start_vf_testpmd()
                self.close_vf_testpmd()
            self.check_event_counter_number(total)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_vf_testpmd()
            self.close_pf_testpmd()
        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def verify_supported_nic(self):
        supported_drivers = ["i40e"]
        result = all(
            [
                self.dut.ports_info[index]["port"].default_driver in supported_drivers
                for index in self.dut_ports
            ]
        )
        msg = "current nic <0> is not supported".format(self.nic)
        self.verify(result, msg)

    def preset_pmd_res(self):
        # get whitelist and cores
        socket = self.dut.get_numa_id(self.dut_ports[0])
        corelist = self.dut.get_core_list("1S/6C/1T", socket=socket)[2:]
        self.pf_pmd_whitelist = "-a " + self.vf_ports_info[0].get("pf_pci")
        self.pf_pmd_cores = corelist[:2]
        self.vf_pmd_allowlst = "-a " + self.vf_ports_info[0].get("vfs_pci")[0]
        self.vf_pmd_cores = corelist[2:]

    def init_params(self):
        self.is_pf_pmd_on = self.is_vf_pmd_on = None
        self.vf_ports_info = {}

    def preset_test_environment(self):
        self.preset_dpdk_compilation()

    def destroy_resource(self):
        with self.restore_dpdk_compilation():
            self.vf_destroy()
            if self.vf_pmd_session:
                self.dut.close_session(self.vf_pmd_session)
                self.vf_pmd_session = None

    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Not enough ports")
        self.verify_supported_nic()
        # prepare testing environment
        self.preset_test_environment()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.destroy_resource()

    def set_up(self):
        """
        Run before each test case.
        """
        self.init_params()
        self.init_pf_testpmd()
        self.init_vf_testpmd()
        self.vf_create()
        self.preset_pmd_res()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        self.vf_destroy()
        if self.vf_pmd_session:
            self.dut.close_session(self.vf_pmd_session)
            self.vf_pmd_session = None

    def test_malicious_driver_event_detected(self):
        """
        Check log output when malicious driver events is detected
        """
        self.verify_malicious_driver_event_detected()

    def test_malicious_driver_event_counter_number(self):
        """
        Check the event counter number for malicious driver events
        """
        self.verify_malicious_driver_event_counter_number()

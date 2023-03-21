# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

import re
import time
import traceback

# import bonding lib(common methods for pmd bonding command)
import tests.bonding as bonding
from framework.exception import VerifyFailure
from framework.test_case import TestCase

from .bonding import FRAME_SIZE_64, MODE_LACP


######################
# bonding 802.3ad mode
######################
class TestVFPmdBonded8023AD(TestCase):
    AGG_MODES = ["bandwidth", "stable", "count"]
    DEDICATED_QUEUES = ["disable", "enable"]

    #
    # On dut, dpdk bonding
    #

    def set_8023ad_agg_mode(self, bond_port, mode="bandwidth"):
        """
        set bonding agg_mode <port_id> <agg_name>

        Set 802.11AD Aggregator Mode
        """
        cmd = "set bonding agg_mode %d %s" % (bond_port, mode)
        self.bond_inst.d_console(cmd)
        cur_mode = self.bond_inst.get_bonding_info(bond_port, "agg_mode")
        if mode == cur_mode:
            fmt = "set bonding agg_mode <{0}> successfully"
            self.logger.info(fmt.format(mode))
        else:
            msg = "failed to set bonding agg_mode <{0}>".format(mode)
            self.logger.error(msg)
            raise VerifyFailure(msg)

    def get_8023ad_agg_mode(self, bond_port):
        """
        get 802.3ad mode  aggregator Mode
        """
        cur_mode = self.bond_inst.get_bonding_info(bond_port, "agg_mode")
        return cur_mode

    def set_8023ad_dedicated_queues(self, bond_port, status="disable"):
        """
        set 802.11AD dedicated_queues mode(enable|disable)
        """
        cmds = [
            [
                "set bonding lacp dedicated_queues %s %s" % (bond_port, status),
                ["", "port %s failed" % bond_port, False],
                2,
            ],
        ]
        out = self.bond_inst.d_console(cmds)
        # when set 'hw'
        if status == "enable":
            expected_msg = "queues for LACP control packets enabled"
            err_fmt = "link bonding mode 4 (802.3ad) set {0} failed"
            self.verify(expected_msg in out, err_fmt.format(status))
        elif status == "disable":
            expected_msg = "queues for LACP control packets disabled"
            err_fmt = "link bonding mode 4 (802.3ad) set {0} failed"
            self.verify(expected_msg in out, err_fmt.format(status))

    def set_special_command(self, bond_port):
        cmds = [
            "set allmulti 0 on",
            "set allmulti 1 on",
            "set allmulti {} on".format(bond_port),
            "set portlist {}".format(bond_port),
        ]
        [self.bond_inst.d_console([cmd, "testpmd>", 15]) for cmd in cmds]

    def set_8023ad_bonded(self, slaves, bond_mode, ignore=True):
        """set 802.3ad bonded mode for the specified bonding mode"""
        specified_socket = self.dut.get_numa_id(slaves[0])
        # create bonded device, add slaves in it
        bond_port = self.bond_inst.create_bonded_device(bond_mode, specified_socket)
        if not ignore:
            # when no slave attached, mac should be 00:00:00:00:00:00
            self.bonding_8023ad_check_macs_without_slaves(bond_port)
        # add slave
        self.bond_inst.add_slave(bond_port, False, "", *slaves)
        # set special command
        self.set_special_command(bond_port)
        return bond_port

    def set_8023ad_bonded2(self, slaves, bond_mode, ignore=True):
        """set 802.3ad bonded mode for the specified bonding mode"""
        specified_socket = self.dut.get_numa_id(slaves[0])
        # create bonded device, add slaves in it
        bond_port = self.bond_inst.create_bonded_device(bond_mode, specified_socket)
        if not ignore:
            # when no slave attached, mac should be 00:00:00:00:00:00
            self.bonding_8023ad_check_macs_without_slaves(bond_port)
        # add slave
        self.bond_inst.add_slave(bond_port, False, "", *slaves)
        return bond_port

    def get_pci_link(self, slaves):
        """get slaves ports pci address"""
        slaves_pci = []
        for port_id in slaves:
            slaves_pci.append(self.dut.ports_info[port_id]["pci"])
        if not slaves_pci:
            msg = "can't find tx_port pci"
            self.logger.error(msg)
            raise VerifyFailure(msg)
        return slaves_pci

    def set_bond_port_ready(self, tx_port, bond_port):
        cmd = "set portlist {0},{1}".format(tx_port, bond_port)
        self.bond_inst.d_console(cmd)
        # for port link up is slow and unstable,
        # every port should start one by one
        cmds = []
        port_num = len(self.sriov_vfs_port)
        start_fmt = "port start {0}".format
        for cnt in range(port_num):
            cmds.append([start_fmt(cnt), "", 5])
        self.bond_inst.d_console(cmds)
        time.sleep(10)
        self.bond_inst.d_console([start_fmt(self.bond_port), "", 15])
        time.sleep(5)
        self.bond_inst.d_console(["start", "", 10])
        self.verify(
            self.bond_inst.testpmd.wait_link_status_up("all"),
            "Failed to set bond port ready!!!",
        )

    def run_8023ad_pre(self, slaves, bond_mode):
        bond_port = self.set_8023ad_bonded(slaves, bond_mode)
        # should set port to stop and make sure port re-sync with parter when
        # testpmd linking with switch equipment
        cmds = ["port stop all", "", 15]
        self.bond_inst.d_console(cmds)
        time.sleep(2)
        cmds = ["port start all", "", 10]
        self.bond_inst.d_console(cmds)
        self.verify(
            self.bond_inst.testpmd.wait_link_status_up("all"),
            "run_8023ad_pre: Failed to start all port",
        )
        return bond_port

    def bonding_8023ad_check_macs_without_slaves(self, bond_port):
        query_type = "mac"
        bond_port_mac = self.bond_inst.get_port_mac(bond_port, query_type)
        default_mac = "00:00:00:00:00:00"
        if bond_port_mac == default_mac:
            msg = "bond port default mac is [{0}]".format(default_mac)
            self.logger.info(msg)
        else:
            fmt = "bond port default mac is [{0}], not expected mac"
            msg = fmt.format(bond_port_mac)
            self.logger.warning(msg)

    def bonding_8023ad_check_macs(self, slaves, bond_port):
        """check if bonded device's mac is one of its slaves mac"""
        query_type = "mac"
        bond_port_mac = self.bond_inst.get_port_mac(bond_port, query_type)
        if bond_port_mac == "00:00:00:00:00:00":
            msg = "bond port hasn't set mac address"
            self.logger.info(msg)
            return

        for port_id in slaves:
            slave_mac = self.bond_inst.get_port_info(port_id, query_type)
            if bond_port_mac == slave_mac:
                fmt = "bonded device's mac is slave [{0}]'s mac [{1}]"
                msg = fmt.format(port_id, slave_mac)
                self.logger.info(msg)
                return port_id
        else:
            fmt = "bonded device's current mac [{0}] " + "is not one of its slaves mac"
            msg = fmt.format(bond_port_mac)
            # it is not supported by dpdk, but supported by linux normal
            # bonding/802.3ad tool
            self.logger.warning("bonding_8023ad_check_macs: " + msg)

    def check_bonded_device_mac_change(self, slaves, bond_port):
        remove_slave = 0
        cur_slaves = slaves[1:]
        self.bond_inst.remove_slaves(bond_port, False, *[remove_slave])
        self.bonding_8023ad_check_macs(cur_slaves, bond_port)

    def check_bonded_device_start(self, bond_port):
        cmds = [
            ["port stop all", "", 15],
            ["port start %s" % bond_port, "", 10],
            ["start", [" ", "core dump", False]],
        ]
        self.bond_inst.d_console(cmds)
        time.sleep(2)

    def stop_bonded_device(self, bond_port):
        cmds = [
            ["stop", "", 10],
            ["port stop %s" % bond_port, "", 10],
        ]
        self.bond_inst.d_console(cmds)
        time.sleep(2)

    def check_bonded_device_up_down(self, bond_port):
        # stop bonded device
        cmd = "port stop {0}".format(bond_port)
        self.bond_inst.d_console(cmd)
        status = self.bond_inst.get_port_info(bond_port, "link_status")
        if status != "down":
            msg = "bond port {0} fail to set down".format(bond_port)
            self.logger.error(msg)
            raise VerifyFailure(msg)
        else:
            msg = "bond port {0} set down successful !".format(bond_port)
            self.logger.info(msg)
        # start bonded device
        cmds = ["port start {0}".format(bond_port), "", 10]
        self.bond_inst.d_console(cmds)
        self.verify(
            self.bond_inst.testpmd.wait_link_status_up("all", timeout=30),
            "bond port {0} fail to set up".format(bond_port),
        )

    def check_bonded_device_promisc_mode(self, slaves, bond_port):
        # disable bonded device promiscuous mode
        cmd = "set promisc {0} off".format(bond_port)
        self.bond_inst.d_console(cmd)
        time.sleep(2)
        status = self.bond_inst.get_port_info(bond_port, "promiscuous_mode")
        if status != "disabled":
            fmt = "bond port {0} fail to set promiscuous mode disabled"
            msg = fmt.format(bond_port)
            self.logger.warning(msg)
        else:
            fmt = "bond port {0} set promiscuous mode disabled successful !"
            msg = fmt.format(bond_port)
            self.logger.info(msg)
        self.bond_inst.d_console("start")
        time.sleep(2)
        # check slave promiscuous mode
        for port_id in slaves:
            status = self.bond_inst.get_port_info(port_id, "promiscuous_mode")
            if status != "disabled":
                fmt = (
                    "slave port {0} promiscuous mode "
                    "isn't the same as bond port 'disabled', "
                )
                msg = fmt.format(port_id)
                self.logger.warning(msg)
                # dpdk developer hasn't completed this function as linux
                # document description about `Promiscuous mode`, ignore it here
                # temporarily
                # raise VerifyFailure(msg)
            else:
                fmt = "slave port {0} promiscuous mode is 'disabled' too"
                msg = fmt.format(port_id)
                self.logger.info(msg)
        # enable bonded device promiscuous mode
        cmd = "set promisc {0} on".format(bond_port)
        self.bond_inst.d_console(cmd)
        time.sleep(3)
        status = self.bond_inst.get_port_info(bond_port, "promiscuous_mode")
        if status != "enabled":
            fmt = "bond port {0} fail to set promiscuous mode enabled"
            msg = fmt.format(bond_port)
            self.logger.error(msg)
            raise VerifyFailure(msg)
        else:
            fmt = "bond port {0} set promiscuous mode enabled successful !"
            msg = fmt.format(bond_port)
            self.logger.info(msg)
        # check slave promiscuous mode
        for port_id in slaves:
            status = self.bond_inst.get_port_info(port_id, "promiscuous_mode")
            if status != "enabled":
                fmt = (
                    "slave port {0} promiscuous mode "
                    + "isn't the same as bond port 'enabled'"
                )
                msg = fmt.format(port_id)
                self.logger.warning(msg)
                # dpdk developer hasn't completed this function as linux
                # document description about `Promiscuous mode`, ignore it here
                # temporarily
                # raise VerifyFailure(msg)
            else:
                fmt = "slave port {0} promiscuous mode is 'enabled' too"
                msg = fmt.format(port_id)
                self.logger.info(msg)

    def check_8023ad_agg_modes(self, slaves, bond_mode):
        """check aggregator mode"""
        check_results = []
        default_agg_mode = "stable"
        for mode in self.AGG_MODES:
            try:
                self.bond_inst.start_testpmd(self.eal_param)
                bond_port = self.set_8023ad_bonded(slaves, bond_mode)
                cur_agg_mode = self.get_8023ad_agg_mode(bond_port)
                if cur_agg_mode != default_agg_mode:
                    fmt = "link bonding mode 4 (802.3ad) default agg mode " "isn't {0}"
                    msg = fmt.format(default_agg_mode)
                    self.logger.warning(msg)
                # ignore default mode
                if mode == default_agg_mode:
                    fmt = "link bonding mode 4 (802.3ad) " "current agg mode is {0}"
                    msg = fmt.format(mode)
                    self.logger.info(msg)
                    continue
                cmds = [["port stop all", "", 15], ["port start all", "", 15]]
                self.bond_inst.d_console(cmds)
                self.set_8023ad_agg_mode(bond_port, mode)
            except Exception as e:
                check_results.append(e)
                print(traceback.format_exc())
            finally:
                self.bond_inst.close_testpmd()
                time.sleep(2)

        if check_results:
            for result in check_results:
                self.logger.error(result)
            raise VerifyFailure("check_8023ad_agg_modes is failed")

    def check_8023ad_dedicated_queues(self, slaves, bond_mode):
        """check 802.3ad dedicated queues"""
        check_results = []
        default_slow_queue = "unknown"
        for mode in self.DEDICATED_QUEUES:
            try:
                self.bond_inst.start_testpmd(self.eal_param)
                bond_port = self.set_8023ad_bonded2(slaves, bond_mode)
                self.set_8023ad_dedicated_queues(bond_port, mode)
            except Exception as e:
                check_results.append(e)
                print(traceback.format_exc())
            finally:
                self.bond_inst.close_testpmd()
                time.sleep(2)

        if check_results:
            for result in check_results:
                self.logger.error(result)
            raise VerifyFailure("check_8023ad_dedicated_queues is failed")

    def get_commandline_options(self, agg_mode):
        # get bonding port configuration
        slave_pcis = self.vfs_pci
        # create commandline option format
        bonding_name = "net_bonding0"
        slaves_pci = ["slave=" + pci for pci in slave_pcis]
        p = r"\w+\((\d+)\)"
        mode_id = int(re.match(p, str(MODE_LACP)).group(1))
        bonding_mode = "mode={0}".format(mode_id)
        agg_config = "agg_mode={0}"
        vdev_format = ",".join([bonding_name] + slaves_pci + [bonding_mode, agg_config])
        # command line option
        mode = str(MODE_LACP)
        option = vdev_format.format(agg_mode)
        vdev_option = " --vdev '{0}'".format(option)
        # 802.3ad bond port only create one, it must be the max port number
        bond_port = len(self.sriov_vfs_port)
        return bond_port, vdev_option

    def run_test_pre(self, agg_mode):
        # get bonding port configuration
        bond_port, vdev_option = self.get_commandline_options(agg_mode)
        self.bond_port = bond_port
        # boot up testpmd
        eal_param = self.eal_param + vdev_option
        self.bond_inst.start_testpmd(eal_option=eal_param)
        cur_slaves, cur_agg_mode = self.bond_inst.get_bonding_info(
            bond_port, ["slaves", "agg_mode"]
        )
        if agg_mode != cur_agg_mode:
            fmt = "expected agg mode is [{0}], current agg mode is [{1}]"
            msg = fmt.format(agg_mode, cur_agg_mode)
            self.logger.warning(msg)
        # get forwarding port
        for port_id in range(len(self.sriov_vfs_port)):
            # select a non-slave port as forwarding port to do transmitting
            if str(port_id) not in cur_slaves:
                tx_port_id = port_id
                break
        else:
            tx_port_id = bond_port
        # enable dedicated queue,
        # only ice drive supports vf bonded port to enable dedicated queues
        if "ice" in self.kdriver:
            self.set_8023ad_dedicated_queues(bond_port, "enable")
        self.set_bond_port_ready(tx_port_id, bond_port)
        slaves = [int(slave) for slave in cur_slaves]

        return bond_port, slaves, tx_port_id

    def run_dpdk_functional_pre(self):
        mode = MODE_LACP
        slaves = self.vf_ports[:]
        self.bond_inst.start_testpmd(self.eal_param)
        bond_port = self.run_8023ad_pre(slaves, mode)
        return slaves, bond_port

    def run_dpdk_functional_post(self):
        self.bond_inst.close_testpmd()

    def check_cmd_line_option_status(self, agg_mode, bond_port, slaves):
        mode = str(MODE_LACP)
        msgs = []
        (
            cur_mode,
            cur_slaves,
            cur_active_slaves,
            cur_agg_mode,
        ) = self.bond_inst.get_bonding_info(
            bond_port, ["mode", "slaves", "active_slaves", "agg_mode"]
        )
        # check bonding mode
        if mode != cur_mode:
            fmt = "expected mode is [{0}], current mode is [{1}]"
            msg = fmt.format(mode, cur_mode)
            msgs.append(msg)
        # check bonding 802.3ad agg mode
        if agg_mode != cur_agg_mode:
            fmt = "expected agg mode is [{0}], current agg mode is [{1}]"
            msg = fmt.format(agg_mode, cur_agg_mode)
            msgs.append(msg)
        # check bonded slaves
        _cur_slaves = [int(id) for id in cur_slaves]
        if not _cur_slaves or sorted(slaves) != sorted(_cur_slaves):
            slaves_str = " ".join([str(id) for id in slaves])
            cur_slaves_str = (
                " ".join([str(id) for id in _cur_slaves]) if _cur_slaves else ""
            )
            msg_format = "expected slaves is [{0}], current slaves is [{1}]"
            msg = msg_format.format(slaves_str, cur_slaves_str)
            msgs.append(msg)
        # check active slaves status before ports start
        if cur_active_slaves:
            check_active_slaves = [int(id) for id in cur_active_slaves]
            if sorted(slaves) != sorted(check_active_slaves):
                slaves_str = " ".join([str(id) for id in slaves])
                msg_fmt = (
                    "expected active slaves is [{0}], " "current active slaves is [{1}]"
                )
                msg = msg_fmt.format(slaves_str, cur_active_slaves)
                msgs.append(msg)
        else:
            msg = "active slaves should not be empty"
            self.logger.warning(msg)
            msgs.append(msg)
        # check status after ports start
        self.bond_inst.start_ports()
        # set bonded device to active status
        cur_active_slaves = [
            int(id)
            for id in self.bond_inst.get_bonding_info(bond_port, "active_slaves")
        ]
        if not cur_active_slaves or sorted(slaves) != sorted(cur_active_slaves):
            slaves_str = " ".join([str(id) for id in slaves])
            active_str = (
                " ".join([str(id) for id in cur_active_slaves])
                if cur_active_slaves
                else ""
            )
            msg_fmt = (
                "expected active slaves is [{0}], " "current active slaves is [{1}]"
            )
            msg = msg_fmt.format(slaves_str, active_str)
            msgs.append(msg)
        return msgs

    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run before each test suite
        """
        self.verify("bsdapp" not in self.target, "Bonding not support freebsd")
        # ------------------------------------------------------------
        # link peer resource
        self.dut_ports = self.dut.get_ports()
        required_link = 2
        self.dport_info0 = self.dut.ports_info[self.dut_ports[0]]
        self.dport_ifaces = self.dport_info0["intf"]
        self.verify(len(self.dut_ports) >= required_link, "Insufficient ports")
        # Create a vf for each pf and get all vf info,
        self.dut.restore_interfaces()
        self.create_vfs(pfs_id=self.dut_ports[0:2], vf_num=1)
        self.vf_ports = list(range(len(self.vfs_pci)))
        self.eal_param = str()
        for pci in self.vfs_pci:
            self.eal_param += "-a {} ".format(pci)
        # ------------------------------------------------------------
        # 802.3ad related
        self.bond_port = None
        self.bond_slave = self.dut_ports[0]
        # ----------------------------------------------------------------
        # initialize bonding common methods name
        config = {
            "parent": self,
            "pkt_name": "udp",
            "pkt_size": FRAME_SIZE_64,
            "src_mac": "52:00:00:00:00:03",
            "src_ip": "10.239.129.65",
            "src_port": 61,
            "dst_ip": "10.239.129.88",
            "dst_port": 53,
        }
        self.bond_inst = bonding.PmdBonding(**config)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def create_vfs(self, pfs_id, vf_num):
        self.sriov_vfs_port = []
        self.vfs_pci = []
        self.dut.bind_interfaces_linux(self.kdriver)
        pfs_id = pfs_id if isinstance(pfs_id, list) else [pfs_id]
        for pf_id in pfs_id:
            self.dut.generate_sriov_vfs_by_port(pf_id, vf_num)
            self.sriov_vfs_port += self.dut.ports_info[self.dut_ports[pf_id]][
                "vfs_port"
            ]
            dport_iface = self.dut.ports_info[self.dut_ports[pf_id]]["intf"]
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % (dport_iface), "# "
            )
        for vf in self.sriov_vfs_port:
            self.vfs_pci.append(vf.pci)
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.drivername)
        except Exception as e:
            self.dut.destroy_all_sriov_vfs()
            raise Exception(e)

    def test_basic_behav_startStop(self):
        """
        Test Case : basic behavior start/stop
        """
        msg = ""
        slaves, bond_port = self.run_dpdk_functional_pre()
        try:
            for _ in range(10):
                self.check_bonded_device_start(bond_port)
                self.stop_bonded_device(bond_port)
        except Exception as e:
            print(traceback.format_exc())
            msg = "bonding 8023ad check start/stop failed"
        self.run_dpdk_functional_post()
        if msg:
            raise VerifyFailure(msg)

    def test_basic_behav_mac(self):
        """
        Test Case : basic behavior mac
        """
        msg = ""
        slaves, bond_port = self.run_dpdk_functional_pre()
        try:
            self.bonding_8023ad_check_macs(slaves, bond_port)
            self.check_bonded_device_mac_change(slaves, bond_port)
        except Exception as e:
            msg = "bonding 8023ad check mac failed"
        self.run_dpdk_functional_post()
        if msg:
            raise VerifyFailure(msg)

    def test_basic_behav_upDown(self):
        """
        Test Case : basic behavior link up/down
        """
        msg = ""
        slaves, bond_port = self.run_dpdk_functional_pre()
        try:
            self.check_bonded_device_up_down(bond_port)
        except Exception as e:
            msg = "bonding 8023ad check link up/down failed"
        self.run_dpdk_functional_post()
        if msg:
            raise VerifyFailure(msg)

    def test_basic_behav_promisc_mode(self):
        """
        Test Case : basic behavior promiscuous  mode
        """
        msg = ""
        slaves, bond_port = self.run_dpdk_functional_pre()
        try:
            self.check_bonded_device_promisc_mode(slaves, bond_port)
        except Exception as e:
            msg = "bonding 8023ad check promisc mode failed"
        self.run_dpdk_functional_post()
        if msg:
            raise VerifyFailure(msg)

    def test_command_line_option(self):
        """
        Test Case : command line option
        """
        agg_modes_msgs = []
        for agg_mode in self.AGG_MODES:
            bond_port, cur_slaves, tx_port_id = self.run_test_pre(agg_mode)
            msgs = self.check_cmd_line_option_status(agg_mode, bond_port, cur_slaves)
            if msgs:
                agg_modes_msgs.append((msgs, agg_mode))
            self.bond_inst.close_testpmd()
        if agg_modes_msgs:
            msgs = ""
            for msg, agg_mode in agg_modes_msgs:
                self.logger.warning(msg)
                msgs += "fail to config from command line at {0}  ".format(agg_mode)
            raise VerifyFailure(msgs)

    def test_basic_behav_agg_mode(self):
        """
        Test Case : basic behavior agg mode
        """
        mode = MODE_LACP
        self.check_8023ad_agg_modes(self.vf_ports, mode)

    def test_basic_dedicated_queues(self):
        """
        Test Case : basic behavior dedicated queues
        """
        self.skip_case(
            "ice" in self.kdriver,
            "only ice drive supports vf bonded port to enable dedicated queues",
        )
        mode = MODE_LACP
        self.check_8023ad_dedicated_queues(self.vf_ports, mode)

    def tear_down(self):
        """
        Run after each test case.
        """
        try:
            self.bond_inst.close_testpmd()
        except Exception:
            self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.destroy_all_sriov_vfs()

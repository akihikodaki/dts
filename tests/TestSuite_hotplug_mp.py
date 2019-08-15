# <COPYRIGHT_TAG>

"""
DPDK Test suite.
Hotplug Multi-process Test.
"""

import utils
import time
from test_case import TestCase

test_loop = 2


class TestHotplugMp(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.intf0 = self.dut.ports_info[0]['intf']
        self.pci0 = self.dut.ports_info[0]['pci']
        out = self.dut.build_dpdk_apps("./examples/multi_process/")
        self.verify('Error' not in out, "Compilation failed")
        # Start one new session to run primary process
        self.session_pri = self.dut.new_session()
        # Start two new sessions to run secondary process
        self.session_sec_1 = self.dut.new_session()
        self.session_sec_2 = self.dut.new_session()
        if self.drivername != "":
            self.dut.bind_interfaces_linux(self.kdriver)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def multi_process_setup(self):
        """
        Setup primary process and two secondary processes.
        """
        self.iova_param = ""
        if self.drivername in ["igb_uio"]:
            self.iova_param = "--iova-mode=pa"
        out = self.session_pri.send_expect(
            "./examples/multi_process/hotplug_mp/%s/hotplug_mp %s --proc-type=auto"
            % (self.target, self.iova_param), "example>")
        self.verify("Auto-detected process type: PRIMARY" in out,
                    "Failed to setup primary process!")
        for out in [self.session_sec_1.send_expect(
                        "./examples/multi_process/hotplug_mp/%s/hotplug_mp %s --proc-type=auto"
                        % (self.target, self.iova_param), "example>"),
                    self.session_sec_2.send_expect(
                        "./examples/multi_process/hotplug_mp/%s/hotplug_mp %s --proc-type=auto"
                        % (self.target, self.iova_param), "example>")]:
            self.verify("Auto-detected process type: SECONDARY" in out,
                        "Failed to setup secondary process!")

    def multi_process_quit(self):
        """
        Quit primary process and two secondary processes.
        """
        self.session_sec_1.send_expect("quit", "#")
        self.session_sec_2.send_expect("quit", "#")
        self.session_pri.send_expect("quit", "#")

    def verify_devlist(self, dev="0000:00:00.0", flg_exist=1):
        """
        Check device list to verify if exist the device.
        """
        for out in [self.session_pri.send_expect("list", "example>", 100),
                    self.session_sec_1.send_expect("list", "example>", 100),
                    self.session_sec_2.send_expect("list", "example>", 100)]:
            self.verify("list all etherdev" in out,
                        "Failed to list device on multi-process!")
            if flg_exist == 1:
                self.verify(dev in out, "Fail that don't have the device!")
            if flg_exist == 0:
                self.verify(dev not in out, "Fail that have the device!")

    def attach_detach(self, process="pri", is_dev=1, opt_plug="plugin", flg_loop=0, dev="0000:00:00.0"):
        """
        Attach or detach physical/virtual device from primary/secondary
        process.
        process: define primary or secondary process.
        is_dev: define physical device as 1, virtual device as 0.
        opt_plug: define plug options as below
                  plugin: plug in device
                  plugout: plug out device
                  hotplug: plug in then plug out device from primary or
                           secondary process
                  crossplug: plug in from primary process then plug out from
                             secondary process, or plug in from secondary
                             process then plug out from primary
        flg_loop: define loop test flag
        dev: define physical device PCI "0000:00:00.0" or virtual device
             "net_af_packet"
        """

        if opt_plug == "plugin":
            self.verify_devlist(dev, flg_exist=0)
            for i in range(test_loop):
                if process == "pri":
                    if is_dev == 0:
                        self.session_pri.send_expect(
                            "attach %s,iface=%s"
                            % (dev, self.intf0), "example>", 100)
                    else:
                        self.session_pri.send_expect(
                            "attach %s" % dev, "example>", 100)
                if process == "sec":
                    if is_dev == 0:
                        self.session_sec_1.send_expect(
                            "attach %s,iface=%s"
                            % (dev, self.intf0), "example>", 100)
                    else:
                        self.session_sec_1.send_expect(
                            "attach %s" % dev, "example>", 100)
                if flg_loop == 0:
                    break

            self.verify_devlist(dev, flg_exist=1)

        if opt_plug == "plugout":
            self.verify_devlist(dev, flg_exist=1)
            for i in range(test_loop):
                if process == "pri":
                    self.session_pri.send_expect(
                        "detach %s" % dev, "example>", 100)
                if process == "sec":
                    self.session_sec_1.send_expect(
                        "detach %s" % dev, "example>", 100)
                if flg_loop == 0:
                    break

            self.verify_devlist(dev, flg_exist=0)

    def attach_detach_dev(self, process="pri", opt_plug="plugin", flg_loop=0, dev="0000:00:00.0"):
        """
        Attach or detach physical device from primary/secondary process.
        """
        # Scan port status when example setup, list ports that have been
        #  bound to pmd
        if opt_plug in ["plugin", "hotplug", "crossplug"]:
            self.multi_process_setup()
            self.dut.bind_interfaces_linux(self.drivername)
        elif opt_plug == "plugout":
            self.dut.bind_interfaces_linux(self.drivername)
            self.multi_process_setup()

        if opt_plug in ["plugin", "plugout"]:
            self.attach_detach(process, 1, opt_plug, flg_loop, dev)
        elif opt_plug in ["hotplug", "crossplug"]:
            for i in range(test_loop):
                self.attach_detach(process, 1, "plugin", flg_loop, dev)
                if opt_plug == "crossplug":
                    if process == "pri":
                        cross_proc = "sec"
                    elif process == "sec":
                        cross_proc = "pri"
                    self.attach_detach(cross_proc, 1, "plugout", flg_loop, dev)
                else:
                    self.attach_detach(process, 1, "plugout", flg_loop, dev)

        self.multi_process_quit()
        self.dut.bind_interfaces_linux(self.kdriver)

    def attach_detach_vdev(self, process="pri", opt_plug="plugin", flg_loop=0, dev="net_af_packet"):
        """
        Attach or detach virtual device from primary/secondary process.
        Check port interface is at link up status before hotplug test.
        If link not up, may have below error:
        rte_pmd_init_internals(): net_af_packet: ioctl failed (SIOCGIFINDEX)
        EAL: Driver cannot attach the device (net_af_packet)
        """
        self.dut.send_expect("ifconfig %s up" % self.intf0, "#")
        time.sleep(5)
        out = self.dut.send_expect("ethtool %s" % self.intf0, "#")
        self.verify("Link detected: yes" in out, "Wrong link status")

        self.multi_process_setup()
        for i in range(test_loop):
            self.attach_detach(process, 0, "plugin", flg_loop, dev)
            if opt_plug in ["plugout", "hotplug", "crossplug"]:
                if opt_plug == "crossplug":
                    if process == "pri":
                        cross_proc = "sec"
                    elif process == "sec":
                        cross_proc = "pri"
                    self.attach_detach(cross_proc, 0, "plugout", flg_loop, dev)
                else:
                    self.attach_detach(process, 0, "plugout", flg_loop, dev)

            if opt_plug == "plugin" or opt_plug == "plugout":
                break

        self.multi_process_quit()

    def test_attach_dev_primary(self):
        """
        Attach physical device from primary.
        """
        self.attach_detach_dev("pri", "plugin", 0, self.pci0)

    def test_attach_dev_secondary(self):
        """
        Attach physical device from secondary.
        """
        self.attach_detach_dev("sec", "plugin", 0, self.pci0)

    def test_detach_dev_primary(self):
        """
        Detach physical device from primary.
        """
        self.attach_detach_dev("pri", "plugout", 0, self.pci0)

    def test_detach_dev_secondary(self):
        """
        Detach physical device from secondary.
        """
        self.attach_detach_dev("sec", "plugout", 0, self.pci0)

    def test_attach_detach_dev_primary_loop(self):
        """
        Repeat to attach then detach physical device from primary.
        """
        self.attach_detach_dev("pri", "hotplug", 1, self.pci0)

    def test_attach_detach_dev_secondary_loop(self):
        """
        Repeat to attach then detach physical device from secondary.
        """
        self.attach_detach_dev("sec", "hotplug", 1, self.pci0)

    def test_attach_detach_dev_primary_cross_loop(self):
        """
        Repeat to attach physical device from primary then detach device
        from secondary.
        """
        self.attach_detach_dev("pri", "crossplug", 1, self.pci0)

    def test_attach_detach_dev_secondary_cross_loop(self):
        """
        Repeat to attach physical device from secondary then detach device
        from primary.
        """
        self.attach_detach_dev("sec", "crossplug", 1, self.pci0)

    def test_attach_vdev_primary(self):
        """
        Attach virtual device from primary.
        """
        self.attach_detach_vdev("pri", "plugin", 0, "net_af_packet")

    def test_attach_vdev_secondary(self):
        """
        Attach virtual device from secondary.
        """
        self.attach_detach_vdev("sec", "plugin", 0, "net_af_packet")

    def test_detach_vdev_primary(self):
        """
        Detach virtual device from primary.
        """
        self.attach_detach_vdev("pri", "plugout", 0, "net_af_packet")

    def test_detach_vdev_secondary(self):
        """
        Detach virtual device from secondary.
        """
        self.attach_detach_vdev("sec", "plugout", 0, "net_af_packet")

    def test_attach_detach_vdev_primary_loop(self):
        """
        Repeat to attach then detach virtual device from primary.
        """
        self.attach_detach_vdev("pri", "hotplug", 1, "net_af_packet")

    def test_attach_detach_vdev_secondary_loop(self):
        """
        Repeat to attach then detach virtual device from secondary.
        """
        self.attach_detach_vdev("sec", "hotplug", 1, "net_af_packet")

    def test_attach_detach_vdev_primary_cross_loop(self):
        """
        Repeat to attach virtual device from primary then detach device
        from secondary.
        """
        self.attach_detach_vdev("pri", "crossplug", 1, "net_af_packet")

    def test_attach_detach_vdev_secondary_cross_loop(self):
        """
        Repeat to attach virtual device from secondary then detach device
        from primary.
        """
        self.attach_detach_vdev("sec", "crossplug", 1, "net_af_packet")

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
        self.dut.close_session(self.dut)
        self.dut.kill_all()

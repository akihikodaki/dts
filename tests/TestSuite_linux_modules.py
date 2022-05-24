# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
# Copyright(c) 2018-2019 The University of New Hampshire
#

"""
DPDK Test suite.
Linux Kernel Modules example.
"""
import os
import time

from framework import settings
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

ETHER_HEADER_LEN = 18
IP_HEADER_LEN = 20
ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000


# A class like this is used because doing inheritance normally breaks the test case discovery process
class LinuxModulesHelperMethods:
    driver: str
    dev_interface: str
    additional_eal_options: str

    def set_up_all(self):
        """
        Prerequisite steps for each test suit.
        """
        self.dut_ports = self.dut.get_ports()
        self.pmdout = PmdOutput(self.dut)
        pci_address = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.old_driver = settings.get_nic_driver(pci_address)
        out = self.dut.bind_interfaces_linux(driver=self.driver)
        self.verify("bind failed" not in out, f"Failed to bind {self.driver}")
        self.verify("not loaded" not in out, f"{self.driver} was not loaded")

    def send_scapy_packet(self, port_id: int, packet: str):
        itf = self.tester.get_interface(port_id)

        self.tester.scapy_foreground()
        self.tester.scapy_append(f'sendp({packet}, iface="{itf}")')
        return self.tester.scapy_execute()

    def tear_down(self):
        self.dut.kill_all()

    def run_example_program_in_userspace(self, directory: str, program: str):
        """
        A function to run a given example program as an unprivileged user.
        @param directory: The directory under examples where the app is
        @param program: the name of the binary to run
        """
        out: str = self.dut.build_dpdk_apps(f"$RTE_SDK/examples/{directory}")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")

        program_build_location = f"$RTE_SDK/examples/{directory}/build/{program}"
        program_user_location = f"/tmp/dut/bin/{program}"

        self.dut.send_expect(f"chmod +x {program_build_location}", "# ")
        self.dut.send_expect("mkdir -p /tmp/dut/bin/", "# ")
        user_home_dir = self.dut.send_expect(
            f"cp {program_build_location} {program_user_location}", "# "
        )

        self.dut.alt_session.send_expect(f"su {settings.UNPRIVILEGED_USERNAME}", "# ")
        self.dut.alt_session.send_expect(
            f"{program_user_location} --in-memory {self.additional_eal_options}", "# "
        )
        out: str = self.dut.alt_session.send_expect("echo $?", "# ")
        self.dut.alt_session.send_expect("exit", "# ")  # Return to root session
        self.verify(out.strip() == "0", f"{program} exited in an error state")

    def tx_rx_test_helper(self, pmdout, param="", eal_param=""):
        pmdout.start_testpmd(
            "Default",
            param=f"--port-topology=loop {param}",
            eal_param=f"{eal_param} {self.additional_eal_options}",
        )
        pmdout.execute_cmd("start")
        dut_mac = self.dut.get_mac_address(self.dut_ports[0])
        tester_mac = self.tester.get_mac(self.tester.get_local_port(self.dut_ports[0]))
        iface = self.tester.get_interface(self.dut_ports[0])
        pcap_path: str = f"/tmp/tester/test-{self.driver}.pcap"
        self.tester.send_expect(
            f"tcpdump -i {iface} -w /tmp/tester/test-{self.driver}.pcap ether src {tester_mac} &",
            "# ",
        )
        self.tester.send_expect(f"TCPDUMP_PID=$!", "# ")
        self.send_scapy_packet(
            self.dut_ports[0],
            f"[Ether(dst='{dut_mac}', src='{tester_mac}')/IP()/TCP()/('a') for i in range(20)]",
        )
        time.sleep(0.1)
        self.tester.send_expect("kill -SIGINT $TCPDUMP_PID", "# ")
        os.system(f"mkdir -p {settings.FOLDERS['Output']}/tmp/pcap/")
        self.tester.session.copy_file_from(
            pcap_path, dst=os.path.join(settings.FOLDERS["Output"], "tmp/pcap/")
        )
        out: str = self.tester.send_expect(
            f"tcpdump -r /tmp/tester/test-{self.driver}.pcap", "# "
        )
        self.verify(
            len(out.splitlines()) >= 20, "Not all packets were received by the tester."
        )
        pmdout.quit()

    #
    #
    #
    # Test cases.
    #

    def tear_down_all(self):
        """
        When the case of this test suite finished, the environment should
        clear up.
        """
        self.dut.bind_interfaces_linux(driver=self.old_driver)
        self.dut.kill_all()

    def test_tx_rx(self):
        """
        Performs the testing that needs to be done as root.
        @param driver: The driver to test
        """
        self.tx_rx_test_helper(self.pmdout)

    def test_helloworld(self):
        self.run_example_program_in_userspace("helloworld", "helloworld-shared")

    def test_tx_rx_userspace(self):
        app_path = self.dut.apps_name["test-pmd"]
        self.dut.send_expect(f"chmod +rx {app_path}", "#")
        path = self.dut.send_expect("pwd", "#")
        self.dut.alt_session.send_expect(f"su {settings.UNPRIVILEGED_USERNAME}", "#")
        self.dut.alt_session.send_expect(f"cd {path}", "#")
        self.dut.send_expect(
            f"setfacl -m u:{settings.UNPRIVILEGED_USERNAME}:rwx {self.dev_interface}",
            "#",
        )
        self.tx_rx_test_helper(
            PmdOutput(self.dut, session=self.dut.alt_session), eal_param="--in-memory"
        )
        self.dut.alt_session.send_expect(f"exit", "#")


class TestVfio(LinuxModulesHelperMethods, TestCase):
    driver = "vfio-pci"
    dev_interface = "/dev/vfio/*"
    additional_eal_options = ""


class TestIgbuio(LinuxModulesHelperMethods, TestCase):
    driver = "igb_uio"
    dev_interface = "/dev/uio*"
    additional_eal_options = "--iova-mode va"


class TestUioPciGeneric(LinuxModulesHelperMethods, TestCase):
    driver = "uio_pci_generic"
    dev_interface = "/dev/uio*"
    additional_eal_options = ""

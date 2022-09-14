# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2021-2022 Intel Corporation
#

"""
DPDK Test suite.
PMD power management test plan.
"""

import re
import time

from framework.test_case import TestCase
from framework.utils import create_mask as dts_create_mask


class TestPowerPMD(TestCase):
    def configure_vfio_with_no_iommu(self):
        # configure VFIO to be used without IOMMU
        # http://doc.dpdk.org/guides/linux_gsg/linux_drivers.html?#vfio-no-iommu-mode
        self.dut.send_expect("modprobe vfio-pci", "# ")
        self.dut.send_expect(
            "echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode", "# "
        )

    def config_pql_gen(self, lcores, offset):
        # generate config string
        #    --config(port,queue,lcore)[,(port,queue,lcore)]
        #        determines which queues from which ports are mapped to which cores.
        arg = ",".join((f"(0,{i},{i + offset})" for i in range(lcores - offset)))
        return f'--config="{arg}"'

    def verify_waitpkg_support(self):
        out = self.dut.send_expect("grep waitpkg /proc/cpuinfo", "# ", 10)
        self.verify(
            "waitpkg" in out,
            "This test requires that the platform MUST support WAITPKG instruction set.",
        )
        self.logger.info(
            'The "waitpkg" capability is NOT available on the platform - OK'
        )

    def reset_pstate(self):
        # Reset all pstate min/max frequency assignments for all cores:
        # This can be done by overwriting lowest and highest frequencies in the CPU
        # scaling driver:
        #   for d in /sys/bus/cpu/devices/cpu*/cpufreq/
        #   do
        #       cat $d/cpuinfo_min_freq > $d/scaling_min_freq
        #       cat $d/cpuinfo_max_freq > $d/scaling_max_freq
        #   done
        self.logger.info("reseting all pstate min/max frequency ..")
        cmd = "for d in /sys/bus/cpu/devices/cpu*/cpufreq/; do"
        cmd = cmd + " cat ${d}/cpuinfo_min_freq > ${d}/scaling_min_freq;"
        cmd = cmd + " cat ${d}/cpuinfo_max_freq > ${d}/scaling_max_freq; done"
        self.dut.send_expect(cmd, "# ")

    def start_l3fwd(self, mode):
        if mode in ["baseline", "scale", "pause", "monitor"]:
            l3fwd_cmd = f"{self.l3fwd_path} -l 0-{self.max_lcore} -- --pmd-mgmt={mode} -P -p 0x1 {self.config_0}"
        else:
            l3fwd_cmd = f"{self.l3fwd_path} -l 0-{self.max_lcore} -- --{mode} -P -p 0x1 {self.config_1}"

        self.l3fwd_is_on = True
        self.l3fwd_session.send_expect(
            l3fwd_cmd, f"L3FWD_POWER:  -- lcoreid={self.max_lcore} ", 20
        )
        time.sleep(3)

    def stop_l3fwd(self):
        if self.l3fwd_is_on:
            self.l3fwd_session.send_expect("^c", "# ", 20)
            self.l3fwd_is_on = False

    def get_pkgwatt(self):
        out = self.dut.send_expect(
            "turbostat --show PkgWatt --Summary --num_iterations 1 2>/dev/null | tail -1",
            "# ",
        )
        return float(out)

    def get_max_and_ref_freq(self):
        cpu0_min_freq = self.dut.send_expect(
            "cat /sys/bus/cpu/devices/cpu0/cpufreq/cpuinfo_min_freq", "# "
        )
        cpu_min_mhz = int(cpu0_min_freq) // 1000
        out = self.dut.send_expect(
            'turbostat --quiet --show "Core,Bzy_MHz" --num_iterations 1', "# "
        )
        nums = re.findall(r"\n\d+\s+(\d+)", out)
        min_mhz, max_mhz = min(nums), max(nums)

        self.logger.info(f'the lowest "cpuinfo_min_freq" is {cpu_min_mhz} MHz')
        self.logger.info(
            f"cores are running at average frequency between {min_mhz} MHz and {max_mhz} MHz"
        )
        return int(max_mhz), cpu_min_mhz

    def verify_turbostat(self):
        # turbostat tool must be installed on the DUT
        # it also must report average core frequency and platform power consumption
        # "turbostat -l" must have "PkgWatt", "Core" (or "CPU"), and "Bzy_MHz" columns
        out = self.dut.send_expect("turbostat -h", "# ")
        self.verify(
            "Usage:" in out,
            '"turbostat" tool was not found. Please install "linux-tools-common" and restart the test.',
        )
        self.logger.info('The "turbostat" tool is available.')

        # check if turbostat reports "PkgWatt", "Core" and "Bzy_MHz" columns
        out = self.dut.send_expect("turbostat --list", "# ")
        for column in ["PkgWatt", "Core", "Bzy_MHz"]:
            self.verify(
                f",{column}," in f",{out},",
                f'"turbostat" does not report "{column}" column. Please check the system configuration.',
            )
            self.logger.info(f'The "turbostat" reports "{column}" column - OK.')

    def verify_pkgwatt_change(self, mode):
        # Test Case 2, 3 and 4: Test PMD power management in "pause"/"monitor" mode
        #
        # Step 1. Launch l3fwd-power in "baseline" mode
        # Step 2. While Step 1 is in progress, run turbostat to determine power consumption
        # Step 3. Relaunch l3fwd-power and enable "pause"/"monitor" PMD power management mode
        # Step 4. While Step 3 is in progress, measure the power consumption again
        # Pass Criteria: PkgWatt number has measurably (e.g. >5%) decreased from the baseline.
        self.start_l3fwd("baseline")
        pkgwatt_baseline = self.get_pkgwatt()
        self.stop_l3fwd()

        self.start_l3fwd(mode)
        pkgwatt_current = self.get_pkgwatt()

        change = pkgwatt_current / pkgwatt_baseline * 100
        summ = f'PkgWatt: {change:.2f}% change from {pkgwatt_baseline} W in "baseline" mode to {pkgwatt_current} W in "{mode}" mode.'
        self.logger.info(summ)
        self.logger.info(
            "Pass Criteria: PkgWatt number has measurably (e.g. >5%) decreased from the baseline."
        )
        self.verify(
            change <= 95, "PkgWatt did not drop at least 5% below the baseline value."
        )

    def set_up_all(self):
        """
        Run once at the start of test suite.
        """
        self.verify_turbostat()
        self.configure_vfio_with_no_iommu()

        # build the 'dpdk-l3fwd-power' tool
        out = self.dut.build_dpdk_apps("examples/l3fwd-power")
        self.verify("Error" not in out, ' "dpdk-l3fwd-power" build error')
        self.l3fwd_path = self.dut.apps_name["l3fwd-power"]
        self.logger.debug("l3fwd-power tool path: {}".format(self.l3fwd_path))
        self.l3fwd_is_on = False
        self.l3fwd_session = self.dut.new_session("l3fwd")

        # determine number of logical cores
        self.max_lcore = len(self.dut.cores)
        self.lcores = self.max_lcore + 1
        self.logger.debug(f"lcores: {self.lcores}")

        # generate two config strings, one including the main lcore 0 and one without
        #    --config(port,queue,lcore)[,(port,queue,lcore)]
        #        determines which queues from which ports are mapped to which cores.
        self.config_0 = self.config_pql_gen(self.lcores, 0)
        self.config_1 = self.config_pql_gen(self.lcores, 1)
        self.logger.debug('reff cfg: --config="(0,0,0),(0,1,1),(0,2,2),..."')
        self.logger.debug(f"config_0: {self.config_0}")
        self.logger.debug('reff cfg: --config="(0,0,1),(0,1,2),(0,2,3),..."')
        self.logger.debug(f"config_1: {self.config_1}")

    def set_up(self):
        """
        Run before each test case.
        """
        self.reset_pstate()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.stop_l3fwd()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.reset_pstate()
        self.dut.close_session("l3fwd")

    def test_scale_mode(self):
        # Test Case 1: Test PMD power management in scale mode
        # Step 1. Reset all pstate min/max frequency assignments for all cores
        # Step 2. Launch l3fwd-power and enable "scale" PMD power management mode
        # Step 3. Ensure all cores operate at lowest frequency available.
        #     To find lowest frequency, read the cpuinfo_min_freq value for core 0 from sysfs:
        #     # find lowest frequency available, in KHz
        #     Ex: cat /sys/bus/cpu/devices/cpu0/cpufreq/cpuinfo_min_freq
        #     1200000
        #     Then, while running `dpdk-l3fwd-power` as described in Step 2, also run
        #     turbostat and ensure that all forwarding cores are running at lowest frequency
        #     available for those cores:
        #     # assume min frequency is 1.2GHz
        #     turbostat -i 1 -n 1 -s "Core,Bzy_MHz"
        #     CPU     Bzy_Mhz
        #     -       1200
        #     0       1200
        #     1       1200
        #     2       1200
        #     3       1200
        #     ...
        # Step 4. Repeat Step 1 to reset the pstate scaling settings.
        # Pass Criteria: average frequency on all cores is roughly equal to minimum
        # frequency (there is some variance to be expected, values within 100MHz are acceptable)
        self.start_l3fwd("scale")
        max_mhz, ref_mhz = self.get_max_and_ref_freq()
        self.logger.info(
            "Pass Criteria: average frequency on all cores is roughly equal to minimum frequency"
        )
        self.logger.info(
            "               (there is some variance to be expected, values within 100 MHz are acceptable)"
        )
        err_msg = f"found frequency {max_mhz} MHz which is over 100 MHz higher than aceptable minimum."
        self.verify(abs(max_mhz - ref_mhz) <= 100, err_msg)

    def test_pause_mode_waitpkg(self):
        # Test Case 3: Test PMD power management in "pause" mode with WAITPKG
        # Requirement: this test requires that the platform must support WAITPKG instruction set
        self.verify_waitpkg_support()
        self.verify_pkgwatt_change("pause")

    def test_monitor_mode_waitpkg(self):
        # Test Case 4: Test PMD power management in "monitor" mode
        # Requirement: this test requires that the platform must support WAITPKG instruction set
        self.verify_waitpkg_support()
        self.verify_pkgwatt_change("monitor")

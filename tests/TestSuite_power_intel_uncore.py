# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2023 Intel Corporation
#

"""
DPDK Test suite.
Power Intel Uncore test suite.
"""

import os
import traceback

from framework.exception import VerifyFailure
from framework.test_case import TestCase

BASE_CLOCK = 100000


class TestPowerIntelUncore(TestCase):
    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = (
            "/root" + self.dut.base_dir[1:]
            if self.dut.base_dir.startswith("~")
            else self.dut.base_dir
        )
        return target_dir

    def prepare_binary(self, name):
        example_dir = "examples/" + name
        self.dut.build_dpdk_apps("./" + example_dir)
        return os.path.join(self.target_dir, self.dut.apps_name[os.path.basename(name)])

    def init_l3fwd_power(self):
        self.l3fwd_power = self.prepare_binary("l3fwd-power")

    def start_l3fwd_power(self, option):
        l3fwd_cmd = f'-c 0x6 -n 1 -- -p 0x1 -P --config="(0,0,2)" {option}'
        prompt = "L3FWD_POWER: lcore 1 has nothing to do"
        # timeout of 120 seconds as it takes that long for l3fwd-power to output its final command
        self.l3fwd_session.send_expect(
            " ".join([self.l3fwd_power, l3fwd_cmd]), prompt, 120
        )
        self.is_l3fwd_on = True

    def close_l3fwd_power(self):
        if not self.is_l3fwd_on:
            return
        cmd = "^C"
        self.l3fwd_session.send_expect(cmd, "#")

    def preset_test_environment(self):
        self.is_l3fwd_on = None
        self.init_l3fwd_power()
        # initialise seperate session for l3fwd, so that while l3fwd-power is ran rdmsr can check values
        self.l3fwd_session = self.dut.new_session("l3fwd")

    def validate_power_uncore_values_equal(self, target_value, current_value):
        if target_value != current_value:
            msg = "l3fwd-power failed to set the correct value for uncore"
            raise VerifyFailure(msg)

    def get_current_uncore_max(self):
        current_uncore_max_cmd = "rdmsr 0x620 -f 8:0 -d"
        current_uncore_max = int(self.dut.send_expect(current_uncore_max_cmd, "#"))
        return current_uncore_max * BASE_CLOCK

    def get_current_uncore_min(self):
        current_uncore_min_cmd = "rdmsr 0x620 -f 16:8 -d"
        current_uncore_min = int(self.dut.send_expect(current_uncore_min_cmd, "#"))
        return current_uncore_min * BASE_CLOCK

    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # prerequisites
        cpu_attr = r"/sys/devices/system/cpu/intel_uncore_frequency"
        cmd = "ls {0}".format(cpu_attr)
        self.dut.send_expect(cmd, "#")
        self.dut.send_expect("modprobe msr", "#")
        self.dut.send_expect("modprobe intel-uncore-frequency", "#")

        # build the 'dpdk-l3fwd-power' tool
        out = self.dut.build_dpdk_apps("examples/l3fwd-power")
        self.verify("Error" not in out, ' "dpdk-l3fwd-power" build error')
        self.l3fwd_path = self.dut.apps_name["l3fwd-power"]
        self.logger.debug("l3fwd-power tool path: {}".format(self.l3fwd_path))
        self.l3fwd_is_on = False
        self.l3fwd_session = self.dut.new_session("l3fwd")

        # prepare testing environment
        self.preset_test_environment()

    def validate_power_uncore_freq_max(self):
        """
        Check that setting max uncore frequency, sets to correct value without errors
        """
        # Make sure that current uncore max is not equal to max possible uncore freq
        current_uncore_max = self.get_current_uncore_max()
        # can just check pkg 0 die 0 as it will be the same for each pkg
        initial_uncore_max_cmd = "cat /sys/devices/system/cpu/intel_uncore_frequency/package_00_die_00/initial_max_freq_khz"
        initial_uncore_max = int(self.dut.send_expect(initial_uncore_max_cmd, "#"))

        if current_uncore_max == initial_uncore_max:
            # reducing freq by BASE_CLOCK is easiest and safest freq value to set
            lower_uncore_max = current_uncore_max - BASE_CLOCK
            intel_uncore_dir_cmd = (
                'os.listdir("/sys/devices/system/cpu/intel_uncore_frequency")'
            )
            intel_uncore_dir = self.dut.send_expect(intel_uncore_dir_cmd, "#")
            for uncore_die_sysfs_file in intel_uncore_dir:
                # check if current path is a file
                if os.path.isfile(
                    os.path.join(intel_uncore_dir, uncore_die_sysfs_file)
                ):
                    set_freq_cmd = f"echo {lower_uncore_max} > /sys/devices/system/cpu/intel_uncore_frequency/{uncore_die_sysfs_file}/max_freq_khz"
                    self.dut.send_expect(set_freq_cmd, "#")

        except_content = None
        try:
            self.start_l3fwd_power("-U")
            current_uncore_max = self.get_current_uncore_max()
            self.validate_power_uncore_values_equal(
                initial_uncore_max, current_uncore_max
            )
            current_uncore_min = self.get_current_uncore_min()
            self.validate_power_uncore_values_equal(
                initial_uncore_max, current_uncore_min
            )
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            msg = "test validate_power_uncore_freq_max successful !!!"
            self.logger.info(msg)

    def validate_power_uncore_freq_min(self):
        """
        Check that setting min uncore frequency, sets to correct value without errors
        """
        # Make sure that current uncore min is not equal to min possible uncore freq
        current_uncore_min = self.get_current_uncore_min()
        # can just check pkg 0 die 0 as it will be the same for each pkg
        initial_uncore_min_cmd = "cat /sys/devices/system/cpu/intel_uncore_frequency/package_00_die_00/initial_min_freq_khz"
        initial_uncore_min = int(self.dut.send_expect(initial_uncore_min_cmd, "#"))

        if current_uncore_min == initial_uncore_min:
            # reducing freq by BASE_CLOCK is easiest and safest freq value to set
            higher_uncore_min = current_uncore_min + BASE_CLOCK
            intel_uncore_dir_cmd = (
                'os.listdir("/sys/devices/system/cpu/intel_uncore_frequency")'
            )
            intel_uncore_dir = self.dut.send_expect(intel_uncore_dir_cmd, "#")
            for uncore_die_sysfs_file in intel_uncore_dir:
                # check if current path is a file
                if os.path.isfile(
                    os.path.join(intel_uncore_dir, uncore_die_sysfs_file)
                ):
                    set_freq_cmd = f"echo {higher_uncore_min} > /sys/devices/system/cpu/intel_uncore_frequency/{uncore_die_sysfs_file}/min_freq_khz"
                    self.dut.send_expect(set_freq_cmd, "#")

        except_content = None
        try:
            self.start_l3fwd_power("-u")
            current_uncore_min = self.get_current_uncore_min()
            self.validate_power_uncore_values_equal(
                initial_uncore_min, current_uncore_min
            )
            current_uncore_max = self.get_current_uncore_max()
            self.validate_power_uncore_values_equal(
                initial_uncore_min, current_uncore_max
            )
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            msg = "test validate_power_uncore_freq_min successful !!!"
            self.logger.info(msg)

    def validate_power_uncore_freq_idx(self):
        """
        Check that setting idx uncore frequency, sets to correct value without errors
        """
        # Make sure that current uncore idx is not equal to idx possible uncore freq
        current_uncore_max = self.get_current_uncore_max()
        # can just check pkg 0 die 0 as it will be the same for each pkg
        initial_uncore_idx_cmd = "cat /sys/devices/system/cpu/intel_uncore_frequency/package_00_die_00/initial_max_freq_khz"
        # 200000 is taken from initial_uncore_idx as the index selected is 2 steps below max
        target_uncore_idx = (
            int(self.dut.send_expect(initial_uncore_idx_cmd, "#")) - 200000
        )

        if current_uncore_max == target_uncore_idx:
            # increasing freq by BASE_CLOCK is easiest and safest freq value to set
            higher_uncore_idx = current_uncore_max + BASE_CLOCK
            intel_uncore_dir_cmd = (
                'os.listdir("/sys/devices/system/cpu/intel_uncore_frequency")'
            )
            intel_uncore_dir = self.dut.send_expect(intel_uncore_dir_cmd, "#")
            for uncore_die_sysfs_file in intel_uncore_dir:
                # check if current path is a file
                if os.path.isfile(
                    os.path.join(intel_uncore_dir, uncore_die_sysfs_file)
                ):
                    set_freq_cmd = f"echo {higher_uncore_idx} > /sys/devices/system/cpu/intel_uncore_frequency/{uncore_die_sysfs_file}/max_freq_khz"
                    self.dut.send_expect(set_freq_cmd, "#")

        except_content = None
        try:
            self.start_l3fwd_power("-i 2")
            current_uncore_max = self.get_current_uncore_max()
            self.validate_power_uncore_values_equal(
                target_uncore_idx, current_uncore_max
            )
            current_uncore_min = self.get_current_uncore_min()
            self.validate_power_uncore_values_equal(
                target_uncore_idx, current_uncore_min
            )
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            msg = "test validate_power_uncore_freq_idx successful !!!"
            self.logger.info(msg)

    def validate_power_uncore_exit(self):
        except_content = None
        try:
            # any command works, output doesn't matter
            self.start_l3fwd_power("-U")
            if not self.is_l3fwd_on:
                return
            # final line when exiting l3fwd-power with this setup and there are no issues
            prompt = "mode and been set back to the original"
            self.l3fwd_session.send_expect("^C", prompt)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            msg = "test validate_power_uncore_exit successful !!!"
            self.logger.info(msg)

    def tear_down_all(self):
        """Run after each test suite."""
        pass

    def set_up(self):
        """Run before each test case."""
        pass

    def tear_down(self):
        """Run after each test case."""
        self.dut.kill_all()

    def test_validate_power_uncore_freq_max(self):
        self.validate_power_uncore_freq_max()

    def test_validate_power_uncore_freq_min(self):
        self.validate_power_uncore_freq_min()

    def test_validate_power_uncore_freq_idx(self):
        self.validate_power_uncore_freq_idx()

    def test_validate_power_uncore_exit(self):
        self.validate_power_uncore_exit()

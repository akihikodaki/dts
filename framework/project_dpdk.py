# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

import os
import re

from .crb import Crb
from .dut import Dut
from .logger import getLogger
from .settings import (
    CONFIG_ROOT_PATH,
    DPDK_RXMODE_SETTING,
    DRIVERS,
    HOST_DRIVER_MODE_SETTING,
    HOST_DRIVER_SETTING,
    HOST_SHARED_LIB_PATH,
    HOST_SHARED_LIB_SETTING,
    NICS,
    accepted_nic,
    load_global_setting,
    save_global_setting,
)
from .ssh_connection import SSHConnection
from .tester import Tester
from .utils import RED


class DPDKdut(Dut):

    """
    DPDK project class for DUT. DTS will call set_target function to setup
    build, memory and kernel module.
    """

    def __init__(self, crb, serializer, dut_id=0, name=None, alt_session=True):
        super(DPDKdut, self).__init__(crb, serializer, dut_id, name, alt_session)
        self.testpmd = None

    def set_target(self, target, bind_dev=True):
        """
        Set env variable, these have to be setup all the time. Some tests
        need to compile example apps by themselves and will fail otherwise.
        Set hugepage on DUT and install modules required by DPDK.
        Configure default ixgbe PMD function.
        """
        self.target = target

        self.set_toolchain(target)

        # set env variable
        self.set_env_variable()

        self.set_rxtx_mode()

        self.apps_name = self.apps_name_conf["meson"]
        # use the dut target directory instead of 'target' string in app name
        for app in self.apps_name:
            cur_app_path = self.apps_name[app].replace("target", self.target)
            self.apps_name[app] = cur_app_path + " "

        if not self.skip_setup:
            self.build_install_dpdk(target)

        self.setup_memory()

        drivername = load_global_setting(HOST_DRIVER_SETTING)
        drivermode = load_global_setting(HOST_DRIVER_MODE_SETTING)
        self.setup_modules(target, drivername, drivermode)

        if bind_dev and self.get_os_type() == "linux":
            self.bind_interfaces_linux(drivername)
        self.extra_nic_setup()

    def set_env_variable(self):
        # These have to be setup all the time. Some tests need to compile
        # example apps by themselves and will fail otherwise.
        self.send_expect("export RTE_TARGET=" + self.target, "#")
        self.send_expect("export RTE_SDK=`pwd`", "#")

    def setup_modules(self, target, drivername, drivermode):
        """
        Install DPDK required kernel module on DUT.
        """
        setup_modules = getattr(self, "setup_modules_%s" % self.get_os_type())
        setup_modules(target, drivername, drivermode)

    def setup_modules_linux(self, target, drivername, drivermode):
        if drivername == "vfio-pci":
            if not self.is_container:
                self.send_expect("rmmod vfio_pci", "#")
                self.send_expect("rmmod vfio_iommu_type1", "#")
                self.send_expect("rmmod vfio", "#")
                self.send_expect("modprobe vfio", "#")
                self.send_expect("modprobe vfio-pci", "#")
            if drivermode == "noiommu":
                self.send_expect(
                    "echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode",
                    "#",
                )
            out = self.send_expect("ls /sys/module|grep vfio_pci", "#")
            assert "vfio_pci" in out, "load vfio_pci failed"

        elif drivername == "uio_pci_generic":
            self.send_expect("modprobe uio", "#", 70)
            self.send_expect("modprobe uio_pci_generic", "#", 70)
            out = self.send_expect("lsmod | grep uio_pci_generic", "#")
            assert "uio_pci_generic" in out, "Failed to setup uio_pci_generic"

        elif drivername == "mlx5_core":
            pass

        elif drivername == "igb_uio":
            self.send_expect("modprobe uio", "#", 70)
            out = self.send_expect("lsmod | grep igb_uio", "#")
            if "igb_uio" in out:
                self.send_expect("rmmod -f igb_uio", "#", 70)
            self.send_expect("insmod ./" + target + "/kmod/igb_uio.ko", "#", 60)

            out = self.send_expect("lsmod | grep igb_uio", "#")
            assert "igb_uio" in out, "Failed to insmod igb_uio"

        else:
            pass

    def setup_modules_freebsd(self, target, drivername, drivermode):
        """
        Install DPDK required Freebsd kernel module on DUT.
        """
        binding_list = ""

        for (pci_bus, pci_id) in self.pci_devices_info:
            if accepted_nic(pci_id):
                binding_list += "%s," % (pci_bus)

        self.send_expect("kldunload if_ixgbe.ko", "#")
        self.send_expect('kenv hw.nic_uio.bdfs="%s"' % binding_list[:-1], "# ")
        self.send_expect("kldload ./%s/kmod/nic_uio.ko" % target, "#", 20)
        out = self.send_expect("kldstat", "#")
        assert "nic_uio" in out, "Failed to insmod nic_uio"

    def restore_modules(self):
        """
        Restore DPDK kernel module on DUT.
        """
        restore_modules = getattr(self, "restore_modules_%s" % self.get_os_type())
        restore_modules()

    def restore_modules_linux(self):
        """
        Restore DPDK Linux kernel module on DUT.
        """
        drivername = load_global_setting(HOST_DRIVER_SETTING)
        if drivername == "vfio-pci":
            drivermode = load_global_setting(HOST_DRIVER_MODE_SETTING)
            if drivermode == "noiommu":
                self.send_expect(
                    "echo 0 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode",
                    "#",
                    70,
                )

    def restore_modules_freebsd(self):
        """
        Restore DPDK Freebsd kernel module on DUT.
        """
        pass

    def set_rxtx_mode(self):
        """
        Set default RX/TX PMD function,
        the rx mode scalar/full/novector are supported dynamically since DPDK 20.11,
        Rx mode avx512 is only supported in DPDK 20.11 and later version.
        """

        mode = load_global_setting(DPDK_RXMODE_SETTING)
        if mode == "avx512":
            out = self.send_expect("lscpu | grep avx512", "#")
            if "avx512f" not in out or "no-avx512f" in out:
                self.logger.warning(
                    RED("*********The DUT CPU do not support AVX512 test!!!********")
                )
                self.logger.warning(
                    RED("*********Now set the rx_mode to default!!!**********")
                )
                save_global_setting(DPDK_RXMODE_SETTING, "default")

    def set_package(self, pkg_name="", patch_list=[]):
        self.package = pkg_name
        self.patches = patch_list

    def set_build_options(self, config_parms, config_file=""):
        self.set_build_options_meson(config_parms, config_file)

    def set_build_options_meson(self, config_parms, config_file=""):
        """
        Set dpdk build options of meson
        """
        if len(config_parms) == 0:
            return
        if config_file == "":
            config_file = "config/rte_config.h"

        for key in config_parms.keys():
            value = config_parms[key]
            if value == "n":
                def_str = "#undef" + " " + key
            else:
                if isinstance(value, int):
                    def_str = "#define %s %d" % (key, value)
                elif value == "" or value == "y":
                    def_str = "#define %s %d" % (key, 1)
                else:
                    value = '\\"%s\\"' % value
                    def_str = "#define %s %s" % (key, value)

            # delete the marco define in the config file
            self.send_expect("sed -i '/%s/d' %s" % (key, config_file), "# ")
            self.send_expect("sed -i '$a\%s' %s" % (def_str, config_file), "# ")

    def build_install_dpdk(self, target, extra_options=""):
        """
        Build DPDK source code with specified target.
        """
        use_shared_lib = load_global_setting(HOST_SHARED_LIB_SETTING)
        if use_shared_lib == "true" and "Virt" not in str(self):
            extra_options += " -Dc_args=-DRTE_BUILD_SHARED_LIB"
        if self.get_os_type() == "linux":
            self.build_install_dpdk_linux_meson(target, extra_options)
        elif self.get_os_type() == "freebsd":
            self.build_install_dpdk_freebsd_meson(target, extra_options)

    def build_install_dpdk_linux_meson(self, target, extra_options):
        """
        Build DPDK source code on linux use meson
        """
        build_time = 1800
        target_info = target.split("-")
        arch = target_info[0]
        machine = target_info[1]
        execenv = target_info[2]
        toolchain = target_info[3]

        default_library = "static"
        use_shared_lib = load_global_setting(HOST_SHARED_LIB_SETTING)
        if use_shared_lib == "true" and "Virt" not in str(self):
            default_library = "shared"
        if arch == "i686":
            # find the pkg-config path and set the PKG_CONFIG_LIBDIR environmental variable to point it
            out = self.send_expect("find /usr -type d -name pkgconfig", "# ")
            pkg_path = ""
            default_cflags = self.send_expect("echo $CFLAGS", "# ")
            default_pkg_config = self.send_expect("echo $PKG_CONFIG_LIBDIR", "# ")
            res_path = out.split("\r\n")
            for cur_path in res_path:
                if "i386" in cur_path:
                    pkg_path = cur_path
                    break
            assert (
                pkg_path != ""
            ), "please make sure you env have the i386 pkg-config path"

            self.send_expect("export CFLAGS=-m32", "# ")
            self.send_expect("export PKG_CONFIG_LIBDIR=%s" % pkg_path, "# ")

        self.send_expect("rm -rf " + target, "#")
        if self.is_container:
            meson_build_cmd = (
                "CC=%s meson -Denable_kmods=False -Dlibdir=lib %s --default-library=%s %s"
                % (toolchain, extra_options, default_library, target)
            )
        else:
            meson_build_cmd = (
                "CC=%s meson -Denable_kmods=True -Dlibdir=lib %s --default-library=%s %s"
                % (toolchain, extra_options, default_library, target)
            )
        out = self.send_expect(meson_build_cmd, "[~|~\]]# ", build_time)
        assert "FAILED" not in out, "meson setup failed ..."

        out = self.send_expect("ninja -C %s" % target, "[~|~\]]# ", build_time)
        assert "FAILED" not in out, "ninja complie failed ..."

        # copy kmod file to the folder same as make
        if not self.is_container:
            out = self.send_expect(
                "find ./%s/kernel/ -name *.ko" % target, "# ", verify=True
            )
            self.send_expect("mkdir -p %s/kmod" % target, "# ")
            if not isinstance(out, int) and len(out) > 0:
                kmod = out.split("\r\n")
                for mod in kmod:
                    self.send_expect("cp %s %s/kmod/" % (mod, target), "# ")

    def build_install_dpdk_freebsd_meson(self, target, extra_options):
        # meson build same as linux
        self.build_install_dpdk_linux_meson(target, extra_options)

        # the uio name different with linux, find the nic_uio
        out = self.send_expect(
            "find ./%s/kernel/ -name nic_uio" % target, "# ", verify=True
        )
        self.send_expect("mkdir -p %s/kmod" % target, "# ")
        if not isinstance(out, int) and len(out) > 0:
            self.send_expect("cp %s %s/kmod/" % (out, target), "# ")

    def prepare_package(self):
        if not self.skip_setup:
            session_info = None
            # if snapshot_load_side=dut, will copy the dpdk tar from dut side
            # and will judge whether the path of tar is existed on dut
            if self.crb["snapshot_load_side"] == "dut":
                if not os.path.isabs(self.package):
                    raise ValueError(
                        "As snapshot_load_side=dut, will copy dpdk.tar "
                        "from dut, please specify a abs path use params "
                        "--snapshot when run dts"
                    )
                # if ':' in session, this is vm dut, use the dut session
                if ":" in self.session.name:
                    session_info = self.host_session
                else:
                    session_info = self.alt_session
                out = session_info.send_expect("ls -F %s" % self.package, "# ")
                assert out == self.package, "Invalid package"
            else:
                assert os.path.isfile(self.package) is True, "Invalid package"

            p_dir, _ = os.path.split(self.base_dir)
            # ToDo: make this configurable
            dst_dir = "/tmp/"

            out = self.send_expect("ls -d %s" % p_dir, "# ", verify=True)
            if out == 2:
                self.send_expect("mkdir -p %s" % p_dir, "# ")

            out = self.send_expect(
                "ls %s && cd %s" % (dst_dir, p_dir), "#", verify=True
            )
            if out == -1:
                raise ValueError(
                    "Directory %s or %s does not exist,"
                    "please check params -d" % (p_dir, dst_dir)
                )
            self.session.copy_file_to(self.package, dst_dir, crb_session=session_info)

            # put patches to p_dir/patches/
            if self.patches is not None:
                for p in self.patches:
                    self.session.copy_file_to("dep/" + p, dst_dir)

            # copy QMP file to dut
            if "virtdut" not in self.session.name:
                out = self.send_expect("ls -d ~/QMP", "# ", verify=True)
                if isinstance(out, int):
                    self.send_expect("mkdir -p ~/QMP", "# ")
                self.session.copy_file_to("dep/QMP/qemu-ga-client", "~/QMP/")
                self.session.copy_file_to("dep/QMP/qmp.py", "~/QMP/")
            self.kill_all()

            # enable core dump
            self.send_expect("ulimit -c unlimited", "#")

            # unpack the code and change to the working folder
            self.send_expect("rm -rf %s" % self.base_dir, "#")

            # unpack dpdk
            out = self.send_expect(
                "tar zxfm %s%s -C %s" % (dst_dir, self.package.split("/")[-1], p_dir),
                "# ",
                60,
                verify=True,
            )
            if out == -1:
                raise ValueError(
                    "Extract dpdk package to %s failure,"
                    "please check params -d" % (p_dir)
                )

            # check dpdk dir name is expect
            out = self.send_expect("ls %s" % self.base_dir, "# ", 20, verify=True)
            if out == -1:
                raise ValueError(
                    "dpdk dir %s mismatch, please check params -d" % self.base_dir
                )

            if self.patches is not None:
                for p in self.patches:
                    out = self.send_expect(
                        "patch -d %s -p1 < %s" % (self.base_dir, dst_dir + p), "# "
                    )
                    assert "****" not in out

    def prerequisites(self):
        """
        Copy DPDK package to DUT and apply patch files.
        """
        self.prepare_package()
        self.dut_prerequisites()
        self.stage = "post-init"

    def extra_nic_setup(self):
        """
        Some nic like RRC required additional setup after module installed
        """
        for port_info in self.ports_info:
            netdev = port_info["port"]
            netdev.setup()

    def bind_interfaces_linux(self, driver="igb_uio", nics_to_bind=None):
        """
        Bind the interfaces to the selected driver. nics_to_bind can be None
        to bind all interfaces or an array with the port indexes
        """
        binding_list = "--bind=%s " % driver

        current_nic = 0
        for port_info in self.ports_info:
            if nics_to_bind is None or current_nic in nics_to_bind:
                binding_list += "%s " % (port_info["pci"])
            current_nic += 1

        bind_script_path = self.get_dpdk_bind_script()
        return self.send_expect(
            "%s --force %s" % (bind_script_path, binding_list), "# "
        )

    def unbind_interfaces_linux(self, nics_to_bind=None):
        """
        Unbind the interfaces
        """

        binding_list = "-u "

        current_nic = 0
        for port_info in self.ports_info:
            if nics_to_bind is None or current_nic in nics_to_bind:
                binding_list += "%s " % (port_info["pci"])
            current_nic += 1

        bind_script_path = self.get_dpdk_bind_script()
        self.send_expect("%s --force %s" % (bind_script_path, binding_list), "# ")

    def build_dpdk_apps(self, folder, extra_options=""):
        """
        Build dpdk sample applications.
        """
        if self.get_os_type() == "linux":
            return self.build_dpdk_apps_linux_meson(folder, extra_options)
        elif self.get_os_type() == "freebsd":
            return self.build_dpdk_apps_freebsd_meson(folder, extra_options)

    def build_dpdk_apps_linux_meson(self, folder, extra_options):
        """
        Build dpdk sample applications on linux use meson
        """
        # icc compile need more time
        if "icc" in self.target:
            timeout = 300
        else:
            timeout = 90

        target_info = self.target.split("-")
        arch = target_info[0]
        if arch == "i686":
            # find the pkg-config path and set the PKG_CONFIG_LIBDIR environmental variable to point it
            out = self.send_expect("find /usr -type d -name pkgconfig", "# ")
            pkg_path = ""
            default_cflags = self.send_expect("echo $CFLAGS", "# ")
            default_pkg_config = self.send_expect("echo $PKG_CONFIG_LIBDIR", "# ")
            res_path = out.split("\r\n")
            for cur_path in res_path:
                if "i386" in cur_path:
                    pkg_path = cur_path
                    break
            assert (
                pkg_path != ""
            ), "please make sure you env have the i386 pkg-config path"

            self.send_expect("export CFLAGS=-m32", "# ", alt_session=True)
            self.send_expect(
                "export PKG_CONFIG_LIBDIR=%s" % pkg_path, "# ", alt_session=True
            )

        folder_info = folder.split("/")
        name = folder_info[-1]
        if name != "examples" and name not in self.apps_name:
            raise Exception(
                f'Please config {name} file path on {os.path.join(CONFIG_ROOT_PATH, "app_name.cfg")}'
            )

        if name == "examples":
            example = "all"
        else:
            example = "/".join(folder_info[folder_info.index("examples") + 1 :])
        out = self.send_expect(
            "meson configure -Dexamples=%s %s" % (example, self.target), "# "
        )
        assert "FAILED" not in out, "Compilation error..."
        out = self.send_expect("ninja -C %s" % self.target, "[~|~\]]# ", timeout)
        assert "FAILED" not in out, "Compilation error..."

        # verify the app build in the config path
        if example != "all":
            out = self.send_expect("ls %s" % self.apps_name[name], "# ", verify=True)
            assert isinstance(out, str), (
                "please confirm %s app path and name in app_name.cfg" % name
            )

        return out

    def build_dpdk_apps_freebsd_meson(self, folder, extra_options):
        # meson build same as linux
        return self.build_dpdk_apps_linux_meson(folder, extra_options)

    def get_blocklist_string(self, target, nic):
        """
        Get block list command string.
        """
        get_blocklist_string = getattr(
            self, "get_blocklist_string_%s" % self.get_os_type()
        )
        return get_blocklist_string(target, nic)

    def get_blocklist_string_linux(self, target, nic):
        """
        Get block list command string on Linux.
        """
        blocklist = ""
        dutPorts = self.get_ports(nic)
        self.restore_interfaces()
        self.send_expect("insmod ./%s/kmod/igb_uio.ko" % target, "# ")
        self.bind_interfaces_linux()
        for port in range(0, len(self.ports_info)):
            if port not in dutPorts:
                blocklist += "-b %s " % self.ports_info[port]["pci"]
        return blocklist

    def get_blocklist_string_freebsd(self, target, nic):
        """
        Get block list command string on Freebsd.
        """
        blocklist = ""
        # No blocklist option in FreeBSD
        return blocklist


class DPDKtester(Tester):

    """
    DPDK project class for tester. DTS will call prerequisites function to setup
    interface and generate port map.
    """

    def __init__(self, crb, serializer, dut_id):
        self.NAME = "tester"
        super(DPDKtester, self).__init__(crb, serializer)

    def prerequisites(self, perf_test=False):
        """
        Setup hugepage on tester and copy validation required files to tester.
        """
        self.kill_all()

        if not self.skip_setup:
            total_huge_pages = self.get_total_huge_pages()
            hugepages_size = self.send_expect(
                "awk '/Hugepagesize/ {print $2}' /proc/meminfo", "# "
            )
            if total_huge_pages == 0:
                self.mount_huge_pages()
                if hugepages_size == "524288":
                    self.set_huge_pages(8)
                else:
                    self.set_huge_pages(1024)

            self.session.copy_file_to("dep/tgen.tgz")
            self.session.copy_file_to("dep/tclclient.tgz")
            # unpack tgen
            out = self.send_expect("tar zxfm tgen.tgz", "# ")
            assert "Error" not in out
            # unpack tclclient
            out = self.send_expect("tar zxfm tclclient.tgz", "# ")
            assert "Error" not in out

        if not self.is_container:
            self.send_expect("modprobe uio", "# ")

        self.tester_prerequisites()

        self.set_promisc()

        self.stage = "post-init"

    def setup_memory(self, hugepages=-1):
        """
        Setup hugepage on tester.
        """
        hugepages_size = self.send_expect(
            "awk '/Hugepagesize/ {print $2}' /proc/meminfo", "# "
        )

        if int(hugepages_size) < (2048 * 2048):
            arch_huge_pages = hugepages if hugepages > 0 else 2048
            total_huge_pages = self.get_total_huge_pages()

        self.mount_huge_pages()
        if total_huge_pages != arch_huge_pages:
            self.set_huge_pages(arch_huge_pages)

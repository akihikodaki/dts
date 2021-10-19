# BSD LICENSE
#
# Copyright(c) 2016-2017 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from framework.config import SuiteConf
from nics.net_device import GetNicObj

conf = SuiteConf('cryptodev_sample')


def build_dpdk_with_cryptodev(test_case):
    # Rebuild the dpdk with cryptodev pmds
    snow3g_lib_path = "/root/libsso_snow3g/snow3g/"
    if "snow3g_lib_path" in conf.suite_cfg:
        snow3g_lib_path = conf.suite_cfg["snow3g_lib_path"]

    zuc_lib_path = "/root/libsso_zuc.1.0.1.1-8/zuc"
    if "zuc_lib_path" in conf.suite_cfg:
        zuc_lib_path = conf.suite_cfg["zuc_lib_path"]

    kasumi_lib_path = "/root/LibSSO_0_3_1/isg_cid-wireless_libs/ciphers/kasumi/"
    if "kasumi_lib_path" in conf.suite_cfg:
        kasumi_lib_path = conf.suite_cfg["kasumi_lib_path"]

    fip_cflags_path = "'-I/opt/openssl-fips-2.0.16/include/'"
    if "fip_cflags_path" in conf.suite_cfg:
        fip_cflags_path = conf.suite_cfg["fip_cflags_path"]

    fip_ldflags_path = "'-L/opt/openssl-fips-2.0.16/'"
    if "fip_ldflags_path" in conf.suite_cfg:
        fip_cflags_path = conf.suite_cfg["fip_ldflags_path"]

    fip_library_path = "/opt/openssl-fips-2.0.16/"
    if "fip_library_path" in conf.suite_cfg:
        fip_cflags_path = conf.suite_cfg["fip_library_path"]

    test_case.dut.send_expect(
        "export LIBSSO_SNOW3G_PATH={}".format(snow3g_lib_path), "#")
    test_case.dut.send_expect(
        "export LIBSSO_ZUC_PATH={}".format(zuc_lib_path), "#")
    test_case.dut.send_expect(
        "export LIBSSO_KASUMI_PATH={}".format(kasumi_lib_path), "#")
    test_case.dut.send_expect(
        "export EXTRA_CFLAGS={}".format(fip_cflags_path), "#")
    test_case.dut.send_expect(
        "export EXTRA_LDFLAGS={}".format(fip_ldflags_path), "#")
    test_case.dut.send_expect(
        "export LD_LIBRARY_PATH={}".format(fip_library_path), "#")

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=n$/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_AESNI_MB': 'y'})

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=n$/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_QAT_SYM': 'y'})

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_QAT_ASYM=n$/CONFIG_RTE_LIBRTE_PMD_QAT_ASYM=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_QAT_ASYM': 'y'})

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_GCM=n$/CONFIG_RTE_LIBRTE_PMD_AESNI_GCM=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_AESNI_GCM': 'y'})

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_OPENSSL=n$/CONFIG_RTE_LIBRTE_PMD_OPENSSL=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_OPENSSL': 'y'})

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_SNOW3G=n$/CONFIG_RTE_LIBRTE_PMD_SNOW3G=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_SNOW3G': 'y'})

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_KASUMI=n$/CONFIG_RTE_LIBRTE_PMD_KASUMI=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_KASUMI': 'y'})

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_ZUC=n$/CONFIG_RTE_LIBRTE_PMD_ZUC=y/' config/common_base", "# ")
    test_case.dut.set_build_options({'RTE_LIBRTE_PMD_ZUC': 'y'})

    test_case.dut.skip_setup = False
    test_case.dut.build_install_dpdk(test_case.dut.target)


def bind_qat_device(test_case, driver = "igb_uio"):
    if driver == 'vfio-pci':
        test_case.dut.send_expect('modprobe vfio', '#', 10)
        test_case.dut.send_expect('modprobe vfio-pci', '#', 10)

    if "crypto_dev_id" in conf.suite_cfg:
        dev_id = conf.suite_cfg["crypto_dev_id"]
        test_case.logger.info("specified the qat hardware device id in cfg: {}".format(dev_id))
        out = test_case.dut.send_expect("lspci -D -d:{}|awk '{{print $1}}'".format(dev_id), "# ", 10)
    else:
        out = test_case.dut.send_expect("lspci -D | grep QuickAssist |awk '{{print $1}}'", "# ", 10)

    pf_list = out.replace("\r", "\n").replace("\n\n", "\n").split("\n")

    dev = {}
    for line in pf_list:
        addr_array = line.strip().split(':')
        if len(addr_array) !=3:
            continue
        domain_id = addr_array[0]
        bus_id = addr_array[1]
        devfun_id = addr_array[2]
        pf_port = GetNicObj(test_case.dut, domain_id, bus_id, devfun_id)

        sriov_vfs_pci = pf_port.get_sriov_vfs_pci()
        if not sriov_vfs_pci:
            raise Exception("can not get vf pci")

        dev[line.strip()] = sriov_vfs_pci

        test_case.dut.bind_eventdev_port(driver, ' '.join(sriov_vfs_pci))

    if not dev:
        raise Exception("can not find qat device")

    test_case.dev = dev


def get_qat_devices(test_case, cpm_num=None, num=1):
    if not cpm_num:
        cpm_num = len(test_case.dev.keys())
    n, dev_list = 0, []
    if cpm_num > len(test_case.dev.keys()):
        test_case.logger.warning("QAT card only {} cpm, but {} required".format(
            len(test_case.dev), cpm_num))
        return []
    for i in range(num):
        for cpm in list(test_case.dev.keys())[:cpm_num]:
            if n >= num:
                break
            if i < len(test_case.dev[cpm]):
                dev_list.append(test_case.dev[cpm][i])
            else:
                test_case.logger.warning("not enough vf in cpm: {}".format(cpm))
            n += 1
    return dev_list


def clear_dpdk_config(test_case):
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=y$/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=y$/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_QAT_ASYM=y$/CONFIG_RTE_LIBRTE_PMD_QAT_ASYM=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_GCM=y$/CONFIG_RTE_LIBRTE_PMD_AESNI_GCM=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_OPENSSL=y$/CONFIG_RTE_LIBRTE_PMD_OPENSSL=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_SNOW3G=y$/CONFIG_RTE_LIBRTE_PMD_SNOW3G=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_KASUMI=y$/CONFIG_RTE_LIBRTE_PMD_KASUMI=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_ZUC=y$/CONFIG_RTE_LIBRTE_PMD_ZUC=n/' config/common_base", "# ")


default_eal_opts = {
    "c": None,
    "l": None,
    "a": None,
    "vdev": None,
    "socket-mem": "512,512",
    "n": "4"
}


def get_eal_opt_str(test_case, override_eal_opts={}, add_port=False):
    cores = ','.join(test_case.dut.get_core_list("1S/3C/1T"))
    if "l" in conf.suite_cfg:
        cores = conf.suite_cfg["l"]
    default_eal_opts.update({'l': cores})
    if "socket-mem" in conf.suite_cfg:
        default_eal_opts.update({"socket-mem": (conf.suite_cfg["socket-mem"])})
    mem_channel = test_case.dut.get_memory_channels()
    default_eal_opts.update({'n': mem_channel})

    return get_opt_str(test_case, default_eal_opts, override_eal_opts, add_port)


def get_opt_str(test_case, default_opts, override_opts={}, add_port=False):
    opts = default_opts.copy()

    # Update options with test suite/case config file
    for key in list(opts.keys()):
        if key in test_case.get_case_cfg():
            opts[key] = test_case.get_case_cfg()[key]

    # Update options with func input
    opts.update(override_opts)

    pci_list = [port["pci"] for port in test_case.dut.ports_info]
    if 'a' in list(opts.keys()) and opts['a']:
        pci_list.append(opts['a'])
    if add_port and pci_list:
        opts['a'] = " -a ".join(pci_list)

    # Generate option string
    opt_str = ""
    for key,value in list(opts.items()):
        if value is None:
            continue
        dash = "-" if len(key) == 1 else "--"
        opt_str = opt_str + "{0}{1} {2} ".format(dash, key, value)

    return opt_str


def get_dpdk_app_cmd_str(app_path, eal_opt_str, app_opt_str=None):
    if not app_opt_str:
        return "{0} {1}".format(app_path, eal_opt_str)
    return "{0} {1} -- {2}".format(app_path, eal_opt_str, app_opt_str)


def is_test_skip(test_case):
    if "test_skip" in test_case.get_case_cfg() \
       and test_case.get_case_cfg()["test_skip"] == "Y":
        test_case.logger.info("Test Skip is YES")
        return True


def is_build_skip(test_case):
    if "build_skip" in conf.suite_cfg \
       and conf.suite_cfg["build_skip"] == "Y":
        test_case.logger.info("Build Skip is YES")
        return True

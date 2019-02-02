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


def build_dpdk_with_cryptodev(test_case):
    # Rebuild the dpdk with cryptodev pmds
    snow3g_lib_path = "/root/libsso_snow3g/snow3g/"
    if "snow3g_lib_path" in test_case.get_suite_cfg():
        snow3g_lib_path = test_case.get_suite_cfg()["snow3g_lib_path"]

    zuc_lib_path = "/root/libsso_zuc.1.0.1.1-8/zuc"
    if "zuc_lib_path" in test_case.get_suite_cfg():
        zuc_lib_path = test_case.get_suite_cfg()["zuc_lib_path"]

    kasumi_lib_path = "/root/LibSSO_0_3_1/isg_cid-wireless_libs/ciphers/kasumi/"
    if "kasumi_lib_path" in test_case.get_suite_cfg():
        kasumi_lib_path = test_case.get_suite_cfg()["kasumi_lib_path"]

    test_case.dut.send_expect(
        "export LIBSSO_SNOW3G_PATH={}".format(snow3g_lib_path), "#")
    test_case.dut.send_expect(
        "export LIBSSO_ZUC_PATH={}".format(zuc_lib_path), "#")
    test_case.dut.send_expect(
        "export LIBSSO_KASUMI_PATH={}".format(kasumi_lib_path), "#")

    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=n$/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=y/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=n$/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=y/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_GCM=n$/CONFIG_RTE_LIBRTE_PMD_AESNI_GCM=y/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_OPENSSL=n$/CONFIG_RTE_LIBRTE_PMD_OPENSSL=y/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_SNOW3G=n$/CONFIG_RTE_LIBRTE_PMD_SNOW3G=y/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_KASUMI=n$/CONFIG_RTE_LIBRTE_PMD_KASUMI=y/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_ZUC=n$/CONFIG_RTE_LIBRTE_PMD_ZUC=y/' config/common_base", "# ")

    test_case.dut.skip_setup = False
    test_case.dut.build_install_dpdk(test_case.dut.target)


def bind_qat_device(test_case, driver = "igb_uio"):
    if not driver:
        test_case.logger.error("Please configure the driver of qat device to bind")
    if driver == 'vfio-pci':
        test_case.dut.send_expect('modprobe vfio-pci', '#', 10)

    if "crypto_dev_id" in test_case.get_suite_cfg():
        crypto_dev_id = test_case.get_suite_cfg()["crypto_dev_id"]
    else:
        crypto_dev_id = "443"
    test_case.logger.info("crypto device id: " + crypto_dev_id)

    # Bind QAT VF devices
    out = test_case.dut.send_expect("lspci -d:{}|awk '{{print $1}}'".format(crypto_dev_id), "# ", 10)
    crypto_list = out.replace("\r", "\n").replace("\n\n", "\n").split("\n")
    test_case._crypto_pci = crypto_list[0]
    test_case.dut.send_expect(
        'echo "8086 {}" > /sys/bus/pci/drivers/{}/new_id'.format(crypto_dev_id, driver), "# ", 10)
    for line in crypto_list:
        cmd = "echo 0000:{} > /sys/bus/pci/devices/0000\:{}/driver/unbind".format(
            line, line.replace(":", "\:"))
        test_case.dut.send_expect(cmd, "# ", 10)
        cmd = "echo 0000:{} > /sys/bus/pci/drivers/{}/bind".format(
            line, driver)
        test_case.dut.send_expect(cmd, "# ", 10)


def clear_dpdk_config(test_case):
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=y$/CONFIG_RTE_LIBRTE_PMD_AESNI_MB=n/' config/common_base", "# ")
    test_case.dut.send_expect(
        "sed -i 's/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=y$/CONFIG_RTE_LIBRTE_PMD_QAT_SYM=n/' config/common_base", "# ")
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
    "w": None,
    "vdev": None,
    "socket-mem": "512,512",
    "n": "4"
}


def get_eal_opt_str(test_case, override_eal_opts={}):
    return get_opt_str(test_case, default_eal_opts, override_eal_opts)


def get_opt_str(test_case, default_opts, override_opts={}):
    opts = default_opts.copy()

    # Update options with test suite/case config file
    for key in opts.keys():
        if key in test_case.get_case_cfg():
            opts[key] = test_case.get_case_cfg()[key]

    # Update options with func input
    opts.update(override_opts)

    # Generate option string
    opt_str = ""
    for key,value in opts.items():
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
    if "build_skip" in test_case.get_suite_cfg() \
       and test_case.get_suite_cfg()["build_skip"] == "Y":
        test_case.logger.info("Build Skip is YES")
        return True

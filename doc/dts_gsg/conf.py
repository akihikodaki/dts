# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2017 Intel Corporation
#

import subprocess

try:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
except:
    pass

project = "DPDK Test Suite"
copyright = "2017, dpdk.org"

strip_version_cmd = (
    "import sys;sys.path.append('../..');import version; print version.dts_version()"
)
version = subprocess.check_output(["python", "-c", strip_version_cmd])
version = version.decode("utf-8").rstrip()
release = version

master_doc = "index"

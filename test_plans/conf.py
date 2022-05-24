# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2017 Intel Corporation
#

try:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
except:
    pass

project = "DPDK Test Plans"
copyright = "2017, dpdk.org"
master_doc = "index"

# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

import os
import re
import shutil

from .exception import VerifyFailure

"""
Generate Rst Test Result Report

Example:
    import framework.rst as rst
    rst.write_title("Test Case: " + test_case.__name__)
    out = table.draw()
    rst.write_text('\n' + out + '\n\n')
    rst.write_result("PASS")

Result:
    <copyright>
    <Prerequisites>
    Test Case: CASE
    ---------------
    Result: PASS
"""

path2Plan = "test_plans"
path2Result = "output"


class RstReport(object):
    def __init__(self, crbName, target, nic, suite, perf=False):
        """
        copy desc from #Name#_test_plan.rst to TestResult_#Name#.rst
        """
        try:
            path = [path2Result, crbName, target, nic]
            # ensure the level folder exist
            for node in range(0, len(path)):
                if not os.path.exists("/".join(path[: node + 1])):
                    for level in range(node, len(path)):
                        os.mkdir("/".join(path[: level + 1]))
                    break

            self.rstName = "%s/TestResult_%s.rst" % ("/".join(path), suite)
            rstReport = open(self.rstName, "w")

            if perf is True:
                self.rstAnnexName = "%s/TestResult_%s_Annex.rst" % (
                    "/".join(path),
                    suite,
                )
                rstAnnexReport = open(self.rstAnnexName, "w")

            f = open("%s/%s_test_plan.rst" % (path2Plan, suite), "r")
            for line in f:
                if line[:13] == "Prerequisites":
                    break
                rstReport.write(line)
                if perf is True:
                    rstAnnexReport.write(line)
            f.close()

            rstReport.close()

        except Exception as e:
            raise VerifyFailure("RST Error: " + str(e))

    def clear_all_rst(self, crbName, target):
        path = [path2Result, crbName, target]
        shutil.rmtree("/".join(path), True)

    def write_title(self, text):
        """
        write case title Test Case: #Name#
        -----------------
        """
        line = "\n%s\n" % text
        with open(self.rstName, "a") as f:
            f.write(line)
            f.write("-" * len(line) + "\n")

    def write_subtitle(self):
        if self._subtitle is not None:
            with open(self.rstName, "a") as f:
                f.write("%s\n" % self._subtitle)

    def write_annex_title(self, text):
        """
        write annex to test case title Annex to #Name#
        -----------------
        """
        line = "\n%s\n" % text
        with open(self.rstAnnexName, "a") as f:
            f.write(line)
            f.write("-" * len(line) + "\n")

    def write_text(self, text, annex=False):
        rstFile = self.rstAnnexName if annex else self.rstName

        with open(rstFile, "a") as f:
            f.write(text)

    def write_frame(self, text, annex=False):
        self.write_text("\n::\n\n", annex)
        parts = re.findall(r"\S+", text)
        text = ""
        length = 0

        for part in parts:
            if length + len(part) > 75:
                text = text + "\n" + " " + part
                length = len(part)
            else:
                length = length + len(part)
                text = text + " " + part
        self.write_text(text, annex)
        self.write_text("\n\n", annex)

    def write_result(self, result):
        with open(self.rstName, "a") as f:
            f.write("\nResult: " + result + "\n")

    def include_image(self, image, width=90):
        """
        Includes an image in the RST file.
        The argument must include path, name and extension.
        """
        with open(self.rstName, "a") as f:
            f.write(".. image:: %s\n   :width: %d%%\n\n" % (image, width))

    def report(self, text, frame=False, annex=False):
        """
        Save report text into rst file.
        """
        if frame:
            self.write_frame(text, annex)
        else:
            self.write_text(text, annex)

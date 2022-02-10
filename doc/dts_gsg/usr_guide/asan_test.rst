About ASan
===========

AddressSanitizer a.k.a. ASan is a widely-used debugging tool to detect memory access errors.
It helps to detect issues like use-after-free, various kinds of buffer overruns in C/C++
programs, and other similar errors, as well as printing out detailed debug information whenever
an error is detected.

ASan is integrated with gcc and clang and can be enabled via a meson option: -Db_sanitize=address,
See the documentation for details (especially regarding clang).

About ASan test
===============

DTS adds one parameter named asan to control ASan test, support through added asan parameter,
otherwise not support. It contains three steps on the whole:

 - Append ASan build parameters to meson build options. this may open the function of ASan detect
   memory access errors. if occuring memory access errors, the stack info will recorded in DTS log

 - After all cases tested finish, analyze DTS log and redefine case test result according to whether
   case log contain memory access error info. modify the result to failed if contain otherwise inherit
   the original result.

 - Generate ASan report to distinguish it from the original report.

ASan test steps
=======================

Check ASan test config
----------------------

ASan config file is placed in conf/asan.cfg

Firstly, check the log filter bounds pairs, customer can modify the pairs if need, and use colon split
bounds, use comma split pairs, there are two pairs key word default as follow:

 - filter_bounds=LeakSanitizer:SUMMARY,AddressSanitizer:SUMMARY

Secondly, check the meson build parameter options pair, there is a list of parameters default as follow:

 - build_param=-Dbuildtype=debug -Db_lundef=false -Db_sanitize=address

Launch DTS
----------

 ./dts --asan

When launch DTS, there are two parameters need attention:
 - provide --asan parameter, means support ASan test.
 - Don't provide -s parameter to skip build DPDK package. ASan test need rebuild DPDK package.

Obtain the ASan test report
---------------------------

ASan report located at DTS output directory also, and provided three format as follow:
 - Json format named asan_test_results.json
 - Excel format named asan_test_results.xls
 - Statistics information of txt format named asan_statistics.txt
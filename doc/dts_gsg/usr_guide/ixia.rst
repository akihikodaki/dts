Practice with IxExplorer
========================

This chapter describes a DTS practice with IXIA IxExplorer, which mainly used for performance testing.
Here we take the performance case nic_single_core as an example.

Configuring your own execution file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First of all, you must configure execution.cfg as below:

.. code-block:: console

   [Execution1]
   crbs=192.168.1.1
   drivername=vfio-pci
   test_suites=
       nic_single_core_perf,
   targets=
       x86_64-native-linuxapp-gcc
   parameters=nic_type=cfg:perf=true
   build_type=meson
   rx_mode=avx512

Configure CRB information
~~~~~~~~~~~~~~~~~~~~~~~~~

Then please add the detail information about your CRB in $DTS_CFG_FOLDER/crbs.conf as following:

.. code-block:: console

   [192.168.1.1]
   dut_ip=192.168.1.1
   dut_user=root
   dut_passwd=passwd
   os=linux
   dut_arch=
   tester_ip=192.168.1.1
   tester_passwd=passwd
   pktgen_group=IXIA
   channels=4
   bypass_core0=True
   dut_cores=

Configure port information
~~~~~~~~~~~~~~~~~~~~~~~~~~

ports topology as below:

.. code-block:: console

   IXIA port 0 <---------> DUT port 0
   IXIA port 1 <---------> DUT port 1

please add port configuration in $DTS_CFG_FOLDER/ports.cfg as following:

.. code-block:: console

   [192.168.1.1]
   ports =
       pci=0000:af:00.0,peer=IXIA:3.1;
       pci=0000:b1:00.0,peer=IXIA:3.2;

Configure pktgen information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

please configure Pktgen information in $DTS_CFG_FOLDER/pktgen.cfg

.. code-block:: console

   [IXIA]
   ixia_version=9.00
   ixia_ip=192.168.2.1
   ixia_ports=
       card=3,port=1;
       card=3,port=2;
   ixia_force100g=disable

.. note::

    The version of ixia must be consistent with your version of IxExplorer.


Configure your own suites
~~~~~~~~~~~~~~~~~~~~~~~~~

Performance tests generally have configuration files.
it's name corresponds to the suite.
Below is the $DTS_CFG_FOLDER/nic_single_core_perf.cfg configuration file.
You can set the test parameters according to your test needs.


.. code-block:: console

   [suite]
   update_expected = True
   test_parameters = {'1C/1T': {64: [512, 2048]},
                      '1C/2T': {64: [512, 2048]}}
   rx_desc_16byte = 'y'
   test_duration = 60
   accepted_tolerance = 1
   expected_throughput = {
        'fortville_spirit': {
            '1C/1T': {64: {512: 0.00, 2048: 0.00}},
            '1C/2T': {64: {512: 0.00, 2048: 0.00}}}}

* accepted_tolerance: defines the accepted tolerance between real pps and expected pps.
* test_parameters: defines the combination of frame size and descriptor numbers,
  and the pattern is {'frame size': ['descriptor number #1', 'descriptor number #2']}.
* rx_desc_16byte: 16byte configuration and default by enabled.
* test_duration: how many seconds each combination performance will be recorded.
* expected_throughput: it's a dictionary defining expected throughput numbers based on NIC,
  and the pattern is {'NIC': {'frame size': {'descriptor number': 'excepted throughput'}}}
  Every user should fill it out with your actual numbers.
* update_expected: if update_expected==True, and add argument "--update-expected" in bash command,
  all objects in this file will changed after the run::

   ./dts --update-expected

At the beginning, please change test_parameters according to your requirements,
then run ./dts --update-expected to get the absolute results which will replace
the default numbers 0.00 in this configuration.
So you will have your own private configuration, and could start your tests as usual.


Run DTS performance test with IXIA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now you can start DTS performance test with IXIA:

.. code-block:: console

    root@test1:~/dts# ./dts
                  dts:
    DUT 192.168.1.1
                        tester: ssh root@192.168.1.1
                        ...
    pktgen: ssh root@192.168.1.1
                        pktgen: tclsh
                        pktgen: source ./IxiaWish.tcl
                        pktgen: set ::env(IXIA_VERSION) 9.00
                        pktgen: package req IxTclHal
                        pktgen: ixConnectToTclServer 192.168.2.1
                        pktgen: ixLogin IxiaTclUser
                        pktgen: ixConnectToChassis 192.168.2.1
                        pktgen: set chasId [ixGetChassisID 192.168.2.1]
                        pktgen: ixClearOwnership [list [list 1 3 1] [list 1 3 2]]
                        pktgen: ixTakeOwnership [list [list 1 3 1] [list 1 3 2]] force
                        pktgen: stat getLineSpeed 1 3 1
                        pktgen: stat getLineSpeed 1 3 2
                        ...

    TestNicSingleCorePerf: Test Case test_perf_nic_single_core Begin
    TestNicSingleCorePerf: Executing Test Using cores: ['28', '29'] of config 1C/1T
    TestNicSingleCorePerf: Test running at parameters: framesize: 64, rxd/txd: 512
    dut.192.168.1.1: x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 28,29 -n 6 -a 0000:af:00.0 -a 0000:b1:00.0 -- -i --portmask=0x3 --rxq=2 --txq=2 --txd=512 --rxd=512 --nb-cores=1
    dut.192.168.1.1: start
                   pktgen: stat getLineSpeed 1 1 1
                   pktgen: stat getLineSpeed 1 1 2
                   pktgen: scp -v dumppcap.py root@192.168.1.1:~/
                   pktgen: scapy -c dumppcap.py 2>/dev/null
                   pktgen: scp -v dumppcap.py root@192.168.1.1:~/
                   pktgen: scapy -c dumppcap.py 2>/dev/null
                   pktgen: scp -v dumppcap.py root@192.168.1.1:~/
                   pktgen: scapy -c dumppcap.py 2>/dev/null
                   pktgen: scp -v dumppcap.py root@192.168.1.1:~/
                   pktgen: scapy -c dumppcap.py 2>/dev/null
                   pktgen: begin traffic ......
                   tester: scp -v ixiaConfig.tcl root@192.168.1.1:~/
                   pktgen: source ixiaConfig.tcl
                   pktgen: begin get port statistic ...
                   pktgen: stat getRate statAllStats 1 3 2
                   pktgen: stat cget -framesReceived
                   pktgen: stat cget -bitsReceived
                   pktgen: stat cget -oversize
                   pktgen: stat getRate statAllStats 1 3 1
                   pktgen: stat cget -framesReceived
                   pktgen: stat cget -bitsReceived
                   pktgen: stat cget -oversize
                   pktgen: stat getRate statAllStats 1 3 2
                   pktgen: stat cget -framesReceived
                   pktgen: stat cget -bitsReceived
                   pktgen: stat cget -oversize
                   pktgen: stat getRate statAllStats 1 3 1
                   pktgen: stat cget -framesReceived
                   pktgen: stat cget -bitsReceived
                   pktgen: stat cget -oversize
                   pktgen: throughput: pps_rx 69504677.000000, bps_rx 35586394625.000000
                   pktgen: ixStopTransmit portList
                   pktgen: traffic completed.
      dut.192.168.1.1: stop
      dut.192.168.1.1: quit
      TestNicSingleCorePerf: Trouthput of framesize: 64, rxd/txd: 512 is :69.504677 Mpps
      ...

         TestNicSingleCorePerf:
      +----------+------------+---------+-------------+---------+---------------------+-----------------------+
      | Fwd_core | Frame Size | TXD/RXD | Throughput  |  Rate   | Expected Throughput | Throughput Difference |
      +==========+============+=========+=============+=========+=====================+=======================+
      | 1C/1T    | 64         | 512     | 69.505 Mpps | 93.414% | 0.000 Mpps          | 69.505 Mpps           |
      +----------+------------+---------+-------------+---------+---------------------+-----------------------+
      | 1C/1T    | 64         | 2048    | 51.078 Mpps | 68.649% | 0.000 Mpps          | 51.078 Mpps           |
      +----------+------------+---------+-------------+---------+---------------------+-----------------------+
      | 1C/2T    | 64         | 512     | 74.404 Mpps | 99.999% | 0.000 Mpps          | 74.404 Mpps           |
      +----------+------------+---------+-------------+---------+---------------------+-----------------------+
      | 1C/2T    | 64         | 2048    | 67.851 Mpps | 91.192% | 0.000 Mpps          | 67.851 Mpps           |
      +----------+------------+---------+-------------+---------+---------------------+-----------------------+
         TestNicSingleCorePerf: Test Case test_perf_nic_single_core Result PASSED:


Test result
~~~~~~~~~~~

After the Test Suite finished the validation, we can find the result files as below in output folder.

.. code-block:: console

   fortville_25g_single_core_perf.json  dts.log  TestNicSingleCorePerf.log test_results.json

The performance case will save the data results in the jison file.
And the pattern is "nic name + suite name.json".
Below is the json file of nic_single_core:

.. code-block:: console

      vim fortville_25g_single_core_perf.json

      {"test_perf_nic_single_core": [{
                "performance": [{"name": "Throughput", "value": 69.505, "unit": "Mpps", "delta": 69.505}],
                "parameters":  [{"name": "Txd/Rxd", "value": 512, "unit": "descriptor"},
                               {"name": "frame_size", "value": 64, "unit": "bytes"},
                               {"name": "Fwd_core", "value": "1C/1T"}], "status": "PASS"},
                {"performance": [{"name": "Throughput", "value": 51.078, "unit": "Mpps", "delta": 51.078}],
                 "parameters": [{"name": "Txd/Rxd", "value": 2048, "unit": "descriptor"},
                                {"name": "frame_size", "value": 64, "unit": "bytes"},
                                {"name": "Fwd_core", "value": "1C/1T"}], "status": "PASS"},
               {"performance": [{"name": "Throughput", "value": 74.404, "unit": "Mpps", "delta": 74.404}],
                "parameters": [{"name": "Txd/Rxd", "value": 512, "unit": "descriptor"},
                                {"name": "frame_size", "value": 64, "unit": "bytes"},
                                {"name": "Fwd_core", "value": "1C/2T"}], "status": "PASS"},
               {"performance": [{"name": "Throughput", "value": 67.851, "unit": "Mpps", "delta": 67.851}],
                "parameters": [{"name": "Txd/Rxd", "value": 2048, "unit": "descriptor"},
                               {"name": "frame_size", "value": 64, "unit": "bytes"},
                               {"name": "Fwd_core", "value": "1C/2T"}], "status": "PASS"}]}


You can set your own expectations in con/suite.cfg based on the json data.
If the actual data differs too much from the expected data, the case fails.

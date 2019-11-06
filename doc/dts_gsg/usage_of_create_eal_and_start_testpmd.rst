How create_eal_parameters and start_testpmd methods use in DPDK Test Suite
===========================

create_eal_parameters
----------------------------

This method used to create EAL parameters character string in DPDK Test Suite.
for example: -l 1,2 -w 0000:88:00.0 -w 0000:88:00.1 --file-prefix=dpdk_1112_20190809143420.

.. code-block:: console

   define: create_eal_parameters(self, fixed_prefix=False, socket=-1, **config)

   usage and example:
        no user parameters:
            param = self.dut.create_eal_parameters()
            output:
                param = '-l 1,2 -n 4 -w 0000:1a:00.0 -w 0000:1a:00.1 --file-prefix=dpdk_397938_20191105143309'

        user parameters:
            1. usage for port and port options, there are two methods for them.
                param = self.dut.create_eal_parameters(cores='1S/4C/1T', ports=[0,1], port_options={0: "proto_xtr=vlan"})
                or
                param = self.dut.create_eal_parameters(cores='1S/4C/1T', ports=['0000:1a:00.0', '0000:1a:00.1'], port_options={'0000:1a:00.0': "proto_xtr=vlan"})
                output:
                    param = '-l 1,2,3,4 -n 4 -w 0000:1a:00.0,proto_xtr=vlan -w 0000:1a:00.1  --file-prefix=dpdk_399214_20191105155446'

            2. usage for b_ports.
                param = self.dut.create_eal_parameters(cores='1S/4C/1T', b_ports=[0])
                or
                param = self.dut.create_eal_parameters(cores='1S/4C/1T', b_ports=['0000:1a:00.0'])
                output:
                    param = '-l 1,2,3,4 -n 4  -b 0000:1a:00.0 --file-prefix=dpdk_399214_20191105155446'

            3. usage for no-pci.
                param = self.dut.create_eal_parameters(cores='1S/4C/1T', no_pci=True)
                output:
                    param = '-l 1,2,3,4 -n 4 --file-prefix=dpdk_399214_20191105155446 --no-pci'

            4. usage for prefix, if fixed_prefix = True, the file-prefix will use the value of prefix, or the value is dpdk_pid_timestamp.
                param = self.dut.create_eal_parameters(cores='1S/4C/1T', ports=[0, 1], port_options={0: "proto_xtr=vlan"}, fixed_prefix=True, prefix='user_defined')
                output:
                    param = '-l 1,2,3,4 -n 4 -w 0000:1a:00.0,proto_xtr=vlan -w 0000:1a:00.1  --file-prefix=user_defined'

            5. usege for vdevs.
                param_vdev = self.dut.create_eal_parameters(cores='1S/4C/1T', no_pci=True, vdevs=[r"net_virtio_user0,mac=%s,path=./vhost-net,queues=1"])
                output:
                    param = '-l 1,2,3,4 -n 4   --file-prefix=dpdk_399214_20191105155446 --no-pci --vdev net_virtio_user0,mac=%s,path=./vhost-net,queues=1'


create_eal_parameters function supports the following parameters:

.. table::

    +---------------------------+---------------------------------------------------+------------------+
    | parameter                 | description                                       | Default Value    |
    +---------------------------+---------------------------------------------------+------------------+
    | fixed_prefix              | Indicate use default prefix or user define prefix | False            |
    +---------------------------+---------------------------------------------------+------------------+
    | socket                    | socket of system                                  | -1               |
    +---------------------------+---------------------------------------------------+------------------+
    | cores                     | set core list                                     | 1S/2C/1T         |
    +---------------------------+---------------------------------------------------+------------------+
    | ports                     | PCI list or PCI ID list                           |                  |
    +---------------------------+---------------------------------------------------+------------------+
    | port_options              | other port options                                |                  |
    +---------------------------+---------------------------------------------------+------------------+
    | b_ports                   | PCI device in black list                          |                  |
    +---------------------------+---------------------------------------------------+------------------+
    | no_pci                    | Disable PCI bug                                   |                  |
    +---------------------------+---------------------------------------------------+------------------+
    | prefix                    | Use a different shared data file prefix for a     |                  |
    |                           | DPDK process                                      |                  |
    +---------------------------+---------------------------------------------------+------------------+
    | vdevs                     | Add a virtual device                              |                  |
    +---------------------------+---------------------------------------------------+------------------+


start_testpmd
----------------------------

The method use to start testpmd application.

.. code-block:: console

   define: start_testpmd(self, cores='default', param='', eal_param='', socket=0, fixed_prefix=False, **config)

   usage and example:
        no user parameters:
            out = self.pmdout.start_testpmd()
        user parameters:
            1. Those two parameters param and eal_param are used for current test suites.
                for example:
                    In current test suite TestSuite_runtime_vf_queue_number, the eal parameters are wrote as a line string as below.
                        eal_param = '-w %s,queue-num-per-vf=%d --file-prefix=test1 --socket-mem 1024,1024' % (self.pf_pci, invalid_qn)
                    then you can call start_testpmd like this.
                        out = self.pmdout.start_testpmd(self.pmdout.default_cores, param='', eal_param=eal_param)

                    Another usage in current test suite like below:
                        self.pmdout.start_testpmd("Default", "--portmask=%s " %(self.portMask) + " --enable-rx-cksum " + "--port-topology=loop", socket=self.ports_socket)

            2. If you will write a new test suite and need to call start_testpmd method,
                The usage of other parameters such as cores, socket, fixed_prefix and **config are the same as create_eal_parameters.
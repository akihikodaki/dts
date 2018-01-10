Multiple Virtual Machines Management
====================================

When managing multiple virtual machines, waiting around 2 minutes for each VM will be exhausted. So DTS imported parallel threads model into multiple VMs management scenario.

.. note::
    Critical resources and actions which can't be handled in parallel have been protected by function level lock.

Command arguments
-----------------

Multiple VMs module support start VMs or send commands to VMs in parallel with specified arguments format.

Arguments for "start" command:

.. table::

    +-----------------+----------------------------------+----------------+-------------+
    | name            | Description                      | Default value  | Must have   |
    |                 |                                  |                |             |
    +-----------------+----------------------------------+----------------+-------------+
    | name            | virtual machine name             | N/A            | Yes         |
    +-----------------+----------------------------------+----------------+-------------+
    | dut_id          | index of DUT                     | 0              | No          |
    +-----------------+----------------------------------+----------------+-------------+
    | autodetect_topo | whether detect network topology  | False          | No          |
    |                 | automatically                    |                |             |
    +-----------------+----------------------------------+----------------+-------------+
    | virt_config     | virtual machine config location  | N/A            | Alternative |
    +-----------------+----------------------------------+----------------+-------------+
    | virt_params     | local parameters of virutal      | N/A            | Alternative |
    |                 | machine                          |                |             |
    +-----------------+----------------------------------+----------------+-------------+

Arguments for "cmd" command:

.. table::

    +-----------------+----------------------------------+----------------+-------------+
    | name            | Description                      | Default value  | Must have   |
    |                 |                                  |                |             |
    +-----------------+----------------------------------+----------------+-------------+
    | name            | virtual machine name             | N/A            | Yes         |
    +-----------------+----------------------------------+----------------+-------------+
    | dut_id          | index of DUT                     | 0              | No          |
    +-----------------+----------------------------------+----------------+-------------+
    | commands        | list of commands which will be   | N/A            | Yes         |
    |                 | sent into the vitual machine     |                |             |
    +-----------------+----------------------------------+----------------+-------------+
    | expects         | list of expect output of the     | N/A            | Yes         |
    |                 | commands                         |                |             |
    +-----------------+----------------------------------+----------------+-------------+
    | timeouts        | list of timeout value of the     | N/A            | Yes         |
    |                 | commands                         |                |             |
    +-----------------+----------------------------------+----------------+-------------+

.. note::
    If there's nothing expected for the command, still need to define expected string as blank

Multiple module will catagorize and save the result value after all tasks have been done. Later users can retrieve the result by function get_parallel_result.

Sample Code
-----------

.. code-block:: console

    vm_task = MultipleVM(max_vm=self.VM_NUM, duts=self.duts)

    for dut_id in range(len(self.duts)):
        for vm_idx in range(VM_NUM):
            vm_name = "vm%d" % vm_idx
            args = {'name': vm_name,
                    'dut_id': dut_id,
                    'autodetect_topo': False,
                    'virt_params': {
                        'qemu': [{'path': '/usr/local/bin/qemu-system-x86_64'}],
                        'cpu': [{'model': 'host', 'number': '1', 'cpupin': ''}],
                        'mem': [{'size': '1024', 'hugepage': 'yes'}],
                        'disk': [{'file': '/storage/vm-image/%s.qcow2' % vm_name}],
                        'login': [{'user': 'root', 'password': 'root'}],
                        'device': None}
                    }

            vm_task.add_parallel_task(action="start", config=args)

    vm_task.do_parallel_task()
    print vm_task.get_parallel_result()

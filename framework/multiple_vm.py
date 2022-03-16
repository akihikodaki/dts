import re
import threading
import time
import traceback

import threadpool

from .logger import getLogger
from .settings import DTS_ERR_TBL, DTS_PARALLEL_SETTING, save_global_setting
from .utils import RED


class MultipleVM(object):
    """
    Module for handle VM related actions in parallel on multiple DUTs
    Supported actions: [start|command|migration]
    Param max_vm: maximum number of threads
    Param duts: list of DUT objects
    """

    def __init__(self, max_vm, duts):
        self.max_vm = max_vm
        self.duts = duts
        self.pool = threadpool.ThreadPool(max_vm)
        self.pool_result = [dict() for _ in duts]
        self._pool_requests = list()
        self._pool_executors = dict()
        self.logger = getLogger("multiple_vm")

        self.logger.info(
            "Created MultipleVM instance with %d DUTs and %d VMs" % (len(duts), max_vm)
        )

    def parallel_vm_start(self, args):
        """
        Start VMs in parallel.
        Args format:
        {
            'name': 'VM0',
            'dut_id': 1,
            'autodetect_topo': False,
            'virt_config': { 'suite_name': '',
                             'vm_name': '',
                           }
            'virt_params' : {
                    'qemu': [{'path': '/usr/local/bin/qemu-system-x86_64'},
                    'cpu': [{'model': 'host', 'number': '1'},
                    'mem': [{'size': '1024', 'hugepage': 'yes'},
                    'disk': [{'file': 'vm0.qcow2'},
                    'login': [{'user': 'root', 'password': 'root'},
                    'vnc' : [{'displayNum': '2'},
                    'device': [{'driver': 'vfio-pci', 'opt_host': '0000:82:00.1'}]
                              [{'driver': 'vhost-user', 'opt_path': '/tmp/vhost-user-0',
                               'opt_mac': '',
                               'opt_legacy': 'on' | 'off'}],
                    'migration': [{'enable': 'yes'}]
            }

            'command': ''
        }

        return format:
        {
            'name': 'VM0',
            'dut_id' : 1,
            'vm_obj': vm_obj
        }
        """

        result = {}
        vm_name = args["name"]
        dut_id = args["dut_id"]

        if "autodetect_topo" in args:
            autodetect_topo = args["autodetect_topo"]
        else:
            autodetect_topo = True

        self.logger.info("Parallel task start for DUT%d %s" % (dut_id, vm_name))
        threading.current_thread().name = vm_name

        from .qemu_kvm import QEMUKvm

        # VM configured by configuration file
        if "virt_config" in args:
            suite_name = args["virt_config"]["suite_name"]
            vm_name = args["virt_config"]["vm_name"]
            vm_obj = QEMUKvm(self.duts[dut_id], vm_name, suite_name)
            if "virt_params" in args:
                virt_params = args["virt_params"]
            else:
                virt_params = dict()
        else:
            # VM configured by parameters
            vm_obj = QEMUKvm(self.duts[dut_id], vm_name, "multi_vm")
            virt_params = args["virt_params"]
            # just save config, should be list
            vm_obj.set_local_config([virt_params])

        vm_dut = None

        if vm_obj.check_alive():
            self.logger.debug("Check VM[%s] is alive" % vm_name)
            vm_obj.attach()
            self.logger.debug("VM[%s] attach is done" % vm_name)
            if "migration" in virt_params:
                self.logger.debug("Immigrated VM[%s] is ready" % vm_name)
            else:
                vm_dut = vm_obj.instantiate_vm_dut(autodetect_topo=autodetect_topo)
                self.logger.debug("VM[%s] instantiate vm dut is done" % vm_name)
        else:
            vm_obj.quick_start()
            self.duts[dut_id].logger.debug("VM[%s] quick start is done" % vm_name)
            if "migration" in virt_params:
                self.logger.debug("Immigrated VM[%s] is ready" % vm_name)
            else:
                vm_obj._check_vm_status()
                self.logger.debug("VM[%s] check status is done" % vm_name)
                vm_dut = vm_obj.instantiate_vm_dut(autodetect_topo=autodetect_topo)
                self.logger.debug("VM[%s] instantiate vm dut is done" % vm_name)

        result["name"] = vm_name
        result["dut_id"] = dut_id
        result["vm_obj"] = vm_obj
        result["vm_dut"] = vm_dut
        self.logger.info("Parallel task DUT%d %s Done and returned" % (dut_id, vm_name))
        return result

    def parallel_vm_stop(self, args):
        NotImplemented

    def parallel_vm_command(self, args):
        """
        Run commands in parallel.
        Args format:
        {
            'name': 'vm1',
            'vm_dut': self.vm_dut,
            'dut_id': 0,
            'commands': ['cd dpdk', 'make install T=x86_64-native-linuxapp-gcc'],
            'expects': ['#', "#"],
            'timeouts': [5, 120],
        }
        """
        result = {}
        vm_name = args["name"]
        vm_dut = args["vm_dut"]
        dut_id = args["dut_id"]
        commands = args["commands"]
        expects = args["expects"]
        timeouts = args["timeouts"]
        outputs = []

        if "delay" in args:
            time.sleep(args["delay"])

        self.logger.debug("Parallel task start for DUT%d %s" % (dut_id, vm_name))

        combinations = list(zip(commands, expects, timeouts))
        for combine in combinations:
            command, expect, timeout = combine
            # timeout value need enlarge if vm number increased
            add_time = int(self.max_vm * 0.5)
            timeout += add_time
            if len(expect) == 0:
                output = vm_dut.send_command(command, timeout)
            else:
                output = vm_dut.send_expect(command, expect, timeout)
            outputs.append(output)

        result["name"] = vm_name
        result["dut_id"] = dut_id
        result["outputs"] = outputs
        self.logger.debug(
            "Parallel task for DUT%d %s has been done and returned" % (dut_id, vm_name)
        )

        return result

    def parallel_vm_migration(self, args):
        """
        Do vm migration action in parallel.
        Args format:
        {
            'name': 'vm1',
            'vm_obj': self.vm_obj,
            'remote_ip': host2_ip,
            'migrage_port': 6666,
        }
        """
        result = {}
        vm_name = args["name"]
        vm_obj = args["vm_obj"]
        dut_id = args["dut_id"]
        remote_ip = args["remote_ip"]
        migrate_port = args["migrate_port"]

        vm_obj.start_migration(remote_ip, migrate_port)
        vm_obj.wait_migration_done()

        result["name"] = vm_name
        result["dut_id"] = dut_id

        return result

    def save_result(self, request, result):
        """
        Save result in local variable, will be used later
        """
        self.pool_result[result["dut_id"]][result["name"]] = result
        self.pool_result[result["dut_id"]][result["name"]]["status"] = 0

    def handle_vm_exception(self, request, exc_info):
        """
        Handle exception when do parallel task
        should check vm status in this function
        """
        if not isinstance(exc_info, tuple):
            # Something is seriously wrong...
            print(request)
            print(exc_info)
            raise SystemExit

        # print traceback info for exception
        name = request.args[0]["name"]
        self.logger.error(
            ("**** Exception occurred DUT%d:%s" % (request.args[0]["dut_id"], name))
        )
        exc_type, exc_value, exc_traceback = exc_info
        self.logger.error(repr(traceback.format_tb(exc_traceback)))

        result = {"name": name, "dut_id": request.args[0]["dut_id"]}
        self.pool_result[result["dut_id"]][result["name"]] = result
        self.pool_result[result["dut_id"]][result["name"]]["status"] = DTS_ERR_TBL[
            "PARALLEL_EXECUTE_ERR"
        ]

    def add_parallel_task(self, action, config):
        """
        Add task into parallel pool, will call corresponding function later
        based on action type.
        """
        if action == "start":
            task = self.parallel_vm_start
            data = config
        elif action == "stop":
            task = self.parallel_vm_stop
            data = config["name"]
        elif action == "cmd":
            # just string command by now
            task = self.parallel_vm_command
            data = config
        elif action == "migration":
            task = self.parallel_vm_migration
            data = config

        # due to threadpool request, one item
        request = threadpool.makeRequests(
            task, [data], self.save_result, self.handle_vm_exception
        )
        self._pool_requests.extend(request)

    def do_parallel_task(self):
        """
        Do configured tasks in parallel, will return if all tasks finished
        """
        # set parallel mode
        save_global_setting(DTS_PARALLEL_SETTING, "yes")

        self.pool_result = [dict() for _ in self.duts]
        for req in self._pool_requests:
            self.pool.putRequest(req)

        self.logger.info("All parallel tasks start at %s" % time.ctime())
        # clean the request queue
        self._pool_requests = list()

        while True:
            try:
                time.sleep(0.5)
                self.pool.poll()
            except threadpool.NoResultsPending:
                self.logger.info(
                    "All parallel tasks have been done at %s" % time.ctime()
                )
                break
            except Exception as e:
                self.logger.error("Met exception %s" % (str(e)))
                break

        # clear pool related queues, clean thread
        self.pool._requests_queue.queue.clear()
        self.pool._results_queue.queue.clear()

        time.sleep(2)

        # exit from parallel mode
        save_global_setting(DTS_PARALLEL_SETTING, "no")

    def get_parallel_result(self):
        """
        Return result information for this parallel task
        """
        return self.pool_result

    def list_threads(self):
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            self.logger.error("thread [%s] is still activing" % t.getName())

    def destroy_parallel(self):
        """
        Destroy created threads otherwise threads may can't created
        """
        self.pool.dismissWorkers(self.max_vm, do_join=True)
        self.pool.wait()
        self.list_threads()

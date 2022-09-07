# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019-2020 Intel Corporation
#

import os
import re
import time

from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestAfXdp(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.logger.info(
            "+---------------------------------------------------------------------+"
        )
        self.logger.info(
            "|                    TestAfXdp: set_up_all                            |"
        )
        self.logger.info(
            "+---------------------------------------------------------------------+"
        )
        # self.verify(self.nic in ("I40E_40G-QSFP_A"), "the port can not run this suite")
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.header_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["udp"]

        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        # get the frame_sizes from cfg file
        if "frame_sizes" in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()["frame_sizes"]
        else:
            self.logger.info(
                f"you can config packets frame_sizes in file {self.suite_name}.cfg, like:"
            )
            self.logger.info("[suite]")
            self.logger.info("frame_sizes=[64, 128, 256, 512, 1024, 1518]")
        self.logger.info(f"configured frame_sizes={self.frame_sizes}")

        self.logger.info(
            f'you can config the traffic duration by setting the "TRAFFIC_DURATION" variable.'
        )
        self.traffic_duration = int(os.getenv("TRAFFIC_DURATION", "30"))
        self.logger.info(f"traffic duration is set to: {self.traffic_duration} sec.")

        self.out_path = "/tmp"
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.pktgen_helper = PacketGeneratorHelper()

        self.dut.restore_interfaces()
        self.irqs_set = self.dut.new_session(suite="irqs-set")
        self.irqs_set.send_expect("killall irqbalance", "# ")

        self.shell = self.dut.new_session(suite="shell")
        self.xdp_file = "/tmp/xdp_example"
        self.sec_proc = self.dut.new_session(suite="sec_proc")

        for numa in [0, 1]:
            cmd = f"echo 4096 > /sys/devices/system/node/node{numa}/hugepages/hugepages-2048kB/nr_hugepages"
            self.dut.send_expect(cmd, "# ", 120)

    def set_up(self):
        self.logger.info(
            "+---------------------------------------------------------------------+"
        )
        pass

    def set_port_queue(self, intf):
        # workaround for:
        #   https://lore.kernel.org/all/a52430d1e11c5cadcd08706bd6d8da3ea48e1c04.camel@coverfire.com/T/
        # Ciara:
        # Sometimes after launching TRex I see the interrupts for my dpdk-testpmd interface disappear:
        #   cat /proc/interrupts | grep fvl0 # returns nothing
        # As a result, I see nothing received on the dpdk-testpmd app.
        # in order to restore the interrupts I have to do the following:
        #    ifconfig enp134s0f0 down
        #    ifconfig enp134s0f0 up
        #    ethtool -L enp134s0f0 combined 2
        self.logger.info(f"initializing port '{intf}'")
        self.dut.send_expect(f"ifconfig {intf} down", "# ")
        self.dut.send_expect(f"ifconfig {intf} up", "# ")
        self.dut.send_expect(
            "ethtool -L %s combined %d" % (intf, self.nb_cores / self.port_num), "# "
        )

    def get_core_list(self):
        core_config = "1S/%dC/1T" % (
            self.nb_cores + 1 + max(self.port_num, self.vdev_num) * self.queue_number
        )
        self.core_list = self.dut.get_core_list(core_config, socket=self.ports_socket)

    def assign_port_core(self):
        if self.separate_cores:
            core_list = self.core_list[
                -max(self.port_num, self.vdev_num) * self.queue_number :
            ]
        else:
            core_list = self.core_list[
                : -max(self.port_num, self.vdev_num) * self.queue_number
            ][-max(self.port_num, self.vdev_num) * self.queue_number :]

        for i in range(self.port_num):
            intf = self.dut.ports_info[i]["port"].get_interface_name()
            cores = ",".join(
                core_list[i * self.queue_number : (i + 1) * self.queue_number]
            )
            if self.port_num == 1 and self.vdev_num == 2:
                cores = ",".join(core_list)
            command = "%s/set_irq_affinity %s %s" % ("/root", cores, intf)
            out = self.irqs_set.send_expect(command, "# ")
            self.verify(
                "No such file or directory" not in out,
                "can not find the set_irq_affinity in dut root "
                + "(see: https://github.com/dmarion/i40e/blob/master/scripts/set_irq_affinity)",
            )
            time.sleep(1)

    def get_vdev_list(self, shared_umem=1, start_queue=0, xdp_prog=""):
        vdev_list = []

        if self.port_num == 1:
            intf = self.dut.ports_info[0]["port"].get_interface_name()
            self.set_port_queue(intf)
            time.sleep(1)
            for i in range(self.vdev_num):
                vdev = ""
                if start_queue > 0:
                    vdev = "net_af_xdp%d,iface=%s,start_queue=%d" % (
                        i,
                        intf,
                        start_queue,
                    )
                else:
                    vdev = "net_af_xdp%d,iface=%s,start_queue=%d,queue_count=%d" % (
                        i,
                        intf,
                        i * self.queue_number,
                        self.queue_number,
                    )
                if shared_umem > 0:
                    vdev += f",shared_umem={shared_umem}"
                # When separate cores are used it is suggested that the 'busy_budget=0'
                # argument is added to the AF_XDP PMD vdev string.
                if self.separate_cores:
                    vdev += ",busy_budget=0"
                if xdp_prog != "":
                    vdev += f",xdp_prog={xdp_prog}"
                vdev_list.append(vdev)
        else:
            for i in range(self.port_num):
                vdev = ""
                intf = self.dut.ports_info[i]["port"].get_interface_name()
                self.set_port_queue(intf)
                vdev = "net_af_xdp%d,iface=%s" % (i, intf)
                if self.separate_cores:
                    vdev += ",busy_budget=0"
                vdev_list.append(vdev)

        return vdev_list

    def launch_testpmd(
        self,
        start_queue=0,
        xdp_prog="",
        fwd_mode="macswap",
        shared_umem=0,
        topology="",
        rss_ip=False,
        no_prefix=False,
    ):

        self.get_core_list()

        vdev = self.get_vdev_list(
            start_queue=start_queue,
            xdp_prog=xdp_prog,
            shared_umem=shared_umem,
        )

        if topology:
            topology = "--port-topology=%s" % topology
        if fwd_mode:
            fwd_mode = "--forward-mode=%s" % fwd_mode
        if rss_ip:
            rss_ip = "--rss-ip"
        else:
            rss_ip = ""

        if no_prefix:
            eal_params = f"--no-pci --vdev={vdev[0]}"
        else:
            eal_params = self.dut.create_eal_parameters(
                cores=self.core_list[
                    : -max(self.port_num, self.vdev_num) * self.queue_number
                ],
                vdevs=vdev,
                no_pci=True,
            )
        app_name = self.dut.apps_name["test-pmd"]
        command = f"{app_name} {eal_params} --log-level=pmd.net.af_xdp:8"
        command += f" -- -i --auto-start --nb-cores={self.nb_cores}"
        command += f" --rxq={self.queue_number} --txq={self.queue_number}"
        command += f" {fwd_mode} {rss_ip} {topology}"

        self.logger.info("start testpmd:")
        self.logger.info(command.replace("--", "\n\t--"))
        self.out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.info("dpdk-testpmd output:\n" + self.out)

    def launch_sec_testpmd(self):
        app_name = self.dut.apps_name["test-pmd"]
        command = f"{app_name} --no-pci"
        command += f" --proc-type=auto"
        command += f" --log-level=pmd.net.af_xdp:8"
        command += f" -- -i --auto-start"
        self.logger.info("start secondary testpmd:")
        self.logger.info(command.replace("--", "\n\t--"))
        self.out = self.sec_proc.send_expect(command, "testpmd> ", 120)
        self.logger.info("secondary dpdk-testpmd output:\n" + self.out)

    def create_table(self, index=1):
        self.table_header = [
            "Frame Size [B]",
            "Queue Number",
            "Port Throughput [Mpps]",
            "Port Linerate [%]",
        ]
        self.result_table_create(self.table_header)

    def update_table_info(self, *param):
        for each in param:
            self.result_table_add(each)

    def calculate_avg_throughput(self, frame_size, tgen_input, fwd_mode):
        """
        send packet and get the throughput
        """
        # set traffic option
        traffic_opt = {"delay": 2, "duration": self.traffic_duration}

        # clear streams before add new streams
        self.tester.scapy_execute()
        self.tester.pktgen.clear_streams()

        # run packet generator
        fields_config = {
            "ip": {
                "dst": {"action": "random"},
            },
        }
        self.logger.debug("Content of 'fields_config':")
        self.logger.debug(fields_config)

        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, 100, fields_config, self.tester.pktgen
        )
        _, pps = self.tester.pktgen.measure_throughput(
            stream_ids=streams, options=traffic_opt
        )

        Mpps = pps / 1000000.0

        if fwd_mode != "rxonly":
            self.verify(
                Mpps > 0, "can not receive packets of frame size %d" % (frame_size)
            )
        throughput = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))

        return Mpps, throughput

    def check_packets(self, port, queue):
        """
        check that given port has receive packets in a queue
        """
        info = re.findall("###### NIC extended statistics for port %d" % port, self.out)
        index = self.out.find(info[0])
        rx = re.search(f"rx_q{queue}_packets:\s*(\d*)", self.out[index:])
        tx = re.search(f"tx_q{queue}_packets:\s*(\d*)", self.out[index:])
        rx_packets = int(rx.group(1))
        tx_packets = int(tx.group(1))
        info = f"port {port} rx_q{queue}_packets: {rx_packets}, tx_q{queue}_packets: {tx_packets}"
        self.logger.info(f"verify non-zero: {info}")
        self.verify(
            rx_packets > 0 and tx_packets > 0,
            info,
        )

    def send_and_verify_throughput(self, pkt_type="", frame_sizes="", fwd_mode=""):
        if frame_sizes == "":
            frame_sizes = self.frame_sizes
        for frame_size in frame_sizes:
            self.logger.info(
                f"Running test {self.running_case} with frame size {frame_size}B."
            )
            result = [frame_size, self.queue_number]
            tgen_input = []
            for rx_port in range(0, max(self.port_num, self.vdev_num)):
                dst_mac = self.dut.get_mac_address(self.dut_ports[rx_port])
                pkt = Packet(pkt_len=frame_size)
                pkt.config_layers(
                    [
                        ("ether", {"dst": dst_mac}),
                        ("ipv4", {"dst": "192.168.%d.1" % (rx_port + 1), "proto": 255}),
                    ]
                )
                pcap = os.path.join(
                    self.out_path, f"af_xdp_{rx_port}_{frame_size}.pcap"
                )
                pkt.save_pcapfile(None, pcap)
                # tgen_input.append((rx_port, rx_port, pcap))
                tgen_input.append((rx_port, 0, pcap))
            self.logger.debug(
                f"tgen_input (port_num={self.port_num}, vdev_num={self.vdev_num}):"
            )
            self.logger.debug(tgen_input)

            Mpps, throughput = self.calculate_avg_throughput(
                frame_size, tgen_input, fwd_mode
            )
            self.logger.debug(f"Mpps: {Mpps}, throughput: {throughput}")
            result.append(Mpps)
            result.append(throughput)
            self.logger.debug(f"result: {result}")

            self.out = self.dut.send_expect("show port xstats all", "testpmd> ", 60)
            # self.out += '\n' + self.dut.send_expect("stop", "testpmd> ", 60)
            self.logger.info("dpdk-testpmd output:\n" + self.out)

            self.logger.info(
                f"port_num: {self.port_num}, queue_number: {self.queue_number}, vdev_num: {self.vdev_num}, nb_cores: {self.nb_cores}, separate_cores: {self.separate_cores}"
            )

            for port_index in range(0, max(self.port_num, self.vdev_num)):
                for queue_index in range(0, self.queue_number):
                    self.check_packets(port_index, queue_index)

            self.dut.send_expect("clear port xstats all", "testpmd> ", 60)
            # self.dut.send_expect("start", "testpmd> ", 60)

            self.update_table_info(result)

    def check_sharing_umem(self):
        """
        Check for the log: eth0,qid1 sharing UMEM
        """
        intf = self.dut.ports_info[0]["port"].get_interface_name()
        to_check = f"{intf},qid1 sharing UMEM"
        self.logger.info(f'check for the log: "{to_check}"')
        info = re.findall(f".*{to_check}", self.out)
        if len(info) > 0:
            self.logger.info(f'"{info[0]}" - confirmed')
        else:
            self.verify(False, '"<port>,qid1 sharing UMEM" - not found')

    def check_busy_polling(self):
        """
        Check for the log: Preferred busy polling not enabled
        """
        to_check = "Preferred busy polling not enabled"
        self.logger.info(f'check for the log: "{to_check}"')
        info = re.findall(f".*{to_check}", self.out)
        if len(info) > 0:
            self.logger.info(f'"{info[0]}" - confirmed')
        else:
            self.verify(False, f'"{to_check}" - not found')

    def check_xdp_program_loaded(self):
        """
        Check for the log: Successfully loaded XDP program xdp_example.o with fd <fd>
        """
        # load_custom_xdp_prog(): Successfully loaded XDP program /tmp/xdp_example.o with fd 227
        to_check = "Successfully loaded XDP program"
        self.logger.info(f'check for the log: "{to_check}"')
        info = re.findall(f".*{to_check}.*", self.out)
        if len(info) > 0:
            self.logger.info(f'"{info[0]}" - confirmed')
        else:
            self.verify(False, f'"{to_check}" - not found')

    def create_xdp_file(self, file_name=""):
        if file_name == "":
            file_name = f"{self.xdp_file}.c"
        program = [
            "#include <linux/bpf.h>",
            "#include <bpf/bpf_helpers.h>",
            "",
            'struct bpf_map_def SEC("maps") xsks_map = {',
            "        .type = BPF_MAP_TYPE_XSKMAP,",
            "        .max_entries = 64,",
            "        .key_size = sizeof(int),",
            "        .value_size = sizeof(int),",
            "};",
            "",
            "static unsigned int idx;",
            "",
            'SEC("xdp-example")',
            "",
            "int xdp_sock_prog(struct xdp_md *ctx)",
            "{",
            "        int index = ctx->rx_queue_index;",
            "",
            "        /* Drop every other packet */",
            "        if (idx++ % 2)",
            "                return XDP_DROP;",
            "        else",
            "                return bpf_redirect_map(&xsks_map, index, XDP_PASS);",
            "}",
        ]
        self.logger.info(f'creating XDP file "{file_name}":')
        with open(file_name, "w") as file:
            for line in program:
                file.write(f"{line}\n")
                self.logger.info(line)

    def compile_xdp_program(self, c_file="", o_file=""):
        if c_file == "":
            c_file = f"{self.xdp_file}.c"
        if o_file == "":
            o_file = f"{self.xdp_file}.o"
        self.logger.info(f'compile the XDP program "{c_file}":')
        out = self.shell.send_expect(
            f"clang -v -O2 -Wall -target bpf -c {c_file} -o {o_file}", "# "
        )
        self.logger.info(out)

    def check_sec_process(self):
        self.out = self.sec_proc.send_expect("show port info all", "testpmd> ", 60)
        self.logger.info("secondary dpdk-testpmd output:\n" + self.out)
        # ensure that you can see the port info of the net_af_xdp0 PMD from the primary process
        # like: "Device name: net_af_xdp0"
        to_check = "net_af_xdp0"
        self.logger.info(f'check for the log: "{to_check}"')
        info = re.findall(f".*{to_check}", self.out)
        if len(info) > 0:
            self.logger.info(f'"{info[0]}" - confirmed')
        else:
            self.verify(False, f'"{to_check}" - not found')

        self.sec_proc.send_expect("quit", "# ", 60)

    def set_busy_polling(self, non_busy_polling=False):
        self.logger.info("configuring preferred busy polling feature:")
        if non_busy_polling:
            # non busy polling tests: TC2,4,5,7,12
            napi_defer_hard_irqs = 0
            gro_flush_timeout = 0
        else:
            # busy polling tests: TC1,3,6,8,9,10,11,13,14,15
            napi_defer_hard_irqs = 2
            gro_flush_timeout = 200000

        for port in self.dut_ports:
            intf = self.dut.ports_info[port]["port"].get_interface_name()
            cmd = f"echo {napi_defer_hard_irqs} >> /sys/class/net/{intf}/napi_defer_hard_irqs"
            self.irqs_set.send_expect(cmd, "# ")
            cmd = f"echo {gro_flush_timeout} >> /sys/class/net/{intf}/gro_flush_timeout"
            self.irqs_set.send_expect(cmd, "# ")

    def test_perf_one_port_multiqueue_and_same_irqs(self):
        """
        Test case 1: multiqueue test with PMD and IRQs pinned to same cores
        """
        self.port_num = 1
        self.queue_number = 2
        self.vdev_num = 1
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.launch_testpmd()
        self.assign_port_core()
        self.send_and_verify_throughput()
        self.result_table_print()

    def test_perf_one_port_multiqueue_and_separate_irqs(self):
        """
        Test case 2: multiqueue test with PMD and IRQs are pinned to separate cores
        """
        self.port_num = 1
        self.queue_number = 2
        self.vdev_num = 1
        self.nb_cores = 2
        self.separate_cores = True

        self.set_busy_polling(non_busy_polling=True)
        self.create_table()
        self.launch_testpmd()
        self.assign_port_core()
        self.send_and_verify_throughput()
        self.result_table_print()

    def test_perf_one_port_multiqueues_with_two_vdev(self):
        """
        Test case 3: one port with two vdev and multi-queues test
        """
        self.port_num = 1
        self.queue_number = 4
        self.vdev_num = 2
        self.nb_cores = 8
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.launch_testpmd()
        self.assign_port_core()
        self.send_and_verify_throughput()
        self.result_table_print()

    def test_perf_one_port_single_queue_and_separate_irqs(self):
        """
        Test case 4: single port test with PMD and IRQs are pinned to separate cores
        """
        self.port_num = 1
        self.queue_number = 1
        self.vdev_num = 1
        self.nb_cores = 1
        self.separate_cores = True

        self.set_busy_polling(non_busy_polling=True)
        self.create_table()
        self.launch_testpmd()
        self.assign_port_core()
        self.send_and_verify_throughput()
        self.result_table_print()

    def test_perf_one_port_single_queue_with_two_vdev(self):
        """
        Test case 5: one port with two vdev and single queue test
        """
        self.port_num = 1
        self.queue_number = 1
        self.vdev_num = 2
        self.nb_cores = 2
        self.separate_cores = True

        self.set_busy_polling(non_busy_polling=True)
        self.create_table()
        self.launch_testpmd()
        self.assign_port_core()
        self.send_and_verify_throughput()
        self.result_table_print()

    def test_perf_two_port_and_same_irqs(self):
        """
        Test case 6: two ports test with PMD and IRQs pinned to same cores
        """
        self.port_num = 2
        self.queue_number = 1
        self.vdev_num = 2
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.launch_testpmd()
        self.assign_port_core()
        self.send_and_verify_throughput()
        self.result_table_print()

    def test_perf_two_port_and_separate_irqs(self):
        """
        Test case 7: two port test with PMD and IRQs are pinned to separate cores
        """
        self.port_num = 2
        self.queue_number = 1
        self.vdev_num = 2
        self.nb_cores = 2
        self.separate_cores = True

        self.set_busy_polling(non_busy_polling=True)
        self.create_table()
        self.launch_testpmd()
        self.assign_port_core()
        self.send_and_verify_throughput()
        self.result_table_print()

    def test_func_start_queue(self):
        """
        Test case 8: func_start_queue
        """
        self.port_num = 1
        self.queue_number = 1
        self.vdev_num = 1
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.launch_testpmd(start_queue=1)
        self.send_and_verify_throughput(frame_sizes=[64])

    def test_func_queue_count(self):
        """
        Test case 9: func_queue_count
        """
        self.port_num = 1
        self.queue_number = 2
        self.vdev_num = 1
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.launch_testpmd()
        self.send_and_verify_throughput(frame_sizes=[64])

    def test_func_shared_umem_1pmd(self):
        """
        Test case 10: func_shared_umem_1pmd
        """
        self.port_num = 1
        self.queue_number = 2
        self.vdev_num = 1
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.launch_testpmd(shared_umem=1)
        self.check_sharing_umem()
        self.send_and_verify_throughput(frame_sizes=[64])

    def test_func_shared_umem_2pmd(self):
        """
        Test case 11: func_shared_umem_2pmd
        """
        self.port_num = 1
        self.queue_number = 1
        self.vdev_num = 2
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.launch_testpmd(shared_umem=1)
        self.check_sharing_umem()
        self.send_and_verify_throughput(frame_sizes=[64])

    def test_func_busy_budget(self):
        """
        Test case 12: func_busy_budget
        """
        self.port_num = 1
        self.queue_number = 1
        self.vdev_num = 1
        self.nb_cores = 1
        self.separate_cores = True

        self.set_busy_polling(non_busy_polling=True)
        self.create_table()
        self.launch_testpmd()
        self.check_busy_polling()
        self.send_and_verify_throughput(frame_sizes=[64])

    def test_func_xdp_prog(self):
        """
        Test case 13: func_xdp_prog
        """
        self.port_num = 1
        self.queue_number = 1
        self.vdev_num = 1
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.create_xdp_file()
        self.compile_xdp_program()
        self.launch_testpmd(fwd_mode="", xdp_prog=f"{self.xdp_file}.o")
        self.check_xdp_program_loaded()
        self.send_and_verify_throughput(frame_sizes=[64])

    def test_func_xdp_prog_mq(self):
        """
        Test case 14: func_xdp_prog_mq
        """
        self.port_num = 1
        self.queue_number = 2
        self.vdev_num = 1
        self.nb_cores = 2
        self.separate_cores = False

        self.set_busy_polling()
        self.create_table()
        self.create_xdp_file()
        self.compile_xdp_program()
        self.launch_testpmd(fwd_mode="", xdp_prog=f"{self.xdp_file}.o")
        self.check_xdp_program_loaded()
        self.send_and_verify_throughput(frame_sizes=[64])

    def test_func_secondary_prog(self):
        """
        Test case 15: func_secondary_prog
        """
        self.port_num = 1
        self.queue_number = 1
        self.vdev_num = 1
        self.nb_cores = 1
        self.separate_cores = False

        self.set_busy_polling()
        self.launch_testpmd(no_prefix=True)
        self.launch_sec_testpmd()
        self.check_sec_process()

    def tear_down(self):
        self.dut.send_expect("quit", "# ", 60)
        self.sec_proc.send_expect("quit", "# ", 60)
        self.shell.send_expect(f"/bin/rm -f {self.xdp_file}*", "# ")
        self.logger.info(
            "+---------------------------------------------------------------------+"
        )
        self.logger.info(
            "|                          Test complete                              |"
        )
        self.logger.info(
            "+---------------------------------------------------------------------+"
        )
        self.logger.info("")

    def tear_down_all(self):
        self.dut.kill_all()

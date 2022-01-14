.. Copyright (c) <2019>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

=========================================
vhost-user/virtio pvp reconnect test plan
=========================================

Description
===========

Vhost-user uses Unix domain sockets for passing messages. This means the DPDK vhost-user implementation has two options:

* DPDK vhost-user acts as the server:
  DPDK will create a Unix domain socket server file and listen for connections from the frontend.
  Note, this is the default mode, and the only mode before DPDK v16.07.

* DPDK vhost-user acts as the client:
  Unlike the server mode, this mode doesn't create the socket file;it just tries to connect to the server (which responses to create the file instead).
  When the DPDK vhost-user application restarts, DPDK vhost-user will try to connect to the server again. This is how the "reconnect" feature works.
  When DPDK vhost-user restarts from an normal or abnormal exit (such as a crash), the client mode allows DPDK to establish the connection again. 
  Also, when DPDK vhost-user acts as the client, it will keep trying to reconnect to the server (QEMU) until it succeeds. 
  This is useful in two cases:

    * When QEMU is not started yet.
    * When QEMU restarts (for example due to a guest OS reboot).

Note that QEMU version v2.7 or above is required for split ring cases, and QEMU version v4.2.0 or above is required for packed ring cases.

Test Case1: vhost-user/virtio-pmd pvp split ring reconnect from vhost-user
==========================================================================
Flow: TG--> NIC --> Vhost --> Virtio --> Vhost--> NIC--> TG

1. Bind one port to vfio-pci, then launch vhost with client mode by below commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=1' -- -i --nb-cores=1
    testpmd>set fwd mac
    testpmd>start

2. Start VM with 1 virtio device, and set the qemu as server mode::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator, check if packets can be RX/TX with virtio-pmd::

    testpmd>show port stats all

5. On host, quit vhost-user, then re-launch the vhost-user with below command::

    testpmd>quit
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=1' -- -i --nb-cores=1
    testpmd>set fwd mac
    testpmd>start

6. Check if the reconnection can work, still send packets by packet generator, check if packets can be RX/TX with virtio-pmd::

    testpmd>show port stats all

Test Case2: vhost-user/virtio-pmd pvp split ring reconnect from VM
==================================================================
Flow: TG--> NIC --> Vhost --> Virtio --> Vhost--> NIC--> TG

1. Bind one port to vfio-pci, then launch vhost with client mode by below commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=1' -- -i --nb-cores=1
    testpmd>set fwd mac
    testpmd>start

2. Start VM with 1 virtio device, and set the qemu as server mode::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator, check if packets can be RX/TX with virtio-pmd::

    testpmd>show port stats all

5. Reboot the VM, rerun step2-step4, check the reconnection can be established.

Test Case3: vhost-user/virtio-pmd pvp split ring reconnect stability test
=========================================================================
Flow: TG--> NIC --> Vhost --> Virtio --> Vhost--> NIC--> TG

Similar as Test Case1, all steps are similar except step 5, 6.

5. Quit vhost-user, then re-launch, repeat it 5-8 times, check if the reconnect can work and ensure the traffic can continue.

6. Reboot VM, then re-launch VM, repeat it 3-5 times, check if the reconnect can work and ensure the traffic can continue.

Test Case 4: vhost-user/virtio-pmd pvp split ring with multi VMs reconnect from vhost-user
==========================================================================================

1. Bind one port to vfio-pci, launch the vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 12 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 12 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :11

3. On VM1, bind virtio1 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. On VM2, bind virtio2 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

6. On host, quit vhost-user, then re-launch the vhost-user with below command::

    testpmd>quit
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

7. Check if the reconnection can work, still send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

Test Case 5: vhost-user/virtio-pmd pvp split ring with multi VMs reconnect from VMs
===================================================================================

1. Bind one port to vfio-pci, launch the vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :11

3. On VM1, bind virtio1 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. On VM2, bind virtio2 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --port-topology=chain --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

6. Reboot the two VMs, rerun step2-step5.

7. Check if the reconnection can work, still send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

Test Case 6: vhost-user/virtio-pmd pvp split ring with multi VMs reconnect stability test
=========================================================================================

Similar as Test Case 4, all steps are similar except step 6, 7.

6. Quit vhost-user, then re-launch, repeat it 5-8 times, check if the reconnect can work and ensure the traffic can continue.

7. Reboot VMs, then re-launch VMs, repeat it 3-5 times, check if the reconnect can work and ensure the traffic can continue.

Test Case 7: vhost-user/virtio-net VM2VM split ring reconnect from vhost-user
=============================================================================
Flow: Virtio-net1 --> Vhost-user --> Virtio-net2

1. Launch the vhost by below commands, enable the client mode and tso::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

3. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :11

4. Set virtio device IP and run arp protocal on two VMs::

    VM1: ifconfig ens4 1.1.1.2
    VM2: ifconfig ens4 1.1.1.3
    VM1: arp -s 1.1.1.3 52:54:00:00:00:02
    VM2: arp -s 1.1.1.2 52:54:00:00:00:01

5. Run iperf on VM1 and VM2, check the tso enabled performance for 1 min::

    VM1: iperf -s -i 1 -t 60
    VM2: iperf -c 1.1.1.2 -t 60 -i 1

6. Kill the vhost-user, then re-launch the vhost-user::

    testpmd>quit
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

7. Rerun step5, ensure the vhost-user can reconnect to VM again, and the iperf traffic can be continue.

Test Case 8: vhost-user/virtio-net VM2VM split ring reconnect from VMs
======================================================================
Flow: Virtio-net1 --> Vhost-user --> Virtio-net2

1. Launch the vhost by below commands, enable the client mode and tso::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

3. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6002-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f \
    -net user,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024 \
    -vnc :11

4. Set virtio device IP and run arp protocal on two VMs::

    VM1: ifconfig ens4 1.1.1.2
    VM2: ifconfig ens4 1.1.1.3
    VM1: arp -s 1.1.1.3 52:54:00:00:00:02
    VM2: arp -s 1.1.1.2 52:54:00:00:00:01

5. Run iperf on VM1 and VM2, check the tso enabled performance for 1 min::

    VM1: iperf -s -i 1 -t 60
    VM2: iperf -c 1.1.1.2 -t 60 -i 1

6. Reboot VM1 and VM2, rerun step3-step5, ensure the vhost-user can reconnect to VM again, and the iperf traffic can be continue.

Test Case 9: vhost-user/virtio-net VM2VM split ring reconnect stability test
============================================================================
Flow: Virtio-net1 --> Vhost-user --> Virtio-net2

Similar as Test Case 7, all steps are similar except step 6.

6. Quit vhost-user, then re-launch, repeat it 5-8 times, check if the reconnect can work and ensure the traffic can continue.

7. Reboot two VMs, then re-launch VMs, repeat it 3-5 times, check if the reconnect can work and ensure the traffic can continue.

Test Case10: vhost-user/virtio-pmd pvp packed ring reconnect from vhost-user
============================================================================
Flow: TG--> NIC --> Vhost --> Virtio --> Vhost--> NIC--> TG

1. Bind one port to vfio-pci, then launch vhost with client mode by below commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=1' -- -i --nb-cores=1
    testpmd>set fwd mac
    testpmd>start

2. Start VM with 1 virtio device, and set the qemu as server mode::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator, check if packets can be RX/TX with virtio-pmd::

    testpmd>show port stats all

5. On host, quit vhost-user, then re-launch the vhost-user with below command::

    testpmd>quit
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=1' -- -i --nb-cores=1
    testpmd>set fwd mac
    testpmd>start

6. Check if the reconnection can work, still send packets by packet generator, check if packets can be RX/TX with virtio-pmd::

    testpmd>show port stats all

Test Case11: vhost-user/virtio-pmd pvp packed ring reconnect from VM
====================================================================
Flow: TG--> NIC --> Vhost --> Virtio --> Vhost--> NIC--> TG

1. Bind one port to vfio-pci, then launch vhost with client mode by below commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --vdev 'eth_vhost0,iface=vhost-net,client=1,queues=1' -- -i --nb-cores=1
    testpmd>set fwd mac
    testpmd>start

2. Start VM with 1 virtio device, and set the qemu as server mode::

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :10

3. On VM, bind virtio net to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. Send packets by packet generator, check if packets can be RX/TX with virtio-pmd::

    testpmd>show port stats all

5. Reboot the VM, rerun step2-step4, check the reconnection can be established.

Test Case12: vhost-user/virtio-pmd pvp packed ring reconnect stability test
===========================================================================
Flow: TG--> NIC --> Vhost --> Virtio --> Vhost--> NIC--> TG

Similar as Test Case1, all steps are similar except step 5, 6.

5. Quit vhost-user, then re-launch, repeat it 5-8 times, check if the reconnect can work and ensure the traffic can continue.

6. Reboot VM, then re-launch VM, repeat it 3-5 times, check if the reconnect can work and ensure the traffic can continue.

Test Case 13: vhost-user/virtio-pmd pvp packed ring with multi VMs reconnect from vhost-user
============================================================================================

1. Bind one port to vfio-pci, launch the vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 12 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :11

3. On VM1, bind virtio1 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. On VM2, bind virtio2 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

6. On host, quit vhost-user, then re-launch the vhost-user with below command::

    testpmd>quit
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

7. Check if the reconnection can work, still send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

Test Case 14: vhost-user/virtio-pmd pvp packed ring with multi VMs reconnect from VMs
=====================================================================================

1. Bind one port to vfio-pci, launch the vhost by below command::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --file-prefix=vhost --vdev 'net_vhost0,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

2. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 12 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :11

3. On VM1, bind virtio1 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

4. On VM2, bind virtio2 to vfio-pci and run testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i --port-topology=chained --port-topology=chain --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>set fwd mac
    testpmd>start

5. Send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

6. Reboot the two VMs, rerun step2-step5.

7. Check if the reconnection can work, still send packets by packet generator, check if packets can be RX/TX with two virtio-pmds in two VMs::

    testpmd>show port stats all

Test Case 15: vhost-user/virtio-pmd pvp packed ring with multi VMs reconnect stability test
===========================================================================================

Similar as Test Case 4, all steps are similar except step 6, 7.

6. Quit vhost-user, then re-launch, repeat it 5-8 times, check if the reconnect can work and ensure the traffic can continue.

7. Reboot VMs, then re-launch VMs, repeat it 3-5 times, check if the reconnect can work and ensure the traffic can continue.

Test Case 16: vhost-user/virtio-net VM2VM packed ring reconnect from vhost-user
===============================================================================
Flow: Virtio-net1 --> Vhost-user --> Virtio-net2

1. Launch the vhost by below commands, enable the client mode and tso::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

3. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 12 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :11

4. Set virtio device IP and run arp protocal on two VMs::

    VM1: ifconfig ens4 1.1.1.2
    VM2: ifconfig ens4 1.1.1.3
    VM1: arp -s 1.1.1.3 52:54:00:00:00:02
    VM2: arp -s 1.1.1.2 52:54:00:00:00:01

5. Run iperf on VM1 and VM2, check the tso enabled performance for 1 min::

    VM1: iperf -s -i 1 -t 60
    VM2: iperf -c 1.1.1.2 -t 60 -i 1

6. Kill the vhost-user, then re-launch the vhost-user::

    testpmd>quit
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

7. Rerun step5, ensure the vhost-user can reconnect to VM again, and the iperf traffic can be continue.

Test Case 17: vhost-user/virtio-net VM2VM packed ring reconnect from VMs
========================================================================
Flow: Virtio-net1 --> Vhost-user --> Virtio-net2

1. Launch the vhost by below commands, enable the client mode and tso::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x30 -n 4 --no-pci --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,client=1,queues=1' --vdev 'net_vhost1,iface=vhost-net1,client=1,queues=1'  -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

3. Launch VM1 and VM2::

    qemu-system-x86_64 -name vm1 -enable-kvm -cpu host -smp 2 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6000-:22 \
    -chardev socket,id=char0,path=./vhost-net,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :10

    qemu-system-x86_64 -name vm2 -enable-kvm -cpu host -smp 12 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu16-1.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6001-:22 \
    -chardev socket,id=char0,path=./vhost-net1,server \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,packed=on \
    -vnc :11

4. Set virtio device IP and run arp protocal on two VMs::

    VM1: ifconfig ens4 1.1.1.2
    VM2: ifconfig ens4 1.1.1.3
    VM1: arp -s 1.1.1.3 52:54:00:00:00:02
    VM2: arp -s 1.1.1.2 52:54:00:00:00:01

5. Run iperf on VM1 and VM2, check the tso enabled performance for 1 min::

    VM1: iperf -s -i 1 -t 60
    VM2: iperf -c 1.1.1.2 -t 60 -i 1

6. Reboot VM1 and VM2, rerun step3-step5, ensure the vhost-user can reconnect to VM again, and the iperf traffic can be continue.

Test Case 18: vhost-user/virtio-net VM2VM packed ring reconnect stability test
==============================================================================
Flow: Virtio-net1 --> Vhost-user --> Virtio-net2

Similar as Test Case 7, all steps are similar except step 6.

6. Quit vhost-user, then re-launch, repeat it 5-8 times, check if the reconnect can work and ensure the traffic can continue.

7. Reboot two VMs, then re-launch VMs, repeat it 3-5 times, check if the reconnect can work and ensure the traffic can continue.
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

========================================
vhost event idx interrupt mode test plan
========================================

Description
===========

Vhost event idx interrupt need test with l3fwd-power sample, send small packets
from virtio-net to vhost side，check vhost-user cores can be wakeup status，and
vhost-user cores should be sleep status after stop sending packets from virtio
side.For packed virtqueue test, need using qemu version > 4.2.0.


Test flow
=========

Virtio-net --> Vhost-user

Test Case 1: wake up split ring vhost-user core with event idx interrupt mode
=============================================================================

1. Launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 1 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1)"

2. Launch VM1 with server mode::

     taskset -c 17-18 qemu-system-x86_64 -name us-vhost-vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on -vnc :12

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1)"

4. On VM, set ip for virtio device and send packets to vhost by cmds::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. Check vhost related core is waked up by reading l3fwd-power log.

Test Case 2: wake up split ring vhost-user cores with event idx interrupt mode 16 queues test
=============================================================================================

1. Launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

2. Launch VM1 with server mode::

     taskset -c 17-18 qemu-system-x86_64 -name us-vhost-vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,mq=on,vectors=40 -vnc :12

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

4. Set vitio-net with 16 quques and give vitio-net ip address::

    ethtool -L [ens3] combined 16    # [ens3] is the name of virtio-net
    ifconfig [ens3] 1.1.1.1

5. Send packets with different IPs from virtio-net, notice to bind each vcpu to different send packets process::

    taskset -c 0 ping 1.1.1.2
    taskset -c 1 ping 1.1.1.3
    taskset -c 2 ping 1.1.1.4
    taskset -c 3 ping 1.1.1.5
    taskset -c 4 ping 1.1.1.6
    taskset -c 5 ping 1.1.1.7
    taskset -c 6 ping 1.1.1.8
    taskset -c 7 ping 1.1.1.9
    taskset -c 8 ping 1.1.1.2
    taskset -c 9 ping 1.1.1.2
    taskset -c 10 ping 1.1.1.2
    taskset -c 11 ping 1.1.1.2
    taskset -c 12 ping 1.1.1.2
    taskset -c 13 ping 1.1.1.2
    taskset -c 14 ping 1.1.1.2
    taskset -c 15 ping 1.1.1.2

6. Check vhost related cores are waked up with l3fwd-power log, such as following::

    L3FWD_POWER: lcore 0 is waked up from rx interrupt on port 0 queue 0
    ...
    ...
    L3FWD_POWER: lcore 15 is waked up from rx interrupt on port 0 queue 15

Test Case 3: wake up split ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode
=========================================================================================================

1. Launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1' \
    -- -p 0x3 \
    --parse-ptype 1 \
    --config "(0,0,1),(1,0,2)"

2. Launch VM1 and VM2 with server mode::

     taskset -c 33 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
     -chardev socket,server,id=char0,path=/vhost-net0 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on -vnc :10 -daemonize

     taskset -c 34 \
     qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910-2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=/vhost-net1 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,csum=on -vnc :11 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1' \
    -- -p 0x3 \
    --parse-ptype 1 \
    --config "(0,0,1),(1,0,2)"

4. On VM1, set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. On VM2, also set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.4
    #[ens3] is the virtual device name
    ping 1.1.1.5
    #send packets to vhost

6. Check vhost related cores are waked up with l3fwd-power log.

Test Case 4: wake up packed ring vhost-user core with event idx interrupt mode
==============================================================================

1. Launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1)"

2. Launch VM1 with server mode::

     taskset -c 33 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=/vhost-net0 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on,packed=on -vnc :10 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1)"

4. On VM, set ip for virtio device and send packets to vhost by cmds::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. Check vhost related core is waked up by reading l3fwd-power log.

Test Case 5: wake up packed ring vhost-user cores with event idx interrupt mode 16 queues test
==============================================================================================

1. Launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

2. Launch VM1 with server mode::

     taskset -c 17-18 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu1910.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=/vhost-net0 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on,mq=on,packed=on,vectors=40 -vnc :10 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

4. Set vitio-net with 16 quques and give vitio-net ip address::

    ethtool -L [ens3] combined 16    # [ens3] is the name of virtio-net
    ifconfig [ens3] 1.1.1.1

5. Send packets with different IPs from virtio-net, notice to bind each vcpu to different send packets process::

    taskset -c 0 ping 1.1.1.2
    taskset -c 1 ping 1.1.1.3
    taskset -c 2 ping 1.1.1.4
    taskset -c 3 ping 1.1.1.5
    taskset -c 4 ping 1.1.1.6
    taskset -c 5 ping 1.1.1.7
    taskset -c 6 ping 1.1.1.8
    taskset -c 7 ping 1.1.1.9
    taskset -c 8 ping 1.1.1.2
    taskset -c 9 ping 1.1.1.2
    taskset -c 10 ping 1.1.1.2
    taskset -c 11 ping 1.1.1.2
    taskset -c 12 ping 1.1.1.2
    taskset -c 13 ping 1.1.1.2
    taskset -c 14 ping 1.1.1.2
    taskset -c 15 ping 1.1.1.2

6. Check vhost related cores are waked up with l3fwd-power log, such as following::

    L3FWD_POWER: lcore 0 is waked up from rx interrupt on port 0 queue 0
    ...
    ...
    L3FWD_POWER: lcore 15 is waked up from rx interrupt on port 0 queue 15

Test Case 6: wake up packed ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode
==========================================================================================================

1. Launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1' \
    -- -p 0x3 \
    --parse-ptype 1 \
    --config "(0,0,1),(1,0,2)"

2. Launch VM1 and VM2 with server mode::

     taskset -c 33 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=/vhost-net0 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on,packed=on -vnc :10 -daemonize

     taskset -c 34 \
     qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910-2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=/vhost-net1 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,csum=on,packed=on -vnc :11 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 \
    -n 4 --no-pci\
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1' \
    -- -p 0x3 \
    --parse-ptype 1 \
    --config "(0,0,1),(1,0,2)"

4. On VM1, set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. On VM2, also set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.4
    #[ens3] is the virtual device name
    ping 1.1.1.5
    #send packets to vhost

6. Check vhost related cores are waked up with l3fwd-power log.

Test Case 7: wake up split ring vhost-user cores with event idx interrupt mode and cbdma enabled 16 queues test
===============================================================================================================

1. Bind 16 cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

2. Launch VM1 with server mode::

     taskset -c 17-18 qemu-system-x86_64 -name us-vhost-vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,mq=on,vectors=40 -vnc :12

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

4. Set vitio-net with 16 quques and give vitio-net ip address::

    ethtool -L [ens3] combined 16    # [ens3] is the name of virtio-net
    ifconfig [ens3] 1.1.1.1

5. Send packets with different IPs from virtio-net, notice to bind each vcpu to different send packets process::

    taskset -c 0 ping 1.1.1.2
    taskset -c 1 ping 1.1.1.3
    taskset -c 2 ping 1.1.1.4
    taskset -c 3 ping 1.1.1.5
    taskset -c 4 ping 1.1.1.6
    taskset -c 5 ping 1.1.1.7
    taskset -c 6 ping 1.1.1.8
    taskset -c 7 ping 1.1.1.9
    taskset -c 8 ping 1.1.1.2
    taskset -c 9 ping 1.1.1.2
    taskset -c 10 ping 1.1.1.2
    taskset -c 11 ping 1.1.1.2
    taskset -c 12 ping 1.1.1.2
    taskset -c 13 ping 1.1.1.2
    taskset -c 14 ping 1.1.1.2
    taskset -c 15 ping 1.1.1.2

6. Check vhost related cores are waked up with l3fwd-power log, such as following::

    L3FWD_POWER: lcore 0 is waked up from rx interrupt on port 0 queue 0
    ...
    ...
    L3FWD_POWER: lcore 15 is waked up from rx interrupt on port 0 queue 15

Test Case 8: wake up split ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode and cbdma enabled test
================================================================================================================================

1. Bind two cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1,dmas=[txq0@00:04.0]' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1,dmas=[txq0@80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

2. Launch VM1 and VM2 with server mode::

     taskset -c 33 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
     -chardev socket,server,id=char0,path=/vhost-net0 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on -vnc :10 -daemonize

     taskset -c 34 \
     qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910-2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=/vhost-net1 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,csum=on -vnc :11 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1,dmas=[txq0@00:04.0]' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1,dmas=[txq0@80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

4. On VM1, set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. On VM2, also set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.4
    #[ens3] is the virtual device name
    ping 1.1.1.5
    #send packets to vhost

6. Check vhost related cores are waked up with l3fwd-power log.

Test Case 9: wake up packed ring vhost-user cores with event idx interrupt mode and cbdma enabled 16 queues test
================================================================================================================

1. Bind 16 cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

2. Launch VM1 with server mode::

     taskset -c 17-18 qemu-system-x86_64 -name us-vhost-vm1 -enable-kvm -cpu host -smp 1 -m 4096 \
    -object memory-backend-file,id=mem,size=4096M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img  \
    -chardev socket,path=/tmp/vm2_qga0.sock,server,nowait,id=vm2_qga0 -device virtio-serial \
    -device virtserialport,chardev=vm2_qga0,name=org.qemu.guest_agent.2 -daemonize \
    -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
    -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
    -chardev socket,id=char0,path=./vhost-net0 \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=16 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:02,disable-modern=false,mrg_rxbuf=on,csum=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,mq=on,vectors=40,packed=on -vnc :12

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-16 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7]' \
    -- -p 0x1 --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

4. Set vitio-net with 16 quques and give vitio-net ip address::

    ethtool -L [ens3] combined 16    # [ens3] is the name of virtio-net
    ifconfig [ens3] 1.1.1.1

5. Send packets with different IPs from virtio-net, notice to bind each vcpu to different send packets process::

    taskset -c 0 ping 1.1.1.2
    taskset -c 1 ping 1.1.1.3
    taskset -c 2 ping 1.1.1.4
    taskset -c 3 ping 1.1.1.5
    taskset -c 4 ping 1.1.1.6
    taskset -c 5 ping 1.1.1.7
    taskset -c 6 ping 1.1.1.8
    taskset -c 7 ping 1.1.1.9
    taskset -c 8 ping 1.1.1.2
    taskset -c 9 ping 1.1.1.2
    taskset -c 10 ping 1.1.1.2
    taskset -c 11 ping 1.1.1.2
    taskset -c 12 ping 1.1.1.2
    taskset -c 13 ping 1.1.1.2
    taskset -c 14 ping 1.1.1.2
    taskset -c 15 ping 1.1.1.2

6. Check vhost related cores are waked up with l3fwd-power log, such as following::

    L3FWD_POWER: lcore 0 is waked up from rx interrupt on port 0 queue 0
    ...
    ...
    L3FWD_POWER: lcore 15 is waked up from rx interrupt on port 0 queue 15

Test Case 10: wake up packed ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode and cbdma enabled test
==================================================================================================================================

1. Bind two cbdma ports to vfio-pci driver, then launch l3fwd-power example app with client mode::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1,dmas=[txq0@00:04.0]' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1,dmas=[txq0@80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

2. Launch VM1 and VM2 with server mode::

     taskset -c 33 \
     qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6003-:22 \
     -chardev socket,server,id=char0,path=/vhost-net0 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on,packed=on -vnc :10 -daemonize

     taskset -c 34 \
     qemu-system-x86_64 -name us-vhost-vm2 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=1,sockets=1 -drive file=/home/osimg/ubuntu1910-2.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=nttsip1 \
     -netdev user,id=nttsip1,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,server,id=char0,path=/vhost-net1 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:02,netdev=mynet1,csum=on,packed=on -vnc :11 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power  -l 1-2 -n 4 --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1,dmas=[txq0@00:04.0]' \
    --vdev 'eth_vhost1,iface=/vhost-net1,queues=1,client=1,dmas=[txq0@80:04.0]' \
    -- -p 0x3 --parse-ptype 1 --config "(0,0,1),(1,0,2)"

4. On VM1, set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.2
    #[ens3] is the virtual device name
    ping 1.1.1.3
    #send packets to vhost

5. On VM2, also set ip for virtio device and send packets to vhost::

    ifconfig [ens3] 1.1.1.4
    #[ens3] is the virtual device name
    ping 1.1.1.5
    #send packets to vhost

6. Check vhost related cores are waked up with l3fwd-power log.

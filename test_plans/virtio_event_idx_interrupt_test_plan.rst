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
virtio event idx interrupt mode test plan
=========================================

Description
===========

This feature is to suppress interrupts for performance improvement, need compare
interrupt times with and without virtio event idx enabled. Also need cover driver
reload test. For packed virtqueue test, need using qemu version > 4.2.0.

Test flow
=========

TG --> NIC --> Vhost-user --> Virtio-net

Test Case 1: Compare interrupt times with and without split ring virtio event idx enabled
=========================================================================================

1. Bind one nic port to igb_uio, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP::

    ifconfig [ens3] 1.1.1.2  # [ens3] is the name of virtio-net

4. Send 10M packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. Disable virtio event idx feature and rerun step1 ~ step4.

6. Compare interrupt times between virtio event_idx enabled and virtio event_idx disabled.

Test Case 2: Split ring virtio-pci driver reload test
=====================================================

1. Bind one nic port to igb_uio, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP, send 10M packets from packet generator to nic then check virtio device can receive packets::

    ifconfig [ens3] 1.1.1.2      # [ens3] is the name of virtio-net
    tcpdump -i [ens3]

4. Reload virtio-net driver by below cmds::

    ifconfig [ens3] down
    ./dpdk-devbind.py -u [00:03.0]   # [00:03.0] is the pci addr of virtio-net
    ./dpdk-devbind.py -b virtio-pci [00:03.0]

5. Check virtio device can receive packets again::

    ifconfig [ens3] 1.1.1.2
    tcpdump -i [ens3]

6. Rerun step4 and step5 100 times to check event idx workable after driver reload.

Test Case 3: Wake up split ring virtio-net cores with event idx interrupt mode 16 queues test
=============================================================================================

1. Bind one nic port to igb_uio, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -l 1-17 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=16' -- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on \
     -vnc :12 -daemonize

3. On VM1, give virtio device ip addr and enable vitio-net with 16 quques::

    ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
    ethtool -L [ens3] combined 16

4. Send 10M different ip addr packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. After two hours stress test, stop and restart testpmd, check each queue has new packets coming::

    testpmd>stop
    testpmd>start
    testpmd>stop

Test Case 4: Compare interrupt times with and without packed ring virtio event idx enabled
==========================================================================================

1. Bind one nic port to igb_uio, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i
    --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP::

    ifconfig [ens3] 1.1.1.2  # [ens3] is the name of virtio-net

4. Send 10M packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. Disable virtio event idx feature and rerun step1 ~ step4.

6. Compare interrupt times between virtio event_idx enabled and virtio event_idx disabled.

Test Case 5: Packed ring virtio-pci driver reload test
======================================================

1. Bind one nic port to igb_uio, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -c 0xF0000000 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=1' -- -i --nb-cores=1 --txd=1024 --rxd=1024
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=2,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

3. On VM1, set virtio device IP, send 10M packets from packet generator to nic then check virtio device can receive packets::

    ifconfig [ens3] 1.1.1.2      # [ens3] is the name of virtio-net
    tcpdump -i [ens3]

4. Reload virtio-net driver by below cmds::

    ifconfig [ens3] down
    ./dpdk-devbind.py -u [00:03.0]   # [00:03.0] is the pci addr of virtio-net
    ./dpdk-devbind.py -b virtio-pci [00:03.0]

5. Check virtio device can receive packets again::

    ifconfig [ens3] 1.1.1.2
    tcpdump -i [ens3]

6. Rerun step4 and step5 100 times to check event idx workable after driver reload.

Test Case 6: Wake up packed ring virtio-net cores with event idx interrupt mode 16 queues test
==============================================================================================

1. Bind one nic port to igb_uio, then launch the vhost sample by below commands::

    rm -rf vhost-net*
    ./testpmd -l 1-17 -n 4 --file-prefix=vhost --vdev 'net_vhost,iface=vhost-net,queues=16' -- -i --nb-cores=16 --txd=1024 --rxd=1024 --rxq=16 --txq=16
    testpmd>start

2. Launch VM::

    taskset -c 32-33 \
    qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc \
     -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu16.img  \
     -monitor unix:/tmp/vm2_monitor.sock,server,nowait -net nic,macaddr=00:00:00:08:e8:aa,addr=1f -net user,hostfwd=tcp:127.0.0.1:6004-:22 \
     -chardev socket,id=char0,path=./vhost-net -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16 \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=40,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on,packed=on \
     -vnc :12 -daemonize

3. On VM1, give virtio device ip addr and enable vitio-net with 16 quques::

    ifconfig [ens3] 1.1.1.2           # [ens3] is the name of virtio-net
    ethtool -L [ens3] combined 16

4. Send 10M different ip addr packets from packet generator to nic, check virtio-net interrupt times by below cmd in VM::

    cat /proc/interrupts

5. After two hours stress test, stop and restart testpmd, check each queue has new packets coming::

    testpmd>stop
    testpmd>start
    testpmd>stop

Test Case 7: wake up vhost-user core with event idx interrupt mode and cbdma enabled
====================================================================================

1. Launch l3fwd-power example app with client mode::

    ./examples/l3fwd-power/build/l3fwd-power -l 1 -w 80:04.0 \
    -n 4 \
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1,dmas=[txq0@80:04.0],dmathr=1024' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1)"

2. Launch VM1 with server mode::

     taskset -c 33 \
     /home/qemu-install/qemu-3.0/bin/qemu-system-x86_64 -name us-vhost-vm1 \
     -cpu host -enable-kvm -smp cores=1,sockets=1 -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -drive file=/home/osimg/ubuntu1910.img -netdev user,id=yinan,hostfwd=tcp:127.0.0.1:6006-:22 -device e1000,netdev=yinan \
     -chardev socket,server,id=char0,path=/vhost-net0 \
     -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
     -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on -vnc :10 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./examples/l3fwd-power/build/l3fwd-power -l 1 -w 80:04.0 \
    -n 4 \
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=1,client=1,dmas=[txq0@80:04.0],dmathr=1024' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1)"

3.  On VM, set ip for virtio device and send packets to vhost::

      ifconfig [ens3] 1.1.1.2     # [ens3] is the name of virtio-net
      ping 1.1.1.3

4. Check vhost related core is waked up by reading l3fwd-power log.

Test Case 8: wake up vhost-user cores with event idx interrupt mode and cbdma enabled 16 queues test 
====================================================================================================

1. Launch l3fwd-power example app with client mode::

    ./examples/l3fwd-power/build/l3fwd-power -l 1-16 \
    -n 4 \
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7],dmathr=1024' \
    -- -p 0x1 \
    --parse-ptype 1 \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

2. Launch VM1 with server mode::

    taskset -c 17-18 /home/qemu-install/qemu-3.0/bin/qemu-system-x86_64 -name us-vhost-vm1      -cpu host -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on -numa node,memdev=mem -mem-prealloc -netdev user,id=yinan,hostfwd=tcp:127.0.0.1:6001-:22 -device e1000,netdev=yinan      -smp cores=16,sockets=1 -drive file=/home/osimg/ubuntu1910.img       -chardev socket,server,id=char0,path=/vhost-net0      -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=16      -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,csum=on,mq=on,vectors=40 -vnc :10 -daemonize

3. Relauch l3fwd-power sample for port up::

    ./examples/l3fwd-power/build/l3fwd-power -l 1-16 \
    -n 4 \
    --log-level=9 \
    --vdev 'eth_vhost0,iface=/vhost-net0,queues=16,client=1,dmas=[txq0@80:04.0;txq1@80:04.1;txq2@80:04.2;txq3@80:04.3;txq4@80:04.4;txq5@80:04.5;txq6@80:04.6;txq7@80:04.7;txq8@00:04.0;txq9@00:04.1;txq10@00:04.2;txq11@00:04.3;txq12@00:04.4;txq13@00:04.5;txq14@00:04.6;txq15@00:04.7],dmathr=1024' \
    -- -p 0x1 \
    --parse-ptype 1 --interrupt-only \
    --config "(0,0,1),(0,1,2),(0,2,3),(0,3,4),(0,4,5),(0,5,6),(0,6,7),(0,7,8),(0,8,9),(0,9,10),(0,10,11),(0,11,12),(0,12,13),(0,13,14),(0,14,15),(0,15,16)"

3.  Set vitio-net with 16 quques and give vitio-net ip address::

      ethtool -L ens4 combined 16    # [ens3] is the name of virtio-net
      ifconfig ens4 1.1.1.1

4.  Send packets with different IPs from virtio-net, notice to bind each vcpu to different send packets process::

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

5.  Check vhost related cores are waked up with l3fwd-power log, such as following::

      L3FWD_POWER: lcore 0 is waked up from rx interrupt on port 0 queue 0
      .....
      .....
      L3FWD_POWER: lcore 15 is waked up from rx interrupt on port 0 queue 15

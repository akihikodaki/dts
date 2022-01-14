.. Copyright (c) <2016-2017>, Intel Corporation
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

===============================
Vhost User Live Migration Tests
===============================

This feature is to make sure vhost user live migration works based on testpmd.
For packed virtqueue test, need using qemu version > 4.2.0.

Prerequisites
-------------

HW setup

1. Connect three ports to one switch, these three ports are from Host, Backup
   host and tester. Ensure the tester can send packets out, then host/backup server ports
   can receive these packets.
2. Better to have 2 similar machine with the same CPU and OS.

NFS configuration

1. Make sure host nfsd module updated to v4 version(v2 not support file > 4G)

2. Start nfs service and export nfs to backup host IP::

    host# service rpcbind start
    host# service nfs-server start
    host# service nfs-mountd start
    host# systemctrl stop firewalld.service
    host# vim /etc/exports
    host# /home/osimg/live_mig backup-host-ip(rw,sync,no_root_squash)

3. Mount host nfs folder on backup host::

    backup# mount -t nfs -o nolock,vers=4  host-ip:/home/osimg/live_mig /mnt/nfs

Test Case 1: migrate with split ring virtio-pmd
===============================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    host server# testpmd>start

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server # ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    backup server # testpmd>start

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and scp the DPDK folder from host to VM::

    host server# ssh -p 5555 127.0.0.1
    host server# scp -P 5555 -r <dpdk_folder>/ 127.0.0.1:/root

7. Run testpmd in VM::

    host VM# cd /root/<dpdk_folder>
    host VM# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    host VM# ninja -C x86_64-native-linuxapp-gcc
    host VM# modprobe uio
    host VM# insmod ./x86_64-native-linuxapp-gcc/kmod/vfio-pci.ko
    host VM# ./usertools/dpdk-devbind.py --bind=vfio-pci 00:03.0
    host VM# echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
    host VM# screen -S vm
    host VM# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i
    host VM# testpmd>set fwd rxonly
    host VM# testpmd>set verbose 1
    host VM# testpmd>start

8. Send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

9. Check the virtio-pmd can receive the packet, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

10. Start Live migration, ensure the traffic is continuous::

     host server # telnet localhost 3333
     host server # (qemu)migrate -d tcp:backup server:4444
     host server # (qemu)info migrate
     host server # Check if the migrate is active and not failed.

11. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

12. After live migration, go to the backup server and check if the virtio-pmd can continue to receive packets::

     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm

Test Case 2: migrate with split ring virtio-pmd enabled
=================================================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port,note not start vhost port before launching qemu::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server # ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and scp the DPDK folder from host to VM::

    host server# ssh -p 5555 127.0.0.1
    host server# scp -P 5555 -r <dpdk_folder>/ 127.0.0.1:/root

7. Run testpmd in VM::

    host VM# cd /root/<dpdk_folder>
    host VM# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    host VM# ninja -C x86_64-native-linuxapp-gcc
    host VM# modprobe uio
    host VM# insmod ./x86_64-native-linuxapp-gcc/kmod/vfio-pci.ko
    host VM# ./usertools/dpdk-devbind.py --bind=vfio-pci 00:03.0
    host VM# echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
    host VM# screen -S vm
    host VM# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i
    host VM# testpmd>set fwd rxonly
    host VM# testpmd>set verbose 1
    host VM# testpmd>start

8. Start vhost testpmd on host and send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    host# testpmd>start
    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

9. Check the virtio-pmd can receive packets, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

10. Start Live migration, ensure the traffic is continuous::

     host server # telnet localhost 3333
     host server # (qemu)migrate -d tcp:backup server:4444
     host server # (qemu)info migrate
     host server # Check if the migrate is active and not failed.

11. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

12. After live migration, go to the backup server start vhost testpmd and check if the virtio-pmd can continue to receive packets::

     backup server # testpmd>start
     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm

Test Case 3: migrate with split ring virtio-net
===============================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    host server# testpmd>start

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server # ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    backup server # testpmd>start

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and let the virtio-net link up::

    host server# ssh -p 5555 127.0.0.1
    host vm # ifconfig eth0 up
    host VM# screen -S vm
    host VM# tcpdump -i eth0

7. Send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

8. Check the virtio-net can receive the packet, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

9. Start Live migration, ensure the traffic is continuous::

    host server # telnet localhost 3333
    host server # (qemu)migrate -d tcp:backup server:4444
    host server # (qemu)info migrate
    host server # Check if the migrate is active and not failed.

10. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

11. After live migration, go to the backup server and check if the virtio-net can continue to receive packets::

     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm

Test Case 4: adjust split ring virtio-net queue numbers while migrating with virtio-net
=======================================================================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --vdev 'net_vhost0,iface=./vhost-net,queues=4' -- -i --nb-cores=4 --rxq=4 --txq=4
    host server# testpmd>start

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,mq=on,vectors=10 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server#./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --vdev 'net_vhost0,iface=./vhost-net,queues=4' -- -i --nb-cores=4 --rxq=4 --txq=4
    backup server # testpmd>start

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,mq=on,vectors=10 \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and let the virtio-net link up::

    host server# ssh -p 5555 127.0.0.1
    host vm # ifconfig eth0 up
    host VM# screen -S vm
    host VM# tcpdump -i eth0

7. Send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

8. Check the virtio-net can receive the packet, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

9. Start Live migration, ensure the traffic is continuous::

    host server # telnet localhost 3333
    host server # (qemu)migrate -d tcp:backup server:4444
    host server # (qemu)info migrate
    host server # Check if the migrate is active and not failed.

10. Change virtio-net queue numbers from 1 to 4 while migrating::

     host server # ethtool -L ens3 combined 4

11. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

12. After live migration, go to the backup server and check if the virtio-net can continue to receive packets::

     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm

Test Case 5: migrate with packed ring virtio-pmd
================================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    host server# testpmd>start

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server # ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    backup server # testpmd>start

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and scp the DPDK folder from host to VM::

    host server# ssh -p 5555 127.0.0.1
    host server# scp -P 5555 -r <dpdk_folder>/ 127.0.0.1:/root

7. Run testpmd in VM::

    host VM# cd /root/<dpdk_folder>
    host VM# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    host VM# ninja -C x86_64-native-linuxapp-gcc
    host VM# modprobe uio
    host VM# insmod ./x86_64-native-linuxapp-gcc/kmod/vfio-pci.ko
    host VM# ./usertools/dpdk-devbind.py --bind=vfio-pci 00:03.0
    host VM# echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
    host VM# screen -S vm
    host VM# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i
    host VM# testpmd>set fwd rxonly
    host VM# testpmd>set verbose 1
    host VM# testpmd>start

8. Send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

9. Check the virtio-pmd can receive the packet, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

10. Start Live migration, ensure the traffic is continuous::

     host server # telnet localhost 3333
     host server # (qemu)migrate -d tcp:backup server:4444
     host server # (qemu)info migrate
     host server # Check if the migrate is active and not failed.

11. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

12. After live migration, go to the backup server and check if the virtio-pmd can continue to receive packets::

     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm

Test Case 6: migrate with packed ring virtio-pmd enabled
==================================================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port,note not start vhost port before launching qemu::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server # ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and scp the DPDK folder from host to VM::

    host server# ssh -p 5555 127.0.0.1
    host server# scp -P 5555 -r <dpdk_folder>/ 127.0.0.1:/root

7. Run testpmd in VM::

    host VM# cd /root/<dpdk_folder>
    host VM# CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib -Dexamples=all --default-library=static x86_64-native-linuxapp-gcc
    host VM# ninja -C x86_64-native-linuxapp-gcc
    host VM# modprobe uio
    host VM# insmod ./x86_64-native-linuxapp-gcc/kmod/vfio-pci.ko
    host VM# ./usertools/dpdk-devbind.py --bind=vfio-pci 00:03.0
    host VM# echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
    host VM# screen -S vm
    host VM# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x3 -n 4 -- -i
    host VM# testpmd>set fwd rxonly
    host VM# testpmd>set verbose 1
    host VM# testpmd>start

8. Start vhost testpmd on host and send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    host# testpmd>start
    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

9. Check the virtio-pmd can receive packets, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

10. Start Live migration, ensure the traffic is continuous::

     host server # telnet localhost 3333
     host server # (qemu)migrate -d tcp:backup server:4444
     host server # (qemu)info migrate
     host server # Check if the migrate is active and not failed.

11. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

12. After live migration, go to the backup server start vhost testpmd and check if the virtio-pmd can continue to receive packets::

     backup server # testpmd>start
     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm

Test Case 7: migrate with packed ring virtio-net
================================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    host server# testpmd>start

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server # ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xc0000 -n 4 --vdev 'eth_vhost0,iface=./vhost-net,queues=1' -- -i
    backup server # testpmd>start

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and let the virtio-net link up::

    host server# ssh -p 5555 127.0.0.1
    host vm # ifconfig eth0 up
    host VM# screen -S vm
    host VM# tcpdump -i eth0

7. Send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

8. Check the virtio-net can receive the packet, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

9. Start Live migration, ensure the traffic is continuous::

    host server # telnet localhost 3333
    host server # (qemu)migrate -d tcp:backup server:4444
    host server # (qemu)info migrate
    host server # Check if the migrate is active and not failed.

10. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

11. After live migration, go to the backup server and check if the virtio-net can continue to receive packets::

     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm

Test Case 8: adjust packed ring virtio-net queue numbers while migrating with virtio-net
=========================================================================================

On host server side:

1. Create enough hugepages for testpmd and qemu backend memory::

    host server# mkdir /mnt/huge
    host server# mount -t hugetlbfs hugetlbfs /mnt/huge

2. Bind host port to vfio-pci and start testpmd with vhost port::

    host server# ./usertools/dpdk-devbind.py -b vfio-pci 82:00.1
    host server# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --vdev 'net_vhost0,iface=./vhost-net,queues=4' -- -i --nb-cores=4 --rxq=4 --txq=4
    host server# testpmd>start

3. Start VM on host, here we set 5432 as the serial port, 3333 as the qemu monitor port, 5555 as the SSH port::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,mq=on,vectors=10,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -vnc :10 -daemonize

On the backup server, run the vhost testpmd on the host and launch VM:

4. Set huge page, bind one port to vfio-pci and run testpmd on the backup server, the command is very similar to host::

    backup server # mkdir /mnt/huge
    backup server # mount -t hugetlbfs hugetlbfs /mnt/huge
    backup server # ./usertools/dpdk-devbind.py -b vfio-pci 82:00.0
    backup server#./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-6 -n 4 --vdev 'net_vhost0,iface=./vhost-net,queues=4' -- -i --nb-cores=4 --rxq=4 --txq=4
    backup server # testpmd>start

5. Launch VM on the backup server, the script is similar to host, need add " -incoming tcp:0:4444 " for live migration and make sure the VM image is the NFS mounted folder, VM image is the exact one on host server::

    qemu-system-x86_64 -name vm1 \
    -enable-kvm -m 2048 -object memory-backend-file,id=mem,size=2048M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp 2 -cpu host -drive file=/home/osimg/live_mig/ubuntu16.img \
    -net nic,model=e1000,addr=1f -net user,hostfwd=tcp:127.0.0.1:5555-:22 \
    -chardev socket,id=char0,path=./vhost-net \
    -netdev type=vhost-user,id=netdev0,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,netdev=netdev0,mac=52:54:00:00:00:01,mrg_rxbuf=on,mq=on,vectors=10,packed=on \
    -monitor telnet::3333,server,nowait \
    -serial telnet:localhost:5432,server,nowait \
    -incoming tcp:0:4444 \
    -vnc :10 -daemonize

6. SSH to host VM and let the virtio-net link up::

    host server# ssh -p 5555 127.0.0.1
    host vm # ifconfig eth0 up
    host VM# screen -S vm
    host VM# tcpdump -i eth0

7. Send continuous packets with the physical port's mac(e.g: 90:E2:BA:69:C9:C9) from tester port::

    tester# scapy
    tester# p = Ether(dst="90:E2:BA:69:C9:C9")/IP()/UDP()/Raw('x'*20)
    tester# sendp(p, iface="p5p1", inter=1, loop=1)

8. Check the virtio-net can receive the packet, then detach the session for retach on backup server::

    host VM# testpmd>port 0/queue 0: received 1 packets
    host VM# ctrl+a+d

9. Start Live migration, ensure the traffic is continuous::

    host server # telnet localhost 3333
    host server # (qemu)migrate -d tcp:backup server:4444
    host server # (qemu)info migrate
    host server # Check if the migrate is active and not failed.

10. Change virtio-net queue numbers from 1 to 4 while migrating::

     host server # ethtool -L ens3 combined 4

11. Query stats of migrate in monitor, check status of migration, when the status is completed, then the migration is done::

     host server # (qemu)info migrate
     host server # (qemu)Migration status: completed

12. After live migration, go to the backup server and check if the virtio-net can continue to receive packets::

     backup server # ssh -p 5555 127.0.0.1
     backup VM # screen -r vm


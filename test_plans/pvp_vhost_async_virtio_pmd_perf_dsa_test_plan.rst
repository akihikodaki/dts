.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2023 Intel Corporation

===================================================
PVP vhost/virtio-pmd async data-path perf test plan
===================================================

Description
===========

Benchmark pvp qemu test with vhost async data-path.

Test flow
=========

TG --> NIC --> Vhost --> Virtio--> Vhost --> NIC --> TG

Test Case 1: pvp split ring vhost async test with 1core 1queue using idxd kernel driver
---------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 2wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -n 8 -l 9-10 --file-prefix=dpdk_vhost --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'net_vhost,iface=./vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=2048 --rxd=2048 --forward-mode=mac -a

3. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=n tts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

4. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

5. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

6. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 2: pvp split ring vhost async test with 1core 2queue using idxd kernel driver
---------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 4wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-3 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@wq0.0;rxq0@wq0. 1;txq1@wq0.2;rxq1@wq0.3]'
        -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 3: pvp split ring vhost async test with 2core 2queue using idxd kernel driver
---------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 4wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3]' \
    -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 4: pvp split ring vhost async test with 2core 4queue using idxd kernel driver
---------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 8wq by below command::

         ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
         ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
         ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3;txq2@wq0.4;rxq2@wq0.5;txq3@wq0.6;rxq3@wq0.7]'
    -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 5: pvp split ring vhost async test with 4core 4queue using idxd kernel driver
---------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 8wq by below command::

     ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
     ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
     ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3;txq2@wq0.4;rxq2@wq0.5;txq3@wq0.6;rxq3@wq0.7]' \
    -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

Test Case 6: pvp split ring vhost async test with 4core 8queue using idxd kernel driver
---------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 8wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8,dmas=[txq0@wq0.0;rxq0@wq0.0;txq1@wq0.1;rxq1@wq0.1;txq2@wq0.2;rxq2@wq0.2;txq3@wq0.3;rxq3@wq0.3;txq4@wq0.4;rxq4@wq0.4;txq5@wq0.5;rxq5@wq0.5;txq6@wq0.6;rxq6@wq0.6;txq7@wq0.7;rxq7@wq0.7]'
    -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=18,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

Test Case 7: pvp packed ring vhost async test with 1core 1queue using idxd kernel driver
----------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 2wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 2 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -n 8 -l 9-10 --file-prefix=dpdk_vhost --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'net_vhost,iface=./vhost-net,queues=1,dmas=[txq0@wq0.0;rxq0@wq0.1]' \
    --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=2048 --rxd=2048 --forward-mode=mac -a

3. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

4. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

5. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

6. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 8: pvp packed ring vhost async test with 1core 2queue using idxd kernel driver
----------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 4wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-3 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3]'
    -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 9: pvp packed ring vhost async test with 2core 2queue using idxd kernel driver
----------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 4wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 4 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3]' \
    -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 10: pvp packed ring vhost async test with 2core 4queue using idxd kernel driver
-----------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 8wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3;txq2@wq0.4;rxq2@wq0.5;txq3@wq0.6;rxq3@wq0.7]'
    -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 11: pvp packed ring vhost async test with 4core 4queue using idxd kernel driver
-----------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 8wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@wq0.0;rxq0@wq0.1;txq1@wq0.2;rxq1@wq0.3;txq2@wq0.4;rxq2@wq0.5;txq3@wq0.6;rxq3@wq0.7]' \
    -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

Test Case 12: pvp packed ring vhost async test with 4core 8queue using idxd kernel driver
-----------------------------------------------------------------------------------------

1. Bind one nic port to vfio-pci and 1 dsa device to idxd, then generate 8wq by below command::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0
    ./usertools/dpdk-devbind.py -b idxd 0000:6a:01.0
    ./drivers/dma/idxd/dpdk_idxd_cfg.py -q 8 0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8,dmas=[txq0@wq0.0;rxq0@wq0.0;txq1@wq0.1;rxq1@wq0.1;txq2@wq0.2;rxq2@wq0.2;txq3@wq0.3;rxq3@wq0.3;txq4@wq0.4;rxq4@wq0.4;txq5@wq0.5;rxq5@wq0.5;txq6@wq0.6;rxq6@wq0.6;txq7@wq0.7;rxq7@wq0.7]'
    -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=18,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

Test Case 13: pvp split ring vhost async test with 1core 1queue using vfio-pci driver
-------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -n 8 -l 9-10 --file-prefix=dpdk_vhost --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=2 --socket-mem 8192 \
    --vdev 'net_vhost,iface=./vhost-net,queues=1,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1]' \
    --iova=va -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=2048 --rxd=2048 --forward-mode=mac -a

3. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

4. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

5. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

6. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 14: pvp split ring vhost async test with 1core 2queue using vfio-pci driver
-------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-3 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=4 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3]'
    -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 15: pvp split ring vhost async test with 2core 2queue using vfio-pci driver
-------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=4 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3]'
    -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 16: pvp split ring vhost async test with 2core 4queue using vfio-pci driver
-------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=8 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3;txq2@0000:6a:01.0-q4;rxq2@0000:6a:01.0-q5;txq3@0000:6a:01.0-q6;rxq3@0000:6a:01.0-q7]'
    -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 17: pvp split ring vhost async test with 4core 4queue using vfio-pci driver
-------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=8 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3;txq2@0000:6a:01.0-q4;rxq2@0000:6a:01.0-q5;txq3@0000:6a:01.0-q6;rxq3@0000:6a:01.0-q7]'
    -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

Test Case 18: pvp split ring vhost async test with 4core 8queue using vfio-pci driver
-------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=8 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q0;txq1@0000:6a:01.0-q1;rxq1@0000:6a:01.0-q1;txq2@0000:6a:01.0-q2;rxq2@0000:6a:01.0-q2;txq3@0000:6a:01.0-q3;rxq3@0000:6a:01.0-q3;txq4@0000:6a:01.0-q4;rxq4@0000:6a:01.0-q4;txq5@0000:6a:01.0-q5;rxq5@0000:6a:01.0-q5;txq6@0000:6a:01.0-q6;rxq6@0000:6a:01.0-q6;txq7@0000:6a:01.0-q7;rxq7@0000:6a:01.0-q7]'
    -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=18,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

Test Case 19: pvp packed ring vhost async test with 1core 1queue using vfio-pci driver
--------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

   ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-3 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=2 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=1,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1]'
    -- -i --nb-cores=1 --txq=1 --rxq=1 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 20: pvp packed ring vhost async test with 1core 2queue using vfio-pci driver
--------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-3 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=4 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3]'
    -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x3 -n 8 -- -i --nb-cores=1 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 21: pvp packed ring vhost async test with 2core 2queue using vfio-pci driver
--------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=4 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=2,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3]'
    -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=2 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=6,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=2 --rxq=2 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 22: pvp packed ring vhost async test with 2core 4queue using vfio-pci driver
--------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-4 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=8 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3;txq2@0000:6a:01.0-q4;rxq2@0000:6a:01.0-q5;txq3@0000:6a:01.0-q6;rxq3@0000:6a:01.0-q7]'
    -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x7 -n 8 -- -i --nb-cores=2 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518], show throughput with below command::

    testpmd>show port stats all

Test Case 23: pvp packed ring vhost async test with 4core 4queue using vfio-pci driver
--------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=8 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=4,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q1;txq1@0000:6a:01.0-q2;rxq1@0000:6a:01.0-q3;txq2@0000:6a:01.0-q4;rxq2@0000:6a:01.0-q5;txq3@0000:6a:01.0-q6;rxq3@0000:6a:01.0-q7]'
    -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=4 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=10,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=4 --rxq=4 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

Test Case 24: pvp packed ring vhost async test with 4core 8queue using vfio-pci driver
--------------------------------------------------------------------------------------

1. Bind one nic port and 1 dsa device to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:29:00.   0 0000:6a:01.0

2. Launch vhost testpmd by below command::

    ./build/app/dpdk-testpmd -l 2-6 -n 8 --huge-dir=/dev/hugepages -a 0000:29:00.0 -a 0000:6a:01.0,max_queues=8 --socket-mem 8192 \
    --vdev 'eth_vhost0,iface=vhost-net,queues=8,dmas=[txq0@0000:6a:01.0-q0;rxq0@0000:6a:01.0-q0;txq1@0000:6a:01.0-q1;rxq1@0000:6a:01.0-q1;txq2@0000:6a:01.0-q2;rxq2@0000:6a:01.0-q2;txq3@0000:6a:01.0-q3;rxq3@0000:6a:01.0-q3;txq4@0000:6a:01.0-q4;rxq4@0000:6a:01.0-q4;txq5@0000:6a:01.0-q5;rxq5@0000:6a:01.0-q5;txq6@0000:6a:01.0-q6;rxq6@0000:6a:01.0-q6;txq7@0000:6a:01.0-q7;rxq7@0000:6a:01.0-q7]'
    -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048 --max-pkt-len=5200 --tx-offloads=0x00008000 --forward-mode=mac -a

2. Launch VM with mrg_rxbuf feature on::

    taskset -c 11-18 /usr/local/qemu-7.1.0/bin/qemu-system-x86_64 -name us-vhost-vm1 -cpu host -enable-kvm \
    -m 8192 -object memory-backend-file,id=mem,size=8192M,mem-path=/mnt/huge,share=on \
    -numa node,memdev=mem -mem-prealloc -smp cores=8,sockets=1 -drive file=/home/xingguang/osimg/ubuntu22-04.img \
    -chardev socket,id=char0,path=./vhost-net -monitor unix:/tmp/vm2_monitor.sock,server,nowait -device e1000,netdev=ntts1 \
    -netdev user,id=ntts1,hostfwd=tcp:127.0.0.1:6002-:22 \
    -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce,queues=8 \
    -device virtio-net-pci,mac=52:54:00:00:00:01,netdev=mynet1,mrg_rxbuf=on,mq=on,vectors=18,rx_queue_size=1024,tx_queue_size=1024,csum=off,guest_csum=off,gso=off,host_tso4=off,guest_tso4=off,guest_ecn=off,packed=on -vnc :10 --monitor stdio

3. Set affinity::

    (qemu)info cpus
    <host>taskset -cp 11 xxx
    ...
    <host>taskset -cp 18 xxx

4. On VM, bind virtio net to vfio-pci and run testpmd::

    mount -t hugetlbfs nodev /mnt/huge
    modprobe vfio-pci
    echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode
    ./usertools/dpdk-devbind.py -b vfio-pci 00:04.0

    ./build/app/dpdk-testpmd -c 0x1f -n 8 -- -i --nb-cores=4 --txq=8 --rxq=8 --txd=2048 --rxd=2048
    testpmd>set fwd csum
    testpmd>start

5. Send tcp/ip packets by packet generator with different packet sizes [64,128,256,512,1024,1280,1518,2048,4096], show throughput with below command::

    testpmd>show port stats all

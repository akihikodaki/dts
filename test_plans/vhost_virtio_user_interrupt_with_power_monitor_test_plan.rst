.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

=======================================================================
Vhost_user virtio_user interrupt test with power monitor mode test plan
=======================================================================

Description
===========

According to current semantics of power monitor. When no packet come in, the running core will sleep. Once
packets arrive, the value of address will be changed and the running core will wakeup.
This document provides the test plan for testing vhost_user and virtio_user interrupt with power monitor mode.

Prerequisites
==============
multi-queue per core need enable RTM(Restricted Transactional Memory) in bios

General set up
--------------
1. Compile DPDK::

      meson  -Dexamples=l3fwd-power x86_64-native-linuxapp-gcc
      ninja -C x86_64-native-linuxapp-gcc

Test case
=========

Test Case 1: Split ring virtio-user interrupt test with vhost-user as backed
----------------------------------------------------------------------------

1. Bind NIC port to vfio-pci.

2. Launch vhost with testpmd::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --file-prefix=vhost \
      --vdev 'net_vhost0,iface=./vhost-net,queues=1' -- -i  --rxq=1 --txq=1
      testpmd>start

3. Launch virtio with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 3-4 -n 4 --no-pci --file-prefix=l3fwd-power \
      --vdev=virtio_user0,path=./vhost-net --log-level='user1,7' -- -p 1 --config="(0,0,4)" --parse-ptype --pmd-mgmt=monitor

4. Sent imix packets from TG, check packets can forward back from vhost log::

      testpmd>show port stats all

5. Stop and start vhost, check packets can forward back again.

Test Case 2: Split ring multi-queues virtio-user interrupt test with vhost-user as backed
-----------------------------------------------------------------------------------------

1. Bind NIC port to vfio-pci.

2. Launch vhost testpmd with 2queues::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --file-prefix=vhost \
      --vdev 'net_vhost0,iface=./vhost-net,queues=2' -- -i  --rxq=2 --txq=2
      testpmd>start

3. Launch virtio with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 3-4 -n 4 --no-pci --file-prefix=l3fwd-power \
      --vdev=virtio_user0,path=./vhost-net,queues=2 --log-level='user1,7' -- -p 1 --config="(0,0,3),(0,1,4)" --parse-ptype --pmd-mgmt=monitor

4. Sent imix pkts from TG,check packets can fwd back and both 2 queues exist packets::

      testpmd>show port stats all
      testpmd>stop

5. Restart vhost port, check packets can forward back and both 2 queues exist packets.

Test Case 3:Wake up split ring vhost-user core with l3fwd-power sample
----------------------------------------------------------------------

1. bind nic port to vfio-pci 

2. Launch virtio-user with server mode::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 --file-prefix=virtio-user \
      --vdev net_virtio_user0,path=./vhost-net,server=1 -- -i --rxq=1 --txq=1

3. Launch vhost with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 4-5 --file-prefix=vhost --no-pci \
      --vdev net_vhost0,iface=vhost-net,client=1 -- -p 0x01 --config="(0,0,4)" --pmd-mgmt=monitor --parse-ptype

4. Start virtio-user::

      testpmd>start

5. Sent imix packets from TG, check packets can fwd back with correct payload.

6. Stop and start virtio-user, check packets can forward back again.

Test Case 4:Wake up split ring multi-queues vhost-user core with l3fwd-power sample
-----------------------------------------------------------------------------------

Prerequisites
--------------
multi-queue per core need enable RTM(Restricted Transactional Memory) in bios

Flow:TG-->nic-->virtio-user-->vhost-user

1. Bind NIC port to vfio-pci

2. Launch virtio-user with server mode::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 --file-prefix=virtio-user \
      --vdev net_virtio_user0,path=./vhost-net,queues=2,server=1 -- -i --rxq=2 --txq=2

3. Launch vhost with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 4-5 --file-prefix=vhost --no-pci \
      --vdev net_vhost0,iface=vhost-net,queues=2,client=1 -- -p 0x01 --config="(0,0,4),(0,1,5)" --pmd-mgmt=monitor --parse-ptype

4. Start virtio-user::

      testpmd>start

5. Sent imix pkts from TG,check packets can fwd back and both 2 queues exist packets::

      testpmd>show port stats all
      testpmd>stop

6. Restart virtio-user port, check packets can fwd back and both 2 queues exist packets.

Test Case 5: Packed ring virtio-user interrupt test with vhost-user as backed
-----------------------------------------------------------------------------

1. Bind NIC port to vfio-pci.

2. Launch vhost with testpmd::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --file-prefix=vhost \
      --vdev 'net_vhost0,iface=./vhost-net,queues=1' -- -i  --rxq=1 --txq=1
      testpmd>start

3. Launch virtio with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 3-4 -n 4 --no-pci --file-prefix=l3fwd-power \
      --vdev=virtio_user0,path=./vhost-net,packed_vq=1 --log-level='user1,7' -- -p 1 --config="(0,0,3)" --parse-ptype --pmd-mgmt=monitor

4. Sent imix pkts from TG, check packets can fwd back.

5. Stop and start vhost, check packets can fwd back again.

Test Case 6: Packed ring multi-queues virtio-user interrupt test with vhost-user as backed
------------------------------------------------------------------------------------------

Prerequisites
--------------
multi-queue per core need enable RTM(Restricted Transactional Memory) in bios
1. Bind NIC port to vfio-pci.

2. Launch vhost with testpmd::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 1-2 -n 4 --file-prefix=vhost \
      --vdev 'net_vhost0,iface=./vhost-net,queues=2' -- -i  --rxq=2 --txq=2
      testpmd>start

3. Launch virtio with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 3-4 -n 4 --no-pci --file-prefix=l3fwd-power \
      --vdev=virtio_user0,path=./vhost-net,queues=2,packed_vq=1 --log-level='user1,7' -- -p 1 --config="(0,0,3),(0,1,4)" --parse-ptype --pmd-mgmt=monitor

4. Sent imix pkts from TG, check packets can fwd back and both 2 queues exist packets::

      testpmd>show port stats all
      testpmd>stop

5. Restart vhost port, check packets can fwd back and both 2 queues exist packets.

Test Case 7:Wake up packed ring vhost-user core with l3fwd-power sample
-----------------------------------------------------------------------

1. Bind NIC port to vfio-pci

2.Launch virtio-user with server mode::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 --file-prefix=virtio-user \
      --vdev net_virtio_user0,path=./vhost-net,packed_vq=1,server=1 -- -i --rxq=1 --txq=1

3.Launch vhost with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 4-5 --file-prefix=vhost --no-pci \
      --vdev net_vhost0,iface=vhost-net,client=1 -- -p 0x01 --config="(0,0,4)" --pmd-mgmt=monitor --parse-ptype

4. Start virtio-user::

      testpmd>start

5. Sent imix pkts from TG, check packets can fwd back.

6. Stop and start virtio-user, check packets can forward back again.

Test Case 8:Wake up packed ring multi-queues vhost-user core with l3fwd-power sample
------------------------------------------------------------------------------------

Prerequisites
--------------
multi-queue per core need enable RTM(Restricted Transactional Memory) in bios
1. Bind NIC port to vfio-pci

2. Launch virtio-user with server mode::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 2-3 -n 4 --file-prefix=virtio-user \
      --vdev net_virtio_user0,path=./vhost-net,queues=2,packed_vq=1,server=1 -- -i --rxq=2 --txq=2

3. Launch vhost with l3fwd-power::

      ./x86_64-native-linuxapp-gcc/examples/dpdk-l3fwd-power -l 4-5 --file-prefix=vhost --no-pci \
      --vdev net_vhost0,iface=vhost-net,queues=2,client=1 -- -p 0x01 --config="(0,0,4),(0,1,5)" --pmd-mgmt=monitor --parse-ptype

4. Start virtio-user::

      testpmd>start

5. Sent imix pkts from T, check packets can fwd back and both 2 queues exist packets::

      testpmd>show port stats all
      testpmd>stop

6. Restart virtio-user port, check packets can fwd back and both 2 queues exist packets.

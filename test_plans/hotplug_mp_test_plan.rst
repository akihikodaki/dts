.. Copyright (c) <2018>, Intel Corporation
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

==========================
Hotplug on multi-processes
==========================
Currently secondary process will only sync ethdev from primary process at
init stage, but it will not be aware if device is attached/detached on
primary process at runtime.

While there is the requirement from application that take
primary-secondary process model. The primary process work as a resource
management process, it will create/destroy virtual device at runtime,
while the secondary process deal with the network stuff with these devices.

So the orignial intention is to fix this gap, but beyond that the patch
set provide a more comprehesive solution to handle different hotplug
cases in multi-process situation, it cover below scenario:

* Attach a device from the primary
* Detach a device from the primary
* Attach a device from a secondary
* Detach a device from a secondary

In primary-secondary process model, we assume ethernet devices are shared
by default, that means attach or detach a device on any process will
broadcast to all other processes through mp channel then device
information will be synchronized on all processes.

Any failure during attaching process will cause inconsistent status
between processes, so proper rollback action should be considered.


Test Case: Attach physical device from primary or secondary
===========================================================
Start sample code as primary then secondary::

    ./hotplug_mp --proc-type=auto

Check primary and secondary processes don't have any device::

    example> list
    list all etherdev

Bind one port to igb_uio or vfio

Attach the physical device from primary or secondary, check primary and
secondary processes attach the share device successfully::

     example> attach 0000:88:00.0
     example> list
     list all etherdev
     0       0000:88:00.0

Quit primary and secondary processes

Re-bind port to kernel state


Test Case: Detach physical device from primary or secondary
===========================================================
Bind one port to igb_uio or vfio

Start sample code as primary then secondary::

    ./hotplug_mp --proc-type=auto

Check primary and secondary processes have the device::

    example> list
    list all etherdev
    0       0000:88:00.0

Detach the physical device from primary or secondary, check primary and
secondary processes detach the share device successfully::

    example> detach 0000:88:00.0
    example> list
    list all etherdev

Quit primary and secondary processes

Re-bind port to kernel state


Test Case: Attach virtual device from primary or secondary
==========================================================
Start sample code as primary then secondary::

    ./hotplug_mp --proc-type=auto

Check primary and secondary processes don't have any device::

    example> list
    list all etherdev

Attach a virtual device from primary or secondary, check primary and
secondary processes attach the share device successfully::

    example> attach net_af_packet,iface=ens803f1
    example> list
    list all etherdev
    0       net_af_packet

Quit primary and secondary processes

Test Case: Detach virtual device from primary or secondary
==========================================================
Start sample code as primary then secondary::

    ./hotplug_mp --proc-type=auto

Check primary and secondary processes don't have any device::

    example> list
    list all etherdev

Attach a virtual device from primary or secondary, check primary and
secondary processes attach the share device successfully::

    example> attach net_af_packet,iface=ens803f1
    example> list
    list all etherdev
    0       net_af_packet

Detach the physical device from primary or secondary, check primary and
secondary processes detach the share device successfully::

    example> detach net_af_packet
    example> list
    list all etherdev

Quit primary and secondary processes

Test Case: Repeat to attach/detach physical device from primary or secondary
============================================================================
Start sample code as primary then secondary::

    ./hotplug_mp --proc-type=auto

Check primary and secondary processes don't have any device::

    example> list
    list all etherdev

Bind one port to igb_uio or vfio

Attach the physical device from primary or secondary, check primary and
secondary processes attach the share device successfully::

    example> attach 0000:88:00.0
    example> list
    list all etherdev
    0       0000:88:00.0

Attach the same physical device from primary or secondary, check primary and
secondary processes fail to attach same device again

Detach the physical device from primary or secondary, check primary and
secondary processes detach the share device successfully::

    example> detach 0000:88:00.0
    example> list
    list all etherdev

Detach the same physical device from primary or secondary, check primary and
secondary processes fail to detach same device again

Repeat above attach and detach for 2 times

Quit primary and secondary processes

Re-bind port to kernel state


Test Case: Repeat to attach/detach virtual device from primary or secondary
===========================================================================
Start sample code as primary then secondary::

     ./hotplug_mp --proc-type=auto

Check primary and secondary processes don't have any device::

     example> list
     list all etherdev

Attach a virtual device from primary or secondary, check primary and
secondary processes attach the share device successfully::

    example> attach net_af_packet,iface=ens803f1
    example> list
    list all etherdev
    0       net_af_packet

Attach the same virtual device from primary or secondary, check primary and
secondary processes fail to attach same device again

Detach the virtual device from primary or secondary, check primary and
secondary processes detach the share device successfully::

    example> detach net_af_packet
    example> list
    list all etherdev

Detach the same virtual device from primary or secondary, check primary and
secondary processes fail to detach same device again

Repeat above attach and detach for 2 times

Quit primary and secondary processes

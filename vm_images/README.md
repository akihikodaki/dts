# DTS VM Images

This folder contains utilities to create VM 
images for use in virtio testing.

## Host Requirements

The host MUST have qemu/kvm with libvirtd installed
and set up. 

The host MUST be the same architecture as the VM
you are building.

The host MUST have podman and either docker or have podman
aliased as docker (running "docker" calls podman).

## Creating a VM

Use the "create_vm_image.py" script to create the vm image.
If you do not have the required containers on your system,
it will build them. 

The root password it asks for is what to set the VM's 
root password to, not the root password of the system
you run the script on. 

``` --debug ``` will enable debug output from guestfs 
tools. This produces a lot of output and you shouldn't
use it unless something is going wrong.

The base image MUST be a "cloud ready" or "prebuilt"
image, meaning you cannot use an installer ISO. It also
must be in the qcow2 format, (use qemu-img to convert it).
Most distros will have a "cloud image" which is in the 
correct format. This base image will not be modified
by the build script.

The output image is where all of the modifications go and
it is the image that you should use with DTS.

## Supported Distros

Currently, only RHEL 8 family distros and Ubuntu 20.04 are 
supported. Debian might work, but it is untested. Most
testing has gone to Ubuntu 20.04. 

## Architectures

Due to the way that guestfs tools work, they must run 
under kvm, but the host needs to have a kernel image 
that can be used to boot the VM. It may be possible
to work around this issue using containers, but 
several days of experimentation kept running into 
more and more complex issues with the interactions
between libguestfs and docker/podman. As such,
your best bet is to build your VMs on either a 
bare-metal system of your desired architecture
or inside a VM already being emulated as your desired 
architecture. This second approach may run into
issues with the hypervisor, since not all hypervisors 
support nested virtualization by default. Since you need
an appropriate kernel image installed as well, it may
be easiest to build VMs using whatever distro you already
use for most of your servers.

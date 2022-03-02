FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y

RUN apt-get install --no-install-recommends -y libguestfs-tools \
    qemu linux-image-generic qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils \
    linux-image-unsigned-5.11.0-46-generic qemu-system-x86

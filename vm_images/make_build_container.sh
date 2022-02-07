#!/bin/bash

# Podman is used here because Docker does very odd things when
# building for another architecture. Docker's solution to this,
# buildx, is still unstable.

podman build --arch arm64 -t dts_vm_builder:aarch64 . &
DTS_AARCH64_BUILD_PID=$!
podman build --arch amd64 -t dts_vm_builder:x86_64 . &
DTS_x86_64_BUILD_PID=$!
podman build --arch ppc64le -t dts_vm_builder:ppc64le . &
DTS_PPC64LE_BUILD_PID=$!

wait $DTS_AARCH64_BUILD_PID
wait $DTS_PPC64LE_BUILD_PID
wait $DTS_x86_64_BUILD_PID
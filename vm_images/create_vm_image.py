#!/usr/bin/python3

import argparse
import enum
import os
import subprocess
from sys import stderr
from typing import List, Optional, Set, Tuple
import xml.etree.ElementTree as ET
import platform

DOCKER_IMAGE_NAME = "dts_vm_builder"


# From https://libguestfs.org/guestfs.3.html#guestfs_inspect_get_distro
class OsFamily(enum.Enum):
    ALPINE = "alpinelinux"
    ALT = "altlinux"
    ARCH = "archlinux"
    BUILDROOT_DERIVED = "buildroot"
    CENTOS = "centos"
    CIRROS = "cirros"
    COREOS = "coreos"
    DEBIAN = "debian"
    FEDORA = "fedora"
    FREEBSD = "freebsd"
    FREEDOS = "freedos"
    FRUNGALWARE = "frugalware"
    GENTOO = "gentoo"
    KALI = "kalilinux"
    KYLIN = "kylin"
    MINT = "linuxmint"
    MAGEIA = "mageia"
    MANDRIVA = "mandriva"
    MEEGO = "meego"
    MSDOS = "msdos"
    NEOKYLIN = "neokylin"
    NETBSD = "netbsd"
    OPENBSD = "openbsd"
    OPENMANDRIVA = "openmandriva"
    OPENSUSE = "opensuse"
    ORACLE = "oraclelinux"
    PARDUS = "pardus"
    PLD = "pldlinux"
    RHEL_BASED = "redhat-based"
    RHEL = "rhel"
    ROCKY = "rocky"
    SCIENTIFIC_LINUX = "scientificlinux"
    SLACKWARE = "slackware"
    SLES = "sles"
    SUSE_BASED = "suse-based"
    TTY_LINUX = "ttylinux"
    UBUNTU = "ubuntu"
    VOID = "voidlinux"
    WINDOWS = "windows"

    UNKNOWN = "unknown"

    def __str__(self):
        return self.value


# The Os Families that are supported
SUPPORTED_OS_FAMILIES = {
    OsFamily.CENTOS,
    OsFamily.DEBIAN,
    OsFamily.FEDORA,
    OsFamily.RHEL_BASED,
    OsFamily.RHEL,
    OsFamily.UBUNTU,
}


# From https://libguestfs.org/guestfs.3.html#guestfs_file_architecture
class Arch(enum.Enum):
    aarch64 = "aarch64"
    i386 = "i386"
    ia64 = "ia64"
    ppc = "ppc"
    ppc64 = "ppc64"
    ppc64le = "ppc64le"
    riscv32 = "riscv32"
    riscv64 = "riscv64"
    riscv128 = "riscv128"
    s390 = "s390"
    s390x = "s390x"
    sparc = "sparc"
    sparc64 = "sparc64"
    x86_64 = "x86_64"

    def __str__(self):
        return self.value


# The supported architectures
SUPPORTED_ARCHITECTURES = {Arch.x86_64, Arch.aarch64, Arch.ppc64}


def validate_filepath(parser: argparse.ArgumentParser, filepath: str) -> str:
    if not os.path.isabs(filepath):
        filepath = os.path.abspath(filepath)

    if os.path.exists(filepath):
        return filepath
    else:
        parser.error(f"Path {filepath} not found")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    # Base image file
    parser.add_argument("base_image", type=lambda f: validate_filepath(parser, f))

    # Where to write the vm image to
    parser.add_argument("output_path")

    # What to set the root password to
    parser.add_argument(
        "--root_password", help="The new root password for the vm", default="dts"
    )

    # Whether to run virt-customize in debug mode
    parser.add_argument("--debug", action="store_true", default=False)

    return parser.parse_args()


def run_subprocess(
    os_family_tags: Set[OsFamily],
    base_image_path: str,
    output_path: str,
    root_password: str,
    debug_mode: bool,
    arch: Arch,
):
    copy_base_image_to_output_path(base_image_path, output_path)

    print("Building under emulation")

    # Check if the docker container already exists
    docker_process = subprocess.run(
        f"docker image ls {DOCKER_IMAGE_NAME}", capture_output=True, shell=True
    )

    if docker_process.returncode != 0:
        error("Unable to check for presence of docker image")

    if not len(docker_process.stdout.splitlines()) >= 2:  # image does not exist
        subprocess.run(f"./make_build_container.sh")

    docker_command = [
        "docker",
        "run",
        # The container needs to access QEMU/KVM
        "--privileged",
        "-d",
        "--platform",
    ]

    if arch == Arch.x86_64:
        docker_command += ("linux/amd64",)
    elif arch == Arch.ppc64le:
        docker_command += ("linux/ppc64le",)
    elif arch == Arch.aarch64:
        docker_command += ("linux/arm64",)
    else:
        error(f"Please add {arch} to the if chain selecting the docker platform")

    docker_command += ("-v $(pwd):/vm_folder",)

    if debug_mode:
        docker_command += (
            "-e",
            "LIBGUESTFS_DEBUG=1",
            "-e",
            "LIBGUESTFS_TRACE=1",
        )

    # Run cat so it doesn't terminate until we stop it
    docker_command += f"-it {DOCKER_IMAGE_NAME}:{arch}", "cat"

    # if debug_mode:
    print("Running:")
    print(" ".join(docker_command))
    print("\n\n")

    docker_process = subprocess.run(
        " ".join(docker_command), shell=True, capture_output=True
    )

    if docker_process.returncode != 0:
        print(docker_process.stderr)
        print(docker_process.stdout)
        error("Unable to run docker container, try --debug")

    container_id = docker_process.stdout.strip().decode()

    if debug_mode:
        print(f"Docker container is {container_id}")

    virt_customize_command = get_virt_customize_command(
        os_family_tags, output_path, root_password
    )

    vm_build_command = ["docker", "exec", "-w", "/vm_folder"]

    if debug_mode:
        vm_build_command += (
            "-e",
            "LIBGUESTFS_DEBUG=1",
            "-e",
            "LIBGUESTFS_TRACE=1",
        )

    vm_build_command += (
        "-it",
        container_id,
    )

    vm_build_command += (virt_customize_command,)

    # if debug_mode:
    print(" ".join(vm_build_command))

    vm_build_process = subprocess.run(" ".join(vm_build_command), shell=True)

    if vm_build_process.returncode == 0:
        # Shut down the build container
        subprocess.run(f"docker kill {container_id}", shell=True)

    print(vm_build_process.returncode)


def run_command_in_docker_container(
    container_id: str, command: str, debug_mode: bool, **kwargs
) -> subprocess.CompletedProcess:
    docker_command = "docker exec "

    if debug_mode:
        docker_command += f"-e LIBGUESTFS_DEBUG=1 -e LIBGUESTFS_TRACE=1"

    docker_command += f"-w /vm_folder -t {container_id} {command}"
    return subprocess.run(docker_command, **kwargs)


def copy_base_image_to_output_path(base_image_path: str, output_path: str):
    real_base_image_path: str = os.path.realpath(base_image_path)
    real_output_path: str = os.path.realpath(output_path)

    if (
        real_base_image_path != real_output_path
    ):  # do not copy if they are the same path
        subprocess.run(
            ["cp", real_base_image_path, real_output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


def get_virt_customize_command(
    os_family_tags: Set[OsFamily], output_path: str, root_password: str
) -> str:
    commands = [
        f"virt-customize -a {output_path} --root-password password:{root_password} --update"
    ]

    commands = commands + get_enable_additional_repos_commands(os_family_tags)

    packages = get_packages_for_os_family(os_family_tags)
    packagelist = ",".join(packages)
    commands += (f"--install {packagelist}",)
    commands += (f"--run-command {get_install_meson_command(os_family_tags)}",)
    commands += (f"--run-command {get_setup_hugepages_command(os_family_tags)}",)
    commands += (f"--run-command {get_hugepage_mount_command(os_family_tags)}",)
    commands = commands + get_security_enforcement_disable_command(
        os_family_tags, output_path
    )
    return " ".join(commands)


def get_enable_additional_repos_commands(os_family_tags: Set[OsFamily]):
    if OsFamily.RHEL in os_family_tags and OsFamily.FEDORA not in os_family_tags:
        packages = [
            "yum-utils",
            "epel-release",
        ]

        packagelist = ",".join(packages)

        return [
            f"--install {packagelist}",
            f"--run-command 'yum-config-manager --enable powertools'",
        ]
    elif OsFamily.DEBIAN in os_family_tags:
        return []


def get_packages_for_os_family(os_family_tags: Set[OsFamily]) -> List[str]:
    if OsFamily.DEBIAN in os_family_tags:
        return [
            "make",
            "gcc",
            "g++",
            "libc-dev",
            "libc6-dev",
            "ninja-build",
            "pkg-config",
            "libnuma-dev",
            "python3-pyelftools",
            "abigail-tools",
            "git",
            "librdmacm-dev",
            "librdmacm1",
            "rdma-core",
            "libelf-dev",
            "libmnl-dev",
            "libpcap-dev",
            "libcrypto++-dev",
            "libjansson-dev",
            "libatomic1",
            "python3-pip",
            "python3-setuptools",
            "python3-wheel",
            "iperf",
            "chrony",
        ]
    elif OsFamily.RHEL in os_family_tags:
        return [
            "make",
            "gcc",
            "pkg-config",
            "ninja-build",
            "numactl-libs",
            "python3-pyelftools",
            "libabigail-devel",
            "git",
            "librdmacm",
            "librdmacm-utils",
            "rdma-core",
            "elfutils-libelf-devel",
            "libmnl-devel",
            "libpcap-devel",
            "cryptopp-devel",
            "jansson-devel",
            "libatomic",
            "python3-pip",
            "python3-setuptools",
            "python3-wheel",
        ]
    else:
        error(f"Unable to get packages for {os_family_tags} OS family.")


def get_install_meson_command(os_family_tags: Set[OsFamily]) -> str:
    if OsFamily.DEBIAN in os_family_tags or OsFamily.RHEL in os_family_tags:
        # the "--trusted-host" flags are included because the date on the system will be Jan 1, 1970 due to the way
        # guestfs-tools starts the vm. This breaks pip's ssl, so making these hosts trusted fixes that.
        return '"python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org meson"'
    else:
        error(f"Unknown command to install meson for {os_family_tags}")


def get_setup_hugepages_command(os_family_tags: Set[OsFamily]) -> str:
    if OsFamily.DEBIAN in os_family_tags or OsFamily.RHEL in os_family_tags:
        return (
            '"sed -i -r \'s/GRUB_CMDLINE_LINUX_DEFAULT=\\"([^\\"]+)\\"/'
            'GRUB_CMDLINE_LINUX_DEFAULT=\\"\\1 default_hugepagesz=2M hugepagesz=2M'
            ' hugepages=1375 hugepagesz=1G hugepages=8\\"/\' /etc/default/grub"'
        )
    else:
        error(f"Unknown command to setup hugepages for {os_family_tags}")


def get_hugepage_mount_command(os_family_tags: Set[OsFamily]) -> str:
    if OsFamily.DEBIAN in os_family_tags or OsFamily.RHEL in os_family_tags:
        return '"mkdir -p /dev/huge && mount nodev -t hugetlbfs -o rw,pagesize=2M /dev/huge/ && umount /dev/huge"'
    else:
        error(f"Unknown hugepage mount command for {os_family_tags}")


def get_security_enforcement_disable_command(
    os_family_tags: Set[OsFamily], output_path: str
) -> List[str]:
    if OsFamily.RHEL in os_family_tags:
        return [f"--run-command 'echo \"SELINUX=disabled\" > /etc/selinux/config'"]
    else:
        return []


def get_os_family_tags(distribution: OsFamily) -> Set[OsFamily]:
    tags: Set[OsFamily] = {distribution}

    # This is not an if-elif-else chain to reduce duplicate code. This way,
    # for example, a specialized ubuntu distribution may first be tagged
    # ubuntu, then all the ubuntu tags will be applied to it. The most
    # specific distros should be placed first.

    if OsFamily.UBUNTU in tags:
        tags.add(OsFamily.DEBIAN)

    if OsFamily.FEDORA in tags:
        tags.add(OsFamily.CENTOS)

    if OsFamily.CENTOS in tags:
        tags.add(OsFamily.RHEL)

    if OsFamily.RHEL in tags:
        tags.add(OsFamily.RHEL)

    return tags


def check_being_run_as_root():
    proc = subprocess.run(["whoami"], capture_output=True)
    if "root".encode() not in proc.stdout:
        error("This program must be run as root.")


def get_image_info(base_image_path: str) -> (OsFamily, Arch):
    command = [
        "virt-inspector",
        # Otherwise it will show everything installed via the package manager
        "--no-applications",
        # We don't need to icon for the distro
        "--no-icon",
        "-a",
        base_image_path,
    ]

    print(" ".join(command))

    proc = subprocess.run(command, capture_output=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        error("Unable to inspect base image")

    tree = ET.fromstring(proc.stdout)
    distro = OsFamily(tree.findtext("operatingsystem/distro"))
    arch = Arch(tree.findtext("operatingsystem/arch"))

    return distro, arch


def main():
    args = parse_arguments()
    check_being_run_as_root()
    distro, arch = get_image_info(args.base_image)

    if distro not in SUPPORTED_OS_FAMILIES:
        error(f"Unsupported distro {distro}")

    if arch not in SUPPORTED_ARCHITECTURES:
        error(f"Unsupported architecture {arch}")

    os_family_tags = get_os_family_tags(distro)
    run_subprocess(
        os_family_tags,
        args.base_image,
        args.output_path,
        args.root_password,
        args.debug,
        arch,
    )


def error(message: str):
    print(message, file=stderr)
    exit(1)


if __name__ == "__main__":
    main()

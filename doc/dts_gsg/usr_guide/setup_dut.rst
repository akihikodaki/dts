Set up DUT
===========

This chapter describes the packages required to compile the DPDK in DUT.

BIOS Setting Prerequisite on x86
--------------------------------

DPDK prefers devices bound to ``vfio-pci`` kernel module, therefore, `VT-x` and `VT-d` should be enabled.

.. code-block:: console

   Advanced -> Integrated IO Configuration -> Intel(R) VT for Directed I/O <Enabled>
   Advanced -> Processor Configuration -> Intel(R) Virtualization Technology <Enabled>


Set Hugepages
------------------

Hugepage support is required for the large memory pool allocation used for packet buffers
(the HUGETLBFS option must be enabled in the running kernel as indicated the previous section).
By using hugepage allocations, performance is increased since fewer pages are needed,
and therefore less Translation Lookaside Buffers (TLBs, high speed translation caches),
which reduce the time it takes to translate a virtual page address to a physical page address.
Without hugepages, high TLB miss rates would occur with the standard 4k page size, slowing performance.


Edit /etc/default/grub
~~~~~~~~~~~~~~~~~~~~~~~

Set GRUB_CMDLINE_LINUX in etc/default/grub:

for 2M pagesize::

    GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt hugepagesz=2M hugepages=1024 default_hugepagesz=2M intel_pstate=disable"

for 1G pagesize::

    GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt hugepagesz=1G hugepages=16 default_hugepagesz=1G intel_pstate=disable"

Execute grub-mkconfig
~~~~~~~~~~~~~~~~~~~~~~~

execute below command::

    # grub-mkconfig -o /boot/grub/grub.cfg

.. note::

    some OS may need execute following command::

        #grub2-mkconfig -o /boot/grub2/grub.cfg

then reboot OS to make the hugepage setting take effect.

Packages Required
------------------

**Required Tools and Libraries:**

.. note::

    The setup commands and installed packages needed on various systems may be different.
    For details on Linux distributions and the versions tested, please consult the DPDK Release Notes.

*   General development tools including a supported C compiler such as gcc (version 4.9+) or clang (version 3.4+).

    * For RHEL/Fedora systems these can be installed using ``dnf groupinstall "Development Tools"``

    * For Ubuntu/Debian systems these can be installed using ``apt install build-essential``

*   Python 3.5 or later.

*   Meson (version 0.49.2+) and ninja

    * ``meson`` & ``ninja-build`` packages in most Linux distributions

    * If the packaged version is below the minimum version, the latest versions
      can be installed from Python's "pip" repository: ``pip3 install meson ninja``

*   ``pyelftools`` (version 0.22+)

    * For Fedora systems it can be installed using ``dnf install python-pyelftools``

    * For RHEL/CentOS systems it can be installed using ``pip3 install pyelftools``

    * For Ubuntu/Debian it can be installed using ``apt install python3-pyelftools``

*   Library for handling NUMA (Non Uniform Memory Access).

    * ``numactl-devel`` in RHEL/Fedora;

    * ``libnuma-dev`` in Debian/Ubuntu;

.. note::

   Please ensure that the latest patches are applied to third party libraries
   and software to avoid any known vulnerabilities.


**Optional Tools:**

*   Intel® C++ Compiler (icc). For installation, additional libraries may be required.
    See the icc Installation Guide found in the Documentation directory under the compiler installation.

*   IBM® Advance ToolChain for Powerlinux. This is a set of open source development tools and runtime libraries
    which allows users to take leading edge advantage of IBM's latest POWER hardware features on Linux. To install
    it, see the IBM official installation document.

**Additional Libraries**

A number of DPDK components, such as libraries and poll-mode drivers (PMDs) have additional dependencies.
For DPDK builds, the presence or absence of these dependencies will be automatically detected
enabling or disabling the relevant components appropriately.

In each case, the relevant library development package (``-devel`` or ``-dev``) is needed to build the DPDK components.

For libraries the additional dependencies include:

*   libarchive: for some unit tests using tar to get their resources.

*   libelf: to compile and use the bpf library.


Compile DPDK
-------------

Now we can compile the DPDK to check whether the DUT ENV is OK.

commands::

    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

if there are no errors occurred during the compilation and the DPDK apps have been generated,
it means the DUT ENV is OK now.

Check dpdk-testpmd::

    root@dpdk:~/dpdk# ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd --help
    EAL: Detected 72 lcore(s)
    EAL: Detected 2 NUMA nodes

    Usage: ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd [options]

    EAL common options:
      -c COREMASK         Hexadecimal bitmask of cores to run on
      -l CORELIST         List of cores to run on
    ...
    --match-allocations Free hugepages exactly as allocated

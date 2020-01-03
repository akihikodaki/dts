Configuring T-Rex for DPDK Test Suite
=====================================

DPDK can utilize T-Rex as a traffic generator in stateless Layer 2 mode.

An example T-Rex configuration that accomplishes this is shown as follows:

.. code-block:: console

  - port_limit: 2
    version: 2
    interfaces: ["03:00.0", "03:00.1"]
    port_info:
            - src_mac: "aa:bb:cc:dd:ee:ff"
              dest_mac: "ff:ee:dd:cc:bb:aa"
            - src_mac: "ff:ee:dd:cc:bb:aa"
              dest_mac: "aa:bb:cc:dd:ee:ff"

DTS may use a standalone T-Rex instance, or can be configured to start T-Rex
itself using the settings in ``pktgen.conf``.

To read more about T-Rex stateless mode, read the
`T-Rex stateless support guide <https://trex-tgn.cisco.com/trex/doc/trex_stateless.html>`__.

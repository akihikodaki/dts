.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2020 Intel Corporation

=================================================================================
Malicious driver event indication process in Intel® Ethernet 700 Series PF driver
=================================================================================

Need modify the testpmd APP to generate invalid packets in tx only mode

.. code-block:: console

    diff --git a/app/test-pmd/txonly.c b/app/test-pmd/txonly.c
    index 3caf281cb..448aab715 100644
    --- a/app/test-pmd/txonly.c
    +++ b/app/test-pmd/txonly.c
    @@ -299,6 +299,11 @@ pkt_burst_transmit(struct fwd_stream *fs)
            if (nb_pkt == 0)
                    return;
    
    +        for (nb_pkt = 0; nb_pkt < nb_pkt_per_burst; nb_pkt++){
    +                 pkts_burst[nb_pkt]->data_len = 15;
    +         }
    +
    +
            nb_tx = rte_eth_tx_burst(fs->tx_port, fs->tx_queue, pkts_burst, nb_pkt);
            /*
             * Retry if necessary


Test Case1:  Check log output when malicious driver events is detected
======================================================================
1. Generate i40e VF when PF is binded to igb_uio driver
    echo 1 > /sys/bus/pci/devices/0000\:18\:00.1/max_vfs

2. Launch PF by testpmd
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x03 -n 4 --file-prefix=test1 -a [pci of PF] -- -i
     
3. Launch VF by testpmd
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x03 -n 4 --file-prefix=lei1 -a [pci of VF] -- -i
    > set fwd txonly
    > start
    
4. Check the PF can detect the VF's unexpected behavior and output warning log
    testpmd>
    i40e_dev_alarm_handler(): ICR0: malicious programming detected
    i40e_handle_mdd_event(): Malicious Driver Detection event 0x00 on TX queue 65 PF number 0x01 VF number 0x40 device 0000:18:00.1
    i40e_handle_mdd_event(): TX driver issue detected on PF
    i40e_handle_mdd_event(): TX driver issue detected on VF 0 1times


Test Case2:  Check the event counter number for malicious driver events
=======================================================================
1. Generate i40e VF when PF is binded to igb_uio driver
    echo 1 > /sys/bus/pci/devices/0000\:18\:00.1/max_vfs

2. Launch PF by testpmd
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x03 -n 4 --file-prefix=test1 -a [pci of PF] -- -i

3. launch VF by testpmd and start txonly mode 3 times:
    repeat following step 3 times
    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x03 -n 4 --file-prefix=lei1 -a [pci of VF] -- -i
    > set fwd txonly
    > start
    > quit

4. Check the PF can detect the malicious driver events number directly in the log:
   i40e_handle_mdd_event(): TX driver issue detected on VF 0 3times

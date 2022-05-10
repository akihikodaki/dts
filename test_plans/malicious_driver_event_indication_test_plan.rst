.. Copyright (c) <2020>, Intel Corporation
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


=================
etgen replacement
=================
pktgen usage please refer to doc **pktgen_prog_guide.rst**.

import new class
----------------

#. import a new module::

.. code-block:: python

   from pktgen import PacketGeneratorHelper

initialize an instance in `def set_up_all(self)`
------------------------------------------------

.. code-block:: python

   def set_up_all(self):
   ...
      self.pktgen_helper = PacketGeneratorHelper()

create streams for pktgen instance
----------------------------------
each pcap file should only contain one packet.

.. code-block:: python

   pcap1 = os.sep.join([self.pktgen.output_path, "{0}.pcap".format(port)])
   flow1 = "Ether()/IP()/UDP()/("X")"
   self.tester.scapy_append('wrpcap("%s", [flow])' % (pcap1, flow1))
   self.tester.scapy_execute()

   pcap2 = os.sep.join([self.pktgen.output_path, "{0}.pcap".format(port)])
   flow2 = "Ether()/IP()/UDP()/("X")"
   self.tester.scapy_append('wrpcap("%s", [flow])' % (pcap2, flow2))
   self.tester.scapy_execute()

   tgen_input = []
   tgen_input.append([tx_port, rx_port, pcap1])
   tgen_input.append([tx_port, rx_port, pcap2])

pcap field variable(optional)
-----------------------------
If no protocol layer field vary requirement, ignore this content.

field key definition
~~~~~~~~~~~~~~~~~~~~

#. ip protocol layer::
   # protocol layer name
   'mac':  {
      # field name
      'src': {
         # field value vary range
         'range': 64,
         # field value vary step
         'step': 1,
         # action: inc/dec/random
         'action': 'inc'},
      'dst': {'range': 64, 'step': 1, 'action': 'inc'},
       }

#. mac protocol layer::
   # protocol layer name
   'mac':  {
      # field name
      'src': {
         # field value vary range
         'range': 64,
         # field value vary step
         'step': 1,
         # action: inc/dec/random
         'action': 'inc'},
      'dst': {'range': 64, 'step': 1, 'action': 'inc'},
       }

#. vlan protocol layer::
   # protocol layer name
   'vlan':  {
      '0': {
         # field value vary range
         'range': 64,
         # field value vary step
         'step': 1,
         # action: inc/dec/random
         'action': 'inc'},}

usage example
~~~~~~~~~~~~~

.. code-block:: python

   def set_up_all(self):
      ...
      self.pktgen_helper = PacketGeneratorHelper()
      ...

   def set_fields(self):
      fields_config = {
         'ip':  {
            'src': {'range': 64, 'action': 'inc'},
            'dst': {'action': 'random'}},}
      return fields_config

   def test_perf_xxxx(self):
      ...
      vm_config= self.set_fields() # optional
      # clear streams before add new streams
      self.tester.pktgen.clear_streams()
      # run packet generator
      ratePercent = 100
      streams = self.pktgen_helper.prepare_stream_from_tginput(
                         tgenInput, ratePercent, vm_config, self.tester.pktgen)
      _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
      ...

change etgen interface to pktgen interface
------------------------------------------
pktgen interface use the same input parameter/return value definition as
etgen interface.

throughput
~~~~~~~~~~

etgen::

.. code-block:: python

   self.tester.traffic_generator_throughput(tgen_input)

pktgen::

.. code-block:: python

   vm_config= self.set_fields() # optional
   # clear streams before add new streams
   self.tester.pktgen.clear_streams()
   # run packet generator
   ratePercent = 100
   streams = self.pktgen_helper.prepare_stream_from_tginput(
                        tgenInput, ratePercent, vm_config, self.tester.pktgen)
   _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)

loss
~~~~

etgen::

.. code-block:: python

   self.tester.traffic_generator_loss(tgen_input)

pktgen::

.. code-block:: python

   vm_config= self.set_fields() # optional
   # clear streams before add new streams
   self.tester.pktgen.clear_streams()
   # run packet generator
   ratePercent = 100
   streams = self.pktgen_helper.prepare_stream_from_tginput(
                              tgenInput, ratePercent, vm_config, self.tester.pktgen)
   result = self.tester.pktgen.measure_loss(stream_ids=streams)

latency
~~~~~~~

etgen::

.. code-block:: python

   self.tester.traffic_generator_latency(tgen_input)

pktgen::

.. code-block:: python

   vm_config= self.set_fields() # optional
   # clear streams before add new streams
   self.tester.pktgen.clear_streams()
   # run packet generator
   ratePercent = 100
   streams = self.pktgen_helper.prepare_stream_from_tginput(
                        tgenInput, ratePercent, vm_config, self.tester.pktgen)
   latencys = self.tester.pktgen.measure_latency(stream_ids=streams)

rfc2544
~~~~~~~

etgen::

.. code-block:: python

   self.tester.run_rfc2544(tgen_input)

pktgen::

.. code-block:: python

   vm_config= self.set_fields() # optional
   # clear streams before add new streams
   self.tester.pktgen.clear_streams()
   # run packet generator
   ratePercent = 100
   streams = self.pktgen_helper.prepare_stream_from_tginput(
                        tgenInput, ratePercent, vm_config, self.tester.pktgen)
   # set traffic option
   traffic_opt = {'pdr': 0.01, 'duration': 5}
   zero_loss_rate, tx_pkts, rx_pkts = \
     self.tester.pktgen.measure_rfc2544(stream_ids=streams, options=traffic_opt)
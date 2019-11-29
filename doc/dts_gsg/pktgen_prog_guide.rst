
=================
how to use pktgen
=================
these definition and usage pattern come from doc `pktgen-API-1.1.docx` and etgen
usage in dts. For trex(CISCO) rapid iterative development speed, we lack of
adequate manpower to keep up with it. Here we recommend to use trex v2.41/v2.42/v2.43
to run pktgen/trex.

add stream
==========
add stream in pktgen streams table.

one stream content including::

   tx_port: transmit port idx in tester.ports_info.
   rx_port: receive port idx in tester.ports_info.
   pcap: pcap file or Packet instance, Only support one packet in it.

.. code-block:: python

   tx_port = self.tester.get_local_port(dut_port_index1)
   rx_port = self.tester.get_local_port(dut_port_index2)

   stream_id = hPktgen.add_stream(tx_port, rx_port, pcap)

config stream
=============
configure a stream option.

definition
----------
Currently pktgen support ethernet/ipv4/vlan protocol layer some field vary with
increase/decrease/random value.

stream option contain::

   'pcap': network packet format
   'fields_config': protocol layer field behavior(optional)
   'stream_config': stream transmit behavior
   'flow_control': port flow control(optional)

pcap
++++
It is a network packet format. It can be a absolute path of pcap file or
an instance of scapy Packet. It should only contain one packet format.

.. code-block:: python

   Example 1:

      pcap = <Ether  dst=FF:FF:FF:FF:FF:FF src=00:00:00:00:00:00 type=IPv4 |<IP  frag=0 proto=udp src=0.0.0.1 dst=0.0.0.255 |<UDP  sport=22 dport=50 |<Raw  load='xxxxxxxxxxxxxxxxxx' |>>>>

   Example 2:

      pcap = "/root/xxx.pcap"

field option
++++++++++++
define every layer's field behavior.

'mac'
`````
'mac' is ethernet protocol layer name.

.. code-block:: python

   # field name
   'src': {
      # action: inc/dec/random
      'action':'inc',
      # field end value should be bigger than field start value
      'end':   '00:00:00:00:00:FF',
      # field start value
      'start': '00:00:00:00:00:02',
      # field value vary step
      'step': 1},
   'dst': {
      # action: inc/dec/random
      'action':'inc',
      # field end value should be bigger than field start value
      'end':   'ff:00:00:00:00:FF',
      # field start value
      'start': 'ff:00:00:00:00:02',
      # field value vary step
      'step': 1},

'ip'
````
'ip' is ip protocol layer name.

.. code-block:: python

   # field name
   'src': {
      # action: inc/dec/random
      'action': 'inc',
      # field end value should be bigger than field start value
      'end':   '16.0.0.16',
      # field start value
      'start': '16.0.0.1',
      # field value vary step
      'step': 1},
   # field name
   'dst': {
      # action: inc/dec/random
      'action': 'inc',
      # field end value should be bigger than field start value
      'end':   '48.0.0.255',
      # field start value
      'start': '48.0.0.1',
      # field value vary step
      'step': 1},

'vlan'
``````
'vlan' is vlan protocol layer name.

.. code-block:: python

   # internal vlan
   0: {
      # action: inc/dec/random
      'action': 'inc',
      # field end value should be bigger than field start value
      'end': 52,
      # field start value
      'start': 50,
      # field value vary step
      'step': 1},
   # external vlan
   1: {
      # action: inc/dec/random
      'action': 'inc',
      # field end value should be bigger than field start value
      'end': 52,
      # field start value
      'start': 50,
      # field value vary step
      'step': 1},

'stream_config'
+++++++++++++++
define a stream transmit behavior.

basic content including::

   'rate':  0 ~ 100 int type, port line rate should set it.
   'transmit_mode': TRANSMIT_CONT/TRANSMIT_S_BURST
       TRANSMIT_CONT define a continuous transmit.
       TRANSMIT_S_BURST define a burst transmit with custom number of packets.

.. code-block:: python

   from pktgen_base import TRANSMIT_CONT, TRANSMIT_S_BURST

   stream_config = {
       'rate': 100,
       # TRANSMIT_CONT define a continuous transmit.
       # TRANSMIT_S_BURST define a burst transmit with custom number of packets.
       'transmit_mode': TRANSMIT_CONT
   }

stream option examples
----------------------

normal stream option
++++++++++++++++++++
normal stream ignore `fields_config` configuration option.

.. code-block:: python

   Example 1:
      option = {
         'pcap': "/root/xxx.pcap",
         'stream_config': {
             'rate': 100,
             'transmit_mode': TRANSMIT_CONT}}

   Example 2:
      option = {
         'pcap': <Ether  dst=00:00:00:00:20:00 src=00:00:00:00:00:FF type=IPv4 |<IP  frag=0 proto=udp src=0.0.0.1 dst=0.0.0.255 |<UDP  sport=22 dport=50 |<Raw  load='xxxxxxxxxxxxxxxxxx' |>>>>,
         'stream_config': {
             'rate': 100,
             'transmit_mode': TRANSMIT_CONT}}

stream option with mac increase/decrease/random
+++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

   action = 'inc' or 'dec' or 'random'
   option = {
      'pcap': "/root/xxx.pcap",
      'fields_config': {
         'mac': {
            'dst': {
               'action': action,
               'end':   '00:00:00:00:20:00',
               'start': '00:00:00:00:00:FF',
               'step': 1},
            'src': {
               'action': action,
               'end':   '00:00:00:00:00:FF',
               'start': '00:00:00:00:00:02',
               'step': 1}}},
      'stream_config': {
            'rate': 100,
            'transmit_mode': TRANSMIT_CONT
            }
        }

stream option with ip increase/decrease/random
++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

   action = 'inc' or 'dec' or 'random'
   option = {
         'pcap': "/root/xxx.pcap",
         'fields_config': {
            'ip': {
               'dst': {
                  'action': action,
                  'end':   '48.0.0.255',
                  'start': '48.0.0.1',
                  'step': 1},
               'src': {
                  'action': action,
                  'end':   '16.0.0.16',
                  'start': '16.0.0.1',
                  'step': 1}}},
         'stream_config': {
             'rate': 100,
             'transmit_mode': TRANSMIT_CONT,
             }
         }

stream option with vlan increase/decrease/random
++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

   action = 'inc' or 'dec' or 'random'
   option = {
         'pcap': "/root/xxx.pcap",
         'fields_config': {
            'ip': {
               0: {
                  'action': action,
                  'end':   55,
                  'start': 50,
                  'step':  1},
         'stream_config': {
             'rate': 100,
             'transmit_mode': TRANSMIT_CONT,
             }
         }

burst stream option
+++++++++++++++++++

.. code-block:: python

   option = {
         'pcap': "/root/xxx.pcap",
         'stream_config': {
             'rate': 100,
             # set stream transmit mode
             'transmit_mode': TRANSMIT_S_BURST,
             'txmode' : {
                # total packets
                'total_pkts': 1000},
             }
         }

stream option with flow control
+++++++++++++++++++++++++++++++
flow control open (trex not supported)

.. code-block:: python

   option = {
      'flow_control': {
            # 0: disable flow control
            # 1: enable flow control
           'flag': 1},
      'pcap': "/root/xxx.pcap",
      'stream_config': {
          'rate': 100,
          'transmit_mode': TRANSMIT_CONT}}

measure
=======
pktgen measure_xxxx return value is the same as etgen, `measure_xxxx` and
`measure` are both supported. If traffic option is not set, use default values.

two usage examples of pktgen measure method
-------------------------------------------

.. code-block:: python

   Example 1:

      from pktgen import getPacketGenerator, PKTGEN_TREX

      hPktgen = getPacketGenerator(tester, PKTGEN_TREX)

      traffic_option = {'rate': 100}
      hPktgen.measure_throughput(stream_ids, traffic_opt)

   Example 2:

      from pktgen import getPacketGenerator, PKTGEN_TREX

      hPktgen = getPacketGenerator(tester, PKTGEN_TREX)

      traffic_option = {
         'method': 'throughput',
         'rate': 100
      }
      hPktgen.measure(stream_ids, traffic_opt)

throughput
----------
throughput testing scenario.

option
++++++
.. code-block:: python

   traffic_option = {
      # test method name, if use `measure_throughput`, ignore this key
      'method': 'throughput',
      # port rate percent, float(0--100), default value is 100.(reserved)
      'rate': 100,
      # warm up time before start main transmission. If it is set, it will start
      # a custom time transmission to make sure packet generator under good
      # status. It is an optional key.
      'delay': 5,
      # the interval time of get throughput statistic (second).
      # If set this key value, pktgen will return several throughput statistic
      # data in a duration. If not set this key value, only return one statistic
      # data. It is used coupled with `duration` option.
      'interval': 1,
      # this key works with ``interval`` key. If it is set, the callback
      # of suite level will be executed after getting throughput statistic.
      # callback method should define as below, don't add sleep in this method.
      'callback' : callback_method,
      # transmission lasting time(second), default value is 10 second.
      'duration': 5}

return value
++++++++++++
bps_rx_total: Received bits per second
pps_rx_total: Received packets per second

.. code-block:: python

   return_value = (bps_rx_total, pps_rx_total)

loss
----
loss rate testing scenario.

option
++++++

.. code-block:: python

   traffic_option = {
      # test method name, if use `measure_loss`, ignore this key
      'method': 'loss',
      # port rate percent, float(0--100), default value is 100.(reserved)
      'rate': 100,
      # warm up time before start main transmission. If it is set, it will start
      # a custom time transmission to make sure packet generator under good
      # status. It is an optional key.
      'delay': 5,
      # transmission lasting time(second), default value is 10 second.
      'duration': 5}

return value
++++++++++++

.. code-block:: python

   loss_stats = (loss_rate, tx_pkts, rx_pkts)

latency
-------
latency testing scenario.

option
++++++

.. code-block:: python

   traffic_option = {
      # test method name, if use `measure_latency`, ignore this key
      'method': 'latency',
      # port rate percent, float(0--100), default value is 100.(reserved)
      'rate': 100,
      # warm up time before start main transmission. If it is set, it will start
      # a custom time transmission to make sure packet generator under ready
      # status. It is an optional key.
      'delay': 5,
      # transmission lasting time(second), default value is 10 second.
      'duration': 5}

return value
++++++++++++

.. code-block:: python

   latency_stats = { 'min':     15,
                     'max':     15,
                     'average': 15,}

rfc2544 option
--------------
rfc2544 testing scenario by decreasing step.

option
++++++

.. code-block:: python

   traffic_option = {
      # test method name, if use `measure_rfc2544`, ignore this key.
      'method': 'rfc2544',
      # port rate percent at first round testing, 0 ~ 100, default is 100.
      'rate': 100,
      # permit packet drop rate, default is 0.001.
      'pdr': 0.001,
      # port rate percent drop step, 0 ~ 100 , default is 1.
      'drop_step': 1,
      # warm up time before start main transmission. If it is set, it will start
      # a custom time transmission to make sure packet generator under ready
      # status. It is an optional key.
      'delay': 5,
      # transmission lasting time(second), default value is 10 second.
      'duration': 5}

return value
++++++++++++

.. code-block:: python

   loss_stats = (loss_rate, tx_pkts, rx_pkts)

rfc2544_dichotomy option
------------------------
rfc2544 testing scenario using dichotomy algorithm.

option
++++++

.. code-block:: python

   traffic_option = {
      # test method name, if use `measure_rfc2544_dichotomy` method, ignore this key.
      'method': 'rfc2544_dichotomy',
      # dichotomy algorithm lower bound rate percent, default is 0.
      'min_rate': 0,
      # dichotomy algorithm upper bound rate percent, default is 100.
      'max_rate': 100,
      # dichotomy algorithm accuracy, default 0.001.
      'accuracy': 0.001,
      # permit packet drop rate, default is 0.001.
      'pdr': 0.001,
      # warm up time before start main transmission. If it is set, it will start
      # a custom time transmission to make sure packet generator under ready
      # status. It is an optional key.
      'delay': 5,
      # transmission lasting time(second), default value is 10 second.
      'duration': 10}

return value
++++++++++++

.. code-block:: python

   loss_stats = (loss_rate, tx_pkts, rx_pkts)


reference example
=================
This example show how to use pktgen in suite script. In fact, most scenario are
more simpler than this. Part of code is pseudo code and it can't be ran directly.

testing scenario::

   create four streams on two links, each link attach two streams. On one link,
   one stream set mac src increase and packet format is a pcap file, the other
   stream set ip src random / dst decrease and packet format is a scapy Packet
   instance. All streams use continuous transmit and run rfc2544 scenario using
   trex packet generator.

.. code-block:: python

   # import pktgen lib
   from pktgen import getPacketGenerator, PKTGEN_TREX, TRANSMIT_CONT

   # create a pktgen instance
   hPktgen = getPacketGenerator(tester, PKTGEN_TREX)

   # create packet
   pcap1 = <Ether  dst=FF:FF:FF:FF:FF:FF src=00:00:00:00:00:00 type=IPv4 |<IP  frag=0 proto=udp src=0.0.0.1 dst=0.0.0.255 |<UDP  sport=22 dport=50 |<Raw  load='xxxxxxxxxxxxxxxxxx' |>>>>
   pcap2 = "/root/xxx.pcap"

   # attach stream to pktgen
   stream_ids = []
   tx_port1 = self.tester.get_local_port(dut_port_index1)
   rx_port1 = self.tester.get_local_port(dut_port_index2)
   stream_id_1 = hPktgen.add_stream(tx_port1, rx_port1, pcap1)
   stream_id_2 = hPktgen.add_stream(tx_port1, rx_port1, pcap2)
   stream_ids.append(stream_id_1)
   stream_ids.append(stream_id_2)

   tx_port2 = self.tester.get_local_port(dut_port_index2)
   rx_port2 = self.tester.get_local_port(dut_port_index1)
   stream_id_3 = hPktgen.add_stream(tx_port2, rx_port2, pcap1)
   stream_id_4 = hPktgen.add_stream(tx_port2, rx_port2, pcap2)
   stream_ids.append(stream_id_3)
   stream_ids.append(stream_id_4)

   # set pcap1 with mac protocol layer field vary configuration
   stream_option1 = {
      'pcap': pcap1,
      'fields_config': {
         'mac': {
            'src': {
               'action': 'inc',
               'end':   '00:00:00:00:00:FF',
               'start': '00:00:00:00:00:00',
               'step': 1}}},
        'stream_config': {
            'rate': 100,
            'transmit_mode': TRANSMIT_CONT
            }
        }
   # set stream option
   hPktgen.config_stream(stream_id_1, stream_option1)
   hPktgen.config_stream(stream_id_3, stream_option1)

   # set pcap2 with ip protocol layer field vary configuration
   stream_option2 = {
      'pcap': pcap2,
      'fields_config': {
         'ip': {
            'dst': {
               'action': 'dec',
               'end':   '0.0.0.255',
               'start': '0.0.0.1',
               'step': 1},
            'src': {
               'action': 'random',
               'end':   '0.0.0.64',
               'start': '0.0.0.1',
               'step': 1}}},
        'stream_config': {
            'rate': 100,
            'transmit_mode': TRANSMIT_CONT
            }
        }
   # set stream option
   hPktgen.config_stream(stream_id_2, stream_option2)
   hPktgen.config_stream(stream_id_4, stream_option2)

   # run testing scenario
   traffic_option = {
      'method':    'rfc2544',
      'rate':      100,
      'pdr':       0.001,
      'drop_step': 1}

   hPktgen.measure(stream_ids, traffic_opt)
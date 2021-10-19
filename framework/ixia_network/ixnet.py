# BSD LICENSE
#
# Copyright(c) 2010-2021 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
This module implant from pei,yulong ixNetwork tool.
"""

import csv
import json
import os
import re
import time
from collections import OrderedDict
from datetime import datetime

import requests

from .ixnet_stream import IxnetConfigStream

# local lib deps
from .packet_parser import PacketParser


class IxnetTrafficGenerator(object):
    """ixNetwork Traffic Generator."""
    json_header = {'content-type': 'application/json'}

    def __init__(self, config, logger):
        # disable SSL warnings
        requests.packages.urllib3.disable_warnings()
        self.logger = logger
        self.tg_ip = config.tg_ip
        self.tg_ports = config.tg_ports
        port = config.tg_ip_port or '11009'
        # id will always be 1 when using windows api server
        self.api_server = 'http://{0}:{1}'.format(self.tg_ip, port)
        self.session = requests.session()
        self.session_id = self.get_session_id(self.api_server)
        self.session_url = "{0}/api/v1/sessions/{1}".format(
            self.api_server, self.session_id)
        # initialize ixNetwork
        self.new_blank_config()
        self.tg_vports = self.assign_ports(self.tg_ports)

    def get_session_id(self, api_server):
        url = '{server}/api/v1/sessions'.format(server=api_server)
        response = self.session.post(
            url, headers=self.json_header, verify=False)
        session_id = response.json()['links'][0]['href'].split('/')[-1]
        msg = "{0}: Session ID is {1}".format(api_server, session_id)
        self.logger.info(msg)
        return session_id

    def destroy_config(self, name):
        json_header = {
            'content-type': 'application/json',
            'X-HTTP-Method-Override': 'DELETE',
        }
        response = self.session.post(name, headers=json_header, verify=False)
        return response

    def __get_ports(self):
        """Return available tg vports list"""
        return self.tg_vports

    def disable_port_misdirected(self):
        msg = 'close mismatched flag'
        self.logger.debug(msg)
        url = "{0}/ixnetwork/traffic".format(self.session_url)
        data = {
            "detectMisdirectedOnAllPorts": False,
            "disablePortLevelMisdirected": True,
        }
        response = self.session.patch(
            url, data=json.dumps(data), headers=self.json_header, verify=False)

    def delete_session(self):
        """delete session after test done"""
        try:
            url = self.session_url
            response = self.destroy_config(url)
            self.logger.debug("STATUS CODE: %s" % response.status_code)
        except requests.exceptions.RequestException as err_msg:
            raise Exception('DELETE error: {0}\n'.format(err_msg))

    def configure_streams(self, pkt, field_config=None):
        hParser = PacketParser()
        hParser._parse_pcap(pkt)
        hConfig = IxnetConfigStream(
            hParser.packetLayers, field_config, hParser.framesize)
        return hConfig.ixnet_packet

    def regenerate_trafficitems(self, trafficItemList):
        """
        Parameter
            trafficItemList: ['/api/v1/sessions/1/ixnetwork/traffic/trafficItem/1', ...]
        """
        url = "{0}/ixnetwork/traffic/trafficItem/operations/generate".format(
            self.session_url)
        data = {"arg1": trafficItemList}
        self.logger.info('Regenerating traffic items: %s' % trafficItemList)
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        self.wait_for_complete(response, url + '/' + response.json()['id'])

    def apply_traffic(self):
        """Apply the configured traffic."""
        url = "{0}/ixnetwork/traffic/operations/apply".format(self.session_url)
        data = {"arg1": f"/api/v1/sessions/{self.session_id}/ixnetwork/traffic"}
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        self.wait_for_complete(response, url + '/' + response.json()['id'])

    def start_traffic(self):
        """start the configured traffic."""
        self.logger.info("Traffic starting...")
        url = "{0}/ixnetwork/traffic/operations/start".format(self.session_url)
        data = {"arg1": f"/api/v1/sessions/{self.session_id}/ixnetwork/traffic"}
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        self.check_traffic_state(
            expectedState=['started', 'startedWaitingForStats'], timeout=45)
        self.logger.info("Traffic started Successfully.")

    def stop_traffic(self):
        """stop the configured traffic."""
        url = "{0}/ixnetwork/traffic/operations/stop".format(self.session_url)
        data = {"arg1": f"/api/v1/sessions/{self.session_id}/ixnetwork/traffic"}
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        self.check_traffic_state(
            expectedState=['stopped', 'stoppedWaitingForStats'])
        time.sleep(5)

    def check_traffic_state(self, expectedState=['stopped'], timeout=45):
        """
        Description
            Check the traffic state for the expected state.

        Traffic states are:
            startedWaitingForStats, startedWaitingForStreams, started, stopped,
            stoppedWaitingForStats, txStopWatchExpected, locked, unapplied

        Parameters
            expectedState = Input a list of expected traffic state.
                            Example: ['started', startedWaitingForStats']
            timeout = The amount of seconds you want to wait for the expected traffic state.
                      Defaults to 45 seconds.
                      In a situation where you have more than 10 pages of stats, you will
                      need to increase the timeout time.
        """
        if type(expectedState) != list:
            expectedState.split(' ')

        self.logger.info(
            'check_traffic_state: expecting traffic state {0}'.format(expectedState))
        for counter in range(1, timeout + 1):
            url = "{0}/ixnetwork/traffic".format(self.session_url)
            response = self.session.get(
                url, headers=self.json_header, verify=False)
            current_traffic_state = response.json()['state']
            self.logger.info('check_traffic_state: {trafficstate}: Waited {counter}/{timeout} seconds'.format(
                trafficstate=current_traffic_state,
                counter=counter,
                timeout=timeout))
            if counter < timeout and current_traffic_state not in expectedState:
                time.sleep(1)
                continue
            if counter < timeout and current_traffic_state in expectedState:
                time.sleep(8)
                self.logger.info(
                    'check_traffic_state: got expected [ %s ], Done' % current_traffic_state)
                return 0

        raise Exception(
            'Traffic state did not reach the expected state (%s):' % expectedState)

    def _get_stats(self, viewName='Flow Statistics', csvFile=None, csvEnableFileTimestamp=False):
        """
         sessionUrl: http://10.219.x.x:11009/api/v1/sessions/1/ixnetwork

         csvFile = None or <filename.csv>.
                   None will not create a CSV file.
                   Provide a <filename>.csv to record all stats to a CSV file.
                   Example: _get_stats(sessionUrl, csvFile='Flow_Statistics.csv')

         csvEnableFileTimestamp = True or False. If True, timestamp will be appended to the filename.

         viewName options (Not case sensitive):

            'Port Statistics'
            'Tx-Rx Frame Rate Statistics'
            'Port CPU Statistics'
            'Global Protocol Statistics'
            'Protocols Summary'
            'Port Summary'
            'OSPFv2-RTR Drill Down'
            'OSPFv2-RTR Per Port'
            'IPv4 Drill Down'
            'L2-L3 Test Summary Statistics'
            'Flow Statistics'
            'Traffic Item Statistics'
            'IGMP Host Drill Down'
            'IGMP Host Per Port'
            'IPv6 Drill Down'
            'MLD Host Drill Down'
            'MLD Host Per Port'
            'PIMv6 IF Drill Down'
            'PIMv6 IF Per Port'

         Note: Not all of the viewNames are listed here. You have to get the exact names from
               the IxNetwork GUI in statistics based on your protocol(s).

         Return you a dictionary of all the stats: statDict[rowNumber][columnName] == statValue
           Get stats on row 2 for 'Tx Frames' = statDict[2]['Tx Frames']
        """
        url = "{0}/ixnetwork/statistics/view".format(self.session_url)
        viewList = self.session.get(
            url, headers=self.json_header, verify=False)
        views = ['{0}/{1}'.format(url, str(i['id'])) for i in viewList.json()]

        for view in views:
            # GetAttribute
            response = self.session.get(
                view, headers=self.json_header, verify=False)
            if response.status_code != 200:
                raise Exception('getStats: Failed: %s' % response.text)
            captionMatch = re.match(viewName, response.json()['caption'], re.I)
            if captionMatch:
                # viewObj: sessionUrl + /statistics/view/11'
                viewObj = view
                break

        self.logger.info("viewName: %s, %s" % (viewName, viewObj))

        try:
            response = self.session.patch(viewObj, data=json.dumps(
                {'enabled': 'true'}), headers=self.json_header, verify=False)
        except Exception as e:
            raise Exception('get_stats error: No stats available')

        for counter in range(0, 31):
            response = self.session.get(
                viewObj + '/page', headers=self.json_header, verify=False)
            totalPages = response.json()['totalPages']
            if totalPages == 'null':
                self.logger.info(
                    'Getting total pages is not ready yet. Waiting %d/30 seconds' % counter)
                time.sleep(1)
            if totalPages != 'null':
                break
            if totalPages == 'null' and counter == 30:
                raise Exception('getStats: failed to get total pages')

        if csvFile is not None:
            csvFileName = csvFile.replace(' ', '_')
            if csvEnableFileTimestamp:
                timestamp = datetime.now().strftime('%H%M%S')
                if '.' in csvFileName:
                    csvFileNameTemp = csvFileName.split('.')[0]
                    csvFileNameExtension = csvFileName.split('.')[1]
                    csvFileName = csvFileNameTemp + '_' + \
                        timestamp + '.' + csvFileNameExtension
                else:
                    csvFileName = csvFileName + '_' + timestamp

            csvFile = open(csvFileName, 'w')
            csvWriteObj = csv.writer(csvFile)

        # Get the stat column names
        columnList = response.json()['columnCaptions']
        if csvFile is not None:
            csvWriteObj.writerow(columnList)

        statDict = {}
        flowNumber = 1
        # Get the stat values
        for pageNumber in range(1, totalPages + 1):
            self.session.patch(viewObj + '/page', data=json.dumps(
                {'currentPage': pageNumber}), headers=self.json_header, verify=False)
            response = self.session.get(
                viewObj + '/page', headers=self.json_header, verify=False)
            statValueList = response.json()['pageValues']
            for statValue in statValueList:
                if csvFile is not None:
                    csvWriteObj.writerow(statValue[0])

                self.logger.info('Row: %d' % flowNumber)
                statDict[flowNumber] = {}
                index = 0
                for statValue in statValue[0]:
                    statName = columnList[index]
                    statDict[flowNumber].update({statName: statValue})
                    self.logger.info('%s: %s' % (statName, statValue))
                    index += 1
                flowNumber += 1

        if csvFile is not None:
            csvFile.close()
        return statDict
        # Flow Statistics dictionary output example
        """
        Flow: 50
            Tx Port: Ethernet - 002
            Rx Port: Ethernet - 001
            Traffic Item: OSPF T1 to T2
            Source/Dest Value Pair: 2.0.21.1-1.0.21.1
            Flow Group: OSPF T1 to T2-FlowGroup-1 - Flow Group 0002
            Tx Frames: 35873
            Rx Frames: 35873
            Frames Delta: 0
            Loss %: 0
            Tx Frame Rate: 3643.5
            Rx Frame Rate: 3643.5
            Tx L1 Rate (bps): 4313904
            Rx L1 Rate (bps): 4313904
            Rx Bytes: 4591744
            Tx Rate (Bps): 466368
            Rx Rate (Bps): 466368
            Tx Rate (bps): 3730944
            Rx Rate (bps): 3730944
            Tx Rate (Kbps): 3730.944
            Rx Rate (Kbps): 3730.944
            Tx Rate (Mbps): 3.731
            Rx Rate (Mbps): 3.731
            Store-Forward Avg Latency (ns): 0
            Store-Forward Min Latency (ns): 0
            Store-Forward Max Latency (ns): 0
            First TimeStamp: 00:00:00.722
            Last TimeStamp: 00:00:10.568
        """

    def new_blank_config(self):
        """
        Start a new blank configuration.
        """
        url = "{0}/ixnetwork/operations/newconfig".format(self.session_url)
        self.logger.info('newBlankConfig: %s' % url)
        response = self.session.post(url, verify=False)
        url = "{0}/{1}".format(url, response.json()['id'])
        self.wait_for_complete(response, url)

    def wait_for_complete(self, response='', url='', timeout=120):
        """
        Wait for an operation progress to complete.
        response: The POST action response.
        """
        if response.json() == '' and response.json()['state'] == 'SUCCESS':
            self.logger.info('State: SUCCESS')
            return

        if response.json() == []:
            raise Exception('waitForComplete: response is empty.')

        if 'errors' in response.json():
            raise Exception(response.json()["errors"][0])

        if response.json()['state'] in ["ERROR", "EXCEPTION"]:
            raise Exception('WaitForComplete: STATE=%s: %s' %
                            (response.json()['state'], response.text))

        self.logger.info("%s" % url)
        self.logger.info("State: %s" % (response.json()["state"]))
        while response.json()["state"] == "IN_PROGRESS" or response.json()["state"] == "down":
            if timeout == 0:
                raise Exception('%s' % response.text)
            time.sleep(1)
            response = self.session.get(
                url, headers=self.json_header, verify=False)
            self.logger.info("State: %s" % (response.json()["state"]))
            if response.json()["state"] == 'SUCCESS':
                return
            timeout = timeout - 1

    def create_vports(self, portList=None, rawTrafficVport=True):
        """
        This creates virtual ports based on a portList.
        portList:  Pass in a list of ports in the format of ixChassisIp, slotNumber, portNumber
          portList = [[ixChassisIp, '1', '1'],
                      [ixChassisIp, '2', '1']]
        rawTrafficVport = For raw Traffic Item src/dest endpoints, vports must be in format:
                               /api/v1/sessions1/vport/{id}/protocols
        Next step is to call assign_port.
        Return: A list of vports
        """
        createdVportList = []
        for index in range(0, len(portList)):
            url = "{0}/ixnetwork/vport".format(self.session_url)

            card = portList[index][1]
            port = portList[index][2]
            portNumber = str(card) + '/' + str(port)
            self.logger.info('Name: %s' % portNumber)
            data = {'name': portNumber}
            response = self.session.post(
                url, data=json.dumps(data), headers=self.json_header, verify=False)
            vportObj = response.json()['links'][0]['href']
            self.logger.info('createVports: %s' % vportObj)
            if rawTrafficVport:
                createdVportList.append(vportObj + '/protocols')
            else:
                createdVportList.append(vportObj)

        if createdVportList == []:
            raise Exception('No vports created')

        self.logger.info('createVports: %s' % createdVportList)
        return createdVportList

    def assign_ports(self, portList, createVports=True, rawTraffic=True, timeout=90):
        """
        Description
            Use this to assign physical ports to the virtual ports.

        Parameters
            portList: [ [ixChassisIp, '1','1'], [ixChassisIp, '1','2'] ]
            vportList: list return by create_vports.
            timeout: Timeout for port up.

        Syntaxes
            POST: http://{apiServerIp:port}/api/v1/sessions/{id}/ixnetwork/operations/assignports
                  data={arg1: [{arg1: ixChassisIp, arg2: 1, arg3: 1}, {arg1: ixChassisIp, arg2: 1, arg3: 2}],
                        arg2: [],
                        arg3: ['/api/v1/sessions/{1}/ixnetwork/vport/1',
                               '/api/v1/sessions/{1}/ixnetwork/vport/2'],
                        arg4: true}  <-- True will clear port ownership
                  headers={'content-type': 'application/json'}
            GET:  http://{apiServerIp:port}/api/v1/sessions/{id}/ixnetwork/operations/assignports/1
                  data={}
                  headers={}
            Expecting:   RESPONSE:  SUCCESS
        """
        if createVports:
            vportList = self.create_vports(portList, rawTrafficVport=False)
        url = "{0}/ixnetwork/operations/assignports".format(self.session_url)
        data = {"arg1": [], "arg2": [], "arg3": vportList, "arg4": "true"}
        [data["arg1"].append({"arg1": str(chassis), "arg2": str(
            card), "arg3": str(port)}) for chassis, card, port in portList]
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        self.logger.info('%s' % response.json())
        url = "{0}/{1}".format(url, response.json()['id'])
        self.wait_for_complete(response, url)

        for vport in vportList:
            url = "{0}{1}/l1Config".format(self.api_server, vport)
            response = self.session.get(
                url, headers=self.json_header, verify=False)
            url = url + '/' + response.json()['currentType']
            data = {"enabledFlowControl": False}
            response = self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

        if rawTraffic:
            vportList_protocol = []
            for vport in vportList:
                vportList_protocol.append(vport + '/protocols')
            self.logger.info('vports: %s' % vportList_protocol)
            return vportList_protocol
        else:
            self.logger.info('vports: %s' % vportList)
            return vportList

    def destroy_assign_ports(self, vportList):
        msg = "release {}".format(vportList)
        self.logger.info(msg)
        for vport_url in vportList:
            url = self.api_server + "/".join(vport_url.split("/")[:-1])
            self.destroy_config(url)

    def config_config_elements(self, config_element_obj, config_elements):
        """
        Parameters
        config_element_obj: /api/v1/sessions/1/ixnetwork/traffic/trafficItem/{id}/configElement/{id}
        """
        url = self.api_server + config_element_obj + '/transmissionControl'
        if 'transmissionType' in config_elements:
            data = {'type': config_elements['transmissionType']}
            self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

        if 'burstPacketCount' in config_elements:
            data = {
                'burstPacketCount': int(config_elements['burstPacketCount'])}
            self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

        if 'frameCount' in config_elements:
            data = {'frameCount': int(config_elements['frameCount'])}
            self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

        if 'duration' in config_elements:
            data = {'duration': int(config_elements['duration'])}
            self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

        url = self.api_server + config_element_obj + '/frameRate'
        if 'frameRate' in config_elements:
            data = {'rate': int(config_elements['frameRate'])}
            self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

        if 'frameRateType' in config_elements:
            data = {'type': config_elements['frameRateType']}
            self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

        url = self.api_server + config_element_obj + '/frameSize'
        if 'frameSize' in config_elements:
            data = {'fixedSize': int(config_elements['frameSize'])}
            self.session.patch(
                url, data=json.dumps(data), headers=self.json_header, verify=False)

    def import_json_config_obj(self, data_obj):
        """
        Parameter
            data_obj: The JSON config object.
        Note
            arg2 value must be a string of JSON data: '{"xpath": "/traffic/trafficItem[1]", "enabled": false}'
        """
        data = {"arg1": "/api/v1/sessions/1/ixnetwork/resourceManager",
                "arg2": json.dumps(data_obj),
                "arg3": False}
        url = "{0}/ixnetwork/resourceManager/operations/importconfig".format(
            self.session_url)
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        url = "{0}/{1}".format(url, response.json()['id'])
        self.wait_for_complete(response, url)

    def send_rfc2544_throughput(self, options):
        """Send traffic per RFC2544 throughput test specifications.
        Send packets at a variable rate, using ``traffic_list`` configuration,
        until minimum rate at which no packet loss is detected is found.
        """
        # new added parameters
        duration = options.get('duration') or 10
        initialBinaryLoadRate = max_rate = options.get('max_rate') or 100.0
        min_rate = options.get('min_rate') or 0.0
        accuracy = options.get('accuracy') or 0.001
        permit_loss_rate = options.get('pdr') or 0.0
        # old parameters
        traffic_list = options.get('traffic_list')
        if traffic_list is None:
            raise Exception('traffic_list is empty.')

        # close port mismatched statistics
        self.disable_port_misdirected()

        url = "{0}/ixnetwork/traffic/trafficItem".format(self.session_url)
        response = self.session.get(
            url, headers=self.json_header, verify=False)
        if response.json() != []:
            for item in response.json():
                url = "{0}{1}".format(
                    self.api_server, item['links'][0]['href'])
                response = self.destroy_config(url)
                if response.status_code != 200:
                    raise Exception("remove trafficitem failed")

        trafficitem_list = []
        index = 0
        for traffic in traffic_list:
            index = index + 1
            # create trafficitem
            url = "{0}/ixnetwork/traffic/trafficItem".format(self.session_url)
            data = {"name": "Traffic Item " + str(index), "trafficType": "raw"}
            response = self.session.post(
                url, data=json.dumps(data), headers=self.json_header, verify=False)
            trafficitem_obj = response.json()['links'][0]['href']
            self.logger.info('create traffic item: %s' % trafficitem_obj)
            trafficitem_list.append(trafficitem_obj)
            # create endpointset
            url = "{0}{1}/endpointSet".format(self.api_server, trafficitem_obj)
            data = {
                "sources": [traffic[0]],
                "destinations": [traffic[1]]
            }
            response = self.session.post(
                url, data=json.dumps(data), headers=self.json_header, verify=False)
            # packet config
            config_stack_obj = eval(
                str(traffic[2]).replace('trafficItem[1]', 'trafficItem[' + str(index) + ']'))
            self.import_json_config_obj(config_stack_obj)
            # get framesize
            url = "{0}{1}/configElement/1/frameSize".format(
                self.api_server, trafficitem_obj)
            response = self.session.get(
                url, headers=self.json_header, verify=False)
            frame_size = response.json()['fixedSize']

        self.regenerate_trafficitems(trafficitem_list)

        # query existing quick test
        url = "{0}/ixnetwork/quickTest/rfc2544throughput".format(
            self.session_url)
        response = self.session.get(
            url, headers=self.json_header, verify=False)
        if response.json() != []:
            for qt in response.json():
                url = "{0}{1}".format(self.api_server, qt['links'][0]['href'])
                response = self.destroy_config(url)
                if response.status_code != 200:
                    raise Exception("remove quick test failed")
        # create quick test
        url = "{0}/ixnetwork/quickTest/rfc2544throughput".format(
            self.session_url)
        data = [{"name": "QuickTest1", "mode": "existingMode"}]
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        quicktest_obj = response.json()['links'][0]['href']
        self.logger.info('create quick test: %s' % quicktest_obj)
        # add trafficitems
        url = "{0}{1}/trafficSelection".format(self.api_server, quicktest_obj)
        data = [{"__id__": item_obj} for item_obj in trafficitem_list]
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        self.logger.info("add traffic item status: %s" % response.content)
        # modify quick test config
        url = "{0}{1}/testConfig".format(self.api_server, quicktest_obj)
        data = {
            # If Enabled, The minimum size of the frame is used .
            "enableMinFrameSize": True,
            # This attribute is the frame size mode for the Quad Gaussian.
            # Possible values includes:
            "frameSizeMode": "custom",
            # The list of the available frame size.
            "framesizeList": [str(frame_size)],
            # The minimum delay between successive packets.
            "txDelay": 5,
            # Specifies the amount of delay after every transmit
            "delayAfterTransmit": 5,
            # sec
            "duration": duration,
            # The initial binary value of the load rate
            "initialBinaryLoadRate": initialBinaryLoadRate,
            # The upper bound of the iteration rates for each frame size during
            # a binary search
            "maxBinaryLoadRate": max_rate,
            # Specifies the minimum rate of the binary algorithm.
            "minBinaryLoadRate": min_rate,
            # The frame loss unit for traffic in binary.
            # Specifies the resolution of the iteration. The difference between
            # the real rate transmission in two consecutive iterations, expressed
            # as a percentage, is compared with the resolution value. When the
            # difference is smaller than the value specified for the
            # resolution, the test stops .
            "resolution": accuracy * 100,
            # The load unit value in binary.
            "binaryFrameLossUnit": "%",
            # The binary tolerance level.
            "binaryTolerance": permit_loss_rate,
        }
        response = self.session.patch(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        if response.status_code != 200:
            raise Exception("change quick test config failed")
        # run the quick test
        url = "{0}{1}/operations/run".format(self.api_server, quicktest_obj)
        data = {"arg1": quicktest_obj, "arg2": ""}
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)
        url = url + '/' + response.json()['id']
        state = response.json()["state"]
        self.logger.info("Quicktest State: %s" % state)
        while state == "IN_PROGRESS":
            response = self.session.get(
                url, headers=self.json_header, verify=False)
            state = response.json()["state"]
            self.logger.info("Quicktest State: %s" % state)
            time.sleep(5)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        copy_to_path = os.sep.join([
            self.OUTPUT_DIR,
            'ixnet' + datetime.now().strftime("%Y%m%d_%H%M%S")])
        if not os.path.exists(copy_to_path):
            os.makedirs(copy_to_path)
        self.get_quicktest_csvfiles(quicktest_obj, copy_to_path, csvfile='all')
        qt_result_csv = "{0}/AggregateResults.csv".format(copy_to_path)
        return self.parse_quicktest_results(qt_result_csv)

    def parse_quicktest_results(self, path_file):
        """ parse csv filte and return quicktest result """
        results = OrderedDict()

        if not os.path.exists(path_file):
            msg = "failed to get result file from windows api server"
            self.logger.error(msg)
            return results

        ret_result = []
        with open(path_file, "r") as f:
            qt_result = csv.DictReader(f)
            for row in qt_result:
                ret_result.append(row)
                results['framesize'] = row['Framesize']
                results['throughput'] = row['Agg Rx Throughput (fps)']
                results['linerate%'] = row['Agg Rx Throughput (% Line Rate)']
                results['min_latency'] = row['Min Latency (ns)']
                results['max_latency'] = row['Max Latency (ns)']
                results['avg_latency'] = row['Avg Latency (ns)']

        return ret_result

    def get_quicktest_resultpath(self, quicktest_obj):
        """
        quicktest_obj = /api/v1/sessions/1/ixnetwork/quickTest/rfc2544throughput/2
        """
        url = "{0}{1}/results".format(self.api_server, quicktest_obj)
        response = self.session.get(
            url, headers=self.json_header, verify=False)
        return response.json()['resultPath']

    def get_quicktest_csvfiles(self, quicktest_obj, copy_to_path, csvfile='all'):
        """
        Description
            Copy Quick Test CSV result files to a specified path on either Windows or Linux.
            Note: Currently only supports copying from Windows.
        quicktest_obj: The Quick Test handle.
        copy_to_path: The destination path to copy to.
                    If copy to Windows: c:\\Results\\Path
                    If copy to Linux: /home/user1/results/path
        csvfile: A list of CSV files to get: 'all', one or more CSV files to get:
                 AggregateResults.csv, iteration.csv, results.csv, logFile.txt, portMap.csv
        """
        results_path = self.get_quicktest_resultpath(quicktest_obj)
        self.logger.info('get_quickTest_csvfiles: %s' % results_path)
        if csvfile == 'all':
            get_csv_files = [
                'AggregateResults.csv', 'iteration.csv', 'results.csv', 'logFile.txt', 'portMap.csv']
        else:
            if type(csvfile) is not list:
                get_csv_files = [csvfile]
            else:
                get_csv_files = csvfile

        for each_csvfile in get_csv_files:
            # Backslash indicates the results resides on a Windows OS.
            if '\\' in results_path:
                cnt = 0
                while cnt < 5:
                    try:
                        self.copyfile_windows2linux(
                            results_path + '\\{0}'.format(each_csvfile), copy_to_path)
                        break
                    except Exception as e:
                        time.sleep(5)
                        cnt += 1
                        msg = "No.{} retry to get result from windows".format(cnt)
                        self.logger.warning(msg)
                        continue
            else:
                # TODO:Copy from Linux to Windows and Linux to Linux.
                pass

    def copyfile_windows2linux(self, winPathFile, linuxPath, includeTimestamp=False):
        """
        Description
            Copy files from the IxNetwork API Server c: drive to local Linux filesystem.
            You could also include a timestamp for the destination file.
        Parameters
            winPathFile: (str): The full path and filename to retrieve from Windows client.
            linuxPath: (str): The Linux destination path to put the file to.
            includeTimestamp: (bool):  If False, each time you copy the same file will be overwritten.
        Syntax
            post: /api/v1/sessions/1/ixnetwork/operations/copyfile
            data: {'arg1': winPathFile, 'arg2': '/api/v1/sessions/1/ixnetwork/files/'+fileName'}
        """
        self.logger.info('copyfile From: %s to %s' % (winPathFile, linuxPath))
        fileName = winPathFile.split('\\')[-1]
        fileName = fileName.replace(' ', '_')
        destinationPath = '/api/v1/sessions/1/ixnetwork/files/' + fileName
        currentTimestamp = datetime.now().strftime('%H%M%S')

        # Step 1 of 2:
        url = "{0}/ixnetwork/operations/copyfile".format(self.session_url)
        data = {"arg1": winPathFile, "arg2": destinationPath}
        response = self.session.post(
            url, data=json.dumps(data), headers=self.json_header, verify=False)

        # Step 2 of 2:
        url = "{0}/ixnetwork/files/{1}".format(self.session_url, fileName)
        requestStatus = self.session.get(
            url, stream=True, headers=self.json_header, verify=False)
        if requestStatus.status_code == 200:
            contents = requestStatus.raw.read()

            if includeTimestamp:
                tempFileName = fileName.split('.')
                if len(tempFileName) > 1:
                    extension = fileName.split('.')[-1]
                    fileName = tempFileName[0] + '_' + currentTimestamp + '.' + extension
                else:
                    fileName = tempFileName[0] + '_' + currentTimestamp

                linuxPath = linuxPath + '/' + fileName
            else:
                linuxPath = linuxPath + '/' + fileName

            with open(linuxPath, 'wb') as downloadedFileContents:
                downloadedFileContents.write(contents)

            url = "{0}/ixnetwork/files".format(self.session_url)
            response = self.session.get(
                url, headers=self.json_header, verify=False)
            self.logger.info('A copy of saved file is in: %s' % (winPathFile))
            self.logger.info(
                'copyfile_windows2linux: The copyfile is in %s' % linuxPath)
        else:
            raise Exception(
                "copyfile_windows2linux: Failed to download file from IxNetwork API Server.")

    def tear_down(self):
        """do needed clean up"""
        self.destroy_assign_ports(self.tg_vports)
        self.session.close()

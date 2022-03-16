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
import json
import os

from framework.utils import convert_int2ip, convert_ip2int


class IxnetConfigStream(object):
    def __init__(
        self,
        packetLayers,
        field_config=None,
        frame_size=64,
        trafficItem=1,
        configElement=1,
    ):
        self.traffic_item_id = f"trafficItem[{trafficItem}]"
        self.config_element_id = f"configElement[{configElement}]"

        self.packetLayers = packetLayers
        self.layer_names = [name for name in packetLayers]
        self.field_config = field_config or {}
        self.frame_size = frame_size

    def action_key(self, action):
        if not action:
            msg = "action not set !!!"
            print(msg)

        ret = {
            "inc": "increment",
            "dec": "decrement",
        }.get(action or "inc")

        if ret:
            msg = f"action <{action}> not supported, using increment action now"
            print(msg)

        return ret or "increment"

    @property
    def ethernet(self):
        layer_name = "Ethernet"
        default_config = self.packetLayers.get(layer_name)

        index = self.layer_names.index(layer_name) + 1
        tag = f"{layer_name.lower()}-{index}"

        src_mac = default_config.get("src")
        dst_mac = default_config.get("dst")
        # mac src config
        src_config = {"singleValue": src_mac}
        src_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'ethernet.header.sourceAddress-2']"
        # mac dst config
        dst_config = {"singleValue": dst_mac}
        dst_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'ethernet.header.destinationAddress-1']"
        # ixNetwork stream configuration table
        element = {
            "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']",
            "field": [
                src_config,
                dst_config,
            ],
        }
        return element

    @property
    def ip(self):
        layer_name = "IP"
        default_config = self.packetLayers.get(layer_name)
        vm_config = self.field_config.get(layer_name.lower()) or {}

        index = self.layer_names.index(layer_name) + 1
        tag = f"ipv4-{index}"

        src_ip = default_config.get("src")
        dst_ip = default_config.get("dst")

        # ip src config
        ip_src_vm = vm_config.get("src", {})
        start_ip = ip_src_vm.get("start") or src_ip
        end_ip = ip_src_vm.get("end") or "255.255.255.255"
        src_config = (
            {
                "startValue": start_ip,
                "stepValue": convert_int2ip(ip_src_vm.get("step")) or "0.0.0.1",
                "countValue": str(
                    abs(convert_ip2int(end_ip) - convert_ip2int(start_ip)) + 1
                ),
                "valueType": self.action_key(ip_src_vm.get("action")),
            }
            if ip_src_vm
            else {"singleValue": src_ip}
        )
        src_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'ipv4.header.srcIp-27']"
        # ip dst config
        ip_dst_vm = vm_config.get("dst", {})
        start_ip = ip_dst_vm.get("start") or dst_ip
        end_ip = ip_dst_vm.get("end") or "255.255.255.255"
        dst_config = (
            {
                "startValue": start_ip,
                "stepValue": convert_int2ip(ip_dst_vm.get("step")) or "0.0.0.1",
                "countValue": str(
                    abs(convert_ip2int(end_ip) - convert_ip2int(start_ip)) + 1
                ),
                "valueType": self.action_key(ip_dst_vm.get("action")),
            }
            if ip_dst_vm
            else {"singleValue": dst_ip}
        )
        dst_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'ipv4.header.dstIp-28']"
        # ixNetwork stream configuration table
        element = {
            "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']",
            "field": [
                src_config,
                dst_config,
            ],
        }
        return element

    @property
    def ipv6(self):
        layer_name = "IPv6"
        default_config = self.packetLayers.get(layer_name)
        vm_config = self.field_config.get(layer_name.lower()) or {}

        index = self.layer_names.index(layer_name) + 1
        tag = f"{layer_name.lower()}-{index}"

        src_ip = default_config.get("src")
        dst_ip = default_config.get("dst")
        # ip src config
        ip_src_vm = vm_config.get("src", {})
        start_ip = ip_src_vm.get("start") or src_ip
        end_ip = ip_src_vm.get("end") or "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
        src_config = (
            {
                "startValue": start_ip,
                "stepValue": convert_int2ip(ip_src_vm.get("step"), ip_type=6)
                or "0:0:0:0:0:0:0:1",
                "countValue": str(
                    min(
                        abs(
                            convert_ip2int(end_ip, ip_type=6)
                            - convert_ip2int(start_ip, ip_type=6)
                        )
                        + 1,
                        2147483647,
                    )
                ),
                "valueType": self.action_key(ip_src_vm.get("action")),
            }
            if ip_src_vm
            else {"singleValue": src_ip}
        )
        header_src = "srcIP-7"
        src_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'ipv6.header.{header_src}']"
        # ip dst config
        ip_dst_vm = vm_config.get("dst", {})
        start_ip = ip_dst_vm.get("start") or dst_ip
        end_ip = ip_dst_vm.get("end") or "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
        dst_config = (
            {
                "startValue": start_ip,
                "stepValue": convert_int2ip(ip_dst_vm.get("step"), ip_type=6)
                or "0:0:0:0:0:0:0:1",
                "countValue": str(
                    min(
                        abs(
                            convert_ip2int(end_ip, ip_type=6)
                            - convert_ip2int(start_ip, ip_type=6)
                        )
                        + 1,
                        2147483647,
                    )
                ),
                "valueType": self.action_key(ip_dst_vm.get("action")),
            }
            if ip_dst_vm
            else {"singleValue": dst_ip}
        )
        header_dst = "dstIP-8"
        dst_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'ipv6.header.{header_dst}']"
        # ixNetwork stream configuration table
        element = {
            "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']",
            "field": [
                src_config,
                dst_config,
            ],
        }
        return element

    @property
    def udp(self):
        layer_name = "UDP"
        default_config = self.packetLayers.get(layer_name)

        index = self.layer_names.index(layer_name) + 1
        tag = f"{layer_name.lower()}-{index}"

        sport = default_config.get("sport")
        dport = default_config.get("dport")
        # udp src config
        src_config = {"singleValue": str(sport)}
        header_src = "srcPort-1"
        src_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'udp.header.{header_src}']"
        # udp dst config
        dst_config = {"singleValue": str(dport)}
        header_dst = "dstPort-2"
        dst_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'udp.header.{header_dst}']"
        # ixNetwork stream configuration table
        element = {
            "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']",
            "field": [
                src_config,
                dst_config,
            ],
        }

        return element

    @property
    def tcp(self):
        layer_name = "TCP"
        default_config = self.packetLayers.get(layer_name)

        index = self.layer_names.index(layer_name) + 1
        tag = f"{layer_name.lower()}-{index}"

        sport = default_config.get("sport")
        dport = default_config.get("dport")
        # tcp src config
        src_config = {"singleValue": str(sport)}
        header_src = "srcPort-1"
        src_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'tcp.header.{header_src}']"
        # tcp dst config
        dst_config = {"singleValue": str(dport)}
        header_dst = "dstPort-2"
        dst_config[
            "xpath"
        ] = f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']/field[@alias = 'tcp.header.{header_dst}']"
        # ixNetwork stream configuration table
        element = {
            "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}/stack[@alias = '{tag}']",
            "field": [
                src_config,
                dst_config,
            ],
        }

        return element

    @property
    def framePayload(self):
        element = {
            "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}/framePayload",
            "type": "incrementByte",
            "customRepeat": "true",
            "customPattern": "",
        }
        return element

    @property
    def stack(self):
        element = [
            getattr(self, name.lower())
            for name in self.packetLayers
            if name.lower() != "raw"
        ]
        return element

    @property
    def frameSize(self):
        element = {
            "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}/frameSize",
            "fixedSize": self.frame_size,
        }
        return element

    @property
    def configElement(self):
        element = [
            {
                "xpath": f"/traffic/{self.traffic_item_id}/{self.config_element_id}",
                "stack": self.stack,
                "frameSize": self.frameSize,
                "framePayload": self.framePayload,
            }
        ]
        return element

    @property
    def trafficItem(self):
        element = [
            {
                "xpath": f"/traffic/{self.traffic_item_id}",
                "configElement": self.configElement,
            }
        ]
        return element

    @property
    def traffic(self):
        element = {
            "xpath": "/traffic",
            "trafficItem": self.trafficItem,
        }
        return element

    @property
    def ixnet_packet(self):
        element = {
            "xpath": "/",
            "traffic": self.traffic,
        }
        return element

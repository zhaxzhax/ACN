# This code is part of the Advanced Computer Networks (2020) course at Vrije 
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

import topo

import queue

class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)

        # Using dict instead of array.
        self.adj_list = {}
        self.arp_history = {}  # ARP history

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Get switches and links in the network.
        switches = get_switch(self, None)
        links = get_link(self, None)

        # Assume that dpid of switches is 1 based.
        for link in links:
            src = link.src.dpid
            dst = link.dst.dpid
            self.adj_list.setdefault(src, {})
            self.adj_list[src][dst] = link.src.port_no
        print(self.adj_list)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)


    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)
    
    def neighbors(self, s):
        res = []
        for key in self.adj_list[s]:
            res.append(key)
        return res
        
    def solve(self, s):
        q = queue.Queue()
        q.put(s)
        
        visited = {}
        visited[s] = 1

        prev = {}
        while q.empty() == 0:
            node = q.get()
            nbs = self.neighbors(node)
            
            for nb in nbs:
                if nb not in visited:
                    q.put(nb)
                    visited[nb] = 1
                    prev[nb] = node
        return prev
  
    def reconstructPath(self, s, d, prev):
        path = []
        at = d
        while True:
            path.append(at)
            if at in prev:
                at = prev[at]
            else:
                break
        path.reverse()
        return path
        
    # Return a list representing the shortest path between src and dst
    def bfs(self, s, d):
        prev = self.solve(s)
        return self.reconstructPath(s, d, prev)
    
    def trans_out_port(self, datapath, src, dst, in_port):
        dpid = datapath.id
        if src not in self.adj_list:
            self.adj_list.setdefault(src, {})
            self.adj_list[src][dpid] = -1
            self.adj_list.setdefault(dpid, {})
            self.adj_list[dpid][src] = in_port
        if dst in self.adj_list:
            path = self.bfs(src, dst)
            next_hop = path[path.index(dpid) + 1]
            out_port = self.adj_list[dpid][next_hop]
            print("PATH:")
            print(path)
        else:
            out_port = datapath.ofproto.OFPP_FLOOD
        return out_port

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        dpid = datapath.id
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        if eth.ethertype == ether_types.ETH_TYPE_IPV6:
            return
 
        dst = eth.dst
        src = eth.src
        
        out_port = datapath.ofproto.OFPP_FLOOD
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)
            if arp_pkt.opcode == arp.ARP_REQUEST:
                if (datapath.id, arp_pkt.src_mac, arp_pkt.dst_ip) in self.arp_history and self.arp_history[(datapath.id, arp_pkt.src_mac, arp_pkt.dst_ip)] != in_port:
                    #self.logger.info("drop arp- dpid:%s src:%s dst:%s in_port:%s", dpid, arp_pkt.src_mac, arp_pkt.dst_ip, in_port)
                    return
                else:
                    #self.logger.info("add arp history- dpid:%s src:%s dst:%s in_port:%s", dpid, arp_pkt.src_mac, arp_pkt.dst_ip, in_port)      
                    self.arp_history[(datapath.id, arp_pkt.src_mac, arp_pkt.dst_ip)] = in_port
                    print(self.arp_history)
            
        out_port = self.trans_out_port(datapath, src, dst, in_port)
        
        actions = [ofp_parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD and out_port != -1:
            match = ofp_parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath=datapath, priority=1, match=match, actions=actions)

        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
            data = msg.data

        out = ofp_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
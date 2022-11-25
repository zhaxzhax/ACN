# This code is part of the Advanced Computer Networks (ACN) course at VU 
# Amsterdam.

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

# A dirty workaround to import topo.py from lab2

import os
import subprocess
import time

import mininet
import mininet.clean
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.link import TCLink
from mininet.node import Node, OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import waitListening, custom

import topo

class FattreeNet(Topo):
	"""
	Create a fat-tree network in Mininet
	"""

	def __init__(self, ft_topo):
		
		Topo.__init__(self)

		# TODO: please complete the network generation logic here
		for iswitch in range(len(ft_topo.switches)):
			switch = ft_topo.switches[iswitch]
			#self.addSwitch(switch.id)
			self.addSwitch(switch.id, ip=switch.ip, dpid=switch.dpid)

		# add host
		for iserver in range(len(ft_topo.servers)):
			host = ft_topo.servers[iserver]
			self.addHost(host.id, ip=host.ip)

		# add link of hosts
		for ihost in range(len(ft_topo.servers)):
			host = ft_topo.servers[ihost]
			for iedge in range(len(host.edges)):
				ln = self.addHost(host.edges[iedge].lnode.id)
				
				# 右结点是agg switch
				rn = self.addSwitch(host.edges[iedge].rnode.id)				
				#rn = self.addSwitch(host.edges[iedge].rnode.id, dpid = host.edges[iedge].rnode.dpid)
				
				self.addLink(ln, rn, bw = 15, delay = '5')
		
		# add link of agg
		for iaggswitch in range(ft_topo.num_agg):
			aggswitch = ft_topo.switches[ft_topo.num_agg + iaggswitch]
			for iedge in range(len(aggswitch.edges)):
				
				ln = self.addSwitch(aggswitch.edges[iedge].lnode.id)
				#ln = self.addSwitch(aggswitch.edges[iedge].lnode.id, dpid = aggswitch.edges[iedge].lnode.dpid)
				
				# 右边是edge和core
				rn = self.addSwitch(aggswitch.edges[iedge].rnode.id)
				#rn = self.addSwitch(aggswitch.edges[iedge].rnode.id, dpid = aggswitch.edges[iedge].rnode.dpid)
				
				self.addLink(ln, rn, bw = 15, delay = '5')


def make_mininet_instance(graph_topo):

	net_topo = FattreeNet(graph_topo)
	net = Mininet(topo=net_topo, controller=None, autoSetMacs=True)
	net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6653)
	return net

def run(graph_topo):
	
	# Run the Mininet CLI with a given topology
	lg.setLogLevel('info')
	mininet.clean.cleanup()
	net = make_mininet_instance(graph_topo)

	info('*** Starting network ***\n')
	net.start()
	info('*** Running CLI ***\n')
	CLI(net)
	info('*** Stopping network ***\n')
	net.stop()



ft_topo = topo.Fattree(4)
run(ft_topo)

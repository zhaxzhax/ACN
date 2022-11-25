# This code is part of the Advanced Computer Networks course at Vrije 
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

import sys
import random
import queue
# import networkx as nx
# import matplotlib.pyplot as plt

# 当生成switch的Node的时候，计算dpid
def location_to_dpid(core=None, pod=None, switch=None):
	if core is not None:
		return '0000000010%02x0000'%core
	else:
		return'000000002000%02x%02x'%(pod, switch)

# Class for an edge in the graph
class Edge:
	def __init__(self):
		self.lnode = None
		self.rnode = None
	
	def remove(self):
		self.lnode.edges.remove(self)
		self.rnode.edges.remove(self)
		self.lnode = None
		self.rnode = None

# Class for a node in the graph
class Node:
	def __init__(self, id, type, ip_address, dpid = None):
		self.edges = []
		self.id = id
		self.type = type
		self.ip = ip_address
		self.dpid = dpid

	# Add an edge connected to another node
	def add_edge(self, node):
		edge = Edge()
		edge.lnode = self
		edge.rnode = node
		self.edges.append(edge)
		node.edges.append(edge)
		return edge

	# Remove an edge from the node
	def remove_edge(self, edge):
		edge.lnode.edges.remove(edge)
		edge.rnode.edges.remove(edge)

	# Decide if another node is a neighbor
	def is_neighbor(self, node):
		for edge in self.edges:
			if edge.lnode == node or edge.rnode == node:
				return True
		return False
		
class Fattree:

	def __init__(self, num_ports):
		self.servers = []
		self.switches = []
		# self.am_servers = [[9 for i in range(num_switches + num_servers)] for j in range(num_switches + num_servers)]
		self.generate(num_ports)
		num_switches = len(self.switches)
		num_servers = len(self.servers)
		self.am_servers = [[9 for i in range(num_switches + num_servers)] for j in range(num_switches + num_servers)]

	def generate(self, num_ports):

		# TODO: code for generating the fat-tree topology
		CoreSwitchList = []
		AggSwitchList = []
		EdgeSwitchList = []

		self.num_ports = num_ports
		self.num_CoreSwitch = (num_ports/2) ** 2
		self.num_AggSwitch = num_ports * num_ports/2
		self.num_EdgeSwitch = num_ports * num_ports/2
		self.num_Server = num_ports*num_ports * num_ports/4
		self.PREFIX = "s"
		self.num_pods = num_ports


		# pod
		for ipod in range(0, num_ports):

			# edgelist
			#ip: 10.pod.switch.1
			for iswitch in range(0, int(num_ports/2)):
				#eswitch_t = Node("10."+ str(ipod) + "." + str(iswitch) + "." + str(1), "EdgeSwitch")
				dpid = location_to_dpid(pod=ipod, switch=iswitch)
				eswitch_t = Node('p%de%d'%(ipod, iswitch), "EdgeSwitch", "10."+ str(ipod) + "." + str(iswitch) + "." + str(1), dpid)

				# hostlist
				#ip: 10.pod.switch.2 ~ k/2+2
				for ihost in range(2, 2 + int(num_ports/2)):
					#host_t = Node("10."+ str(ipod) + "." + str(iswitch) + "." + str(ihost), "Host")
					host_t = Node( 'p%de%dh%d'%(ipod, iswitch, ihost), "Host", "10."+ str(ipod) + "." + str(iswitch) + "." + str(ihost))
					host_t.add_edge(eswitch_t)
					self.servers.append( host_t )
				
				EdgeSwitchList.append(eswitch_t)

			# agglist
			#ip: 10.pod.switch.1
			for iswitch in range(int( num_ports/2 ), num_ports):
				#aswitch_t = Node("10."+ str(ipod) + "." + str(iswitch) + "." + str(1), "AggSwitch")
				dpid = location_to_dpid(pod=ipod, switch=iswitch)
				aswitch_t = Node('p%da%d'%(ipod, iswitch), "AggSwitch", "10."+ str(ipod) + "." + str(iswitch) + "." + str(1), dpid)
				AggSwitchList.append(aswitch_t)
				pod_start = int(ipod * num_ports/2)
				pod_end = int((ipod+1) * num_ports/2)

				for iswitch in range(pod_start, pod_end):
					aswitch_t.add_edge(EdgeSwitchList[iswitch])

		self.num_agg = len(AggSwitchList)
		
		self.switches += EdgeSwitchList
		self.switches += AggSwitchList

		
		# corelist
		# ip: 10. (k/2)^2. 1~(k/2). 1~(k/2)
		for x in range(1, int(num_ports/2)+1):
			for y in range(1, int(num_ports/2)+1):
				#cswitch_t = Node("10."+str(num_ports)+"." + str(x) + "." + str(y), "CoreSwitch")
				dpid = location_to_dpid(core= int((x-1) * (num_ports/2) + y) )
				cswitch_t = Node( 'c%d%d'%(x, y), "CoreSwitch", "10."+str(num_ports)+"." + str(x) + "." + str(y), dpid)

				for ipod in range(0, num_ports):
					agg_index = int(num_ports/2) * ipod +  x - 1
					cswitch_t.add_edge(AggSwitchList[agg_index])
				CoreSwitchList.append(cswitch_t)

		self.switches += CoreSwitchList

	def draw(self):
		G = nx.Graph()
		sizes = []

		for switch in self.switches:
			G.add_node(switch.id)
			sizes.append(20)
			for edge in switch.edges:
					G.add_edge(edge.lnode.id, edge.rnode.id)

		for server in self.servers:
			G.add_node(server.id)
			sizes.append(5)
			for edge in server.edges:
				G.add_edge(edge.lnode.id, edge.rnode.id)
		pos = nx.kamada_kawai_layout(G)
		nx.draw(G,pos,node_size=sizes, with_labels=True)
		plt.savefig("figure/fattree.png")
	
	def genAdMatrix(self):
		nodes = self.servers + self.switches
		row = 0
		for node1 in nodes:
			col = 0
			for node2 in nodes:
				if node1.is_neighbor(node2):
					if row != col:
						self.am_servers[row][col] = 1
					else:
						self.am_servers[row][col] = 0
				col = col + 1
			row = row + 1
	
	def showAdMatrix(self):
		for i in range(len(self.am_servers)):
			for j in range(len(self.am_servers[0])):
				sys.stdout.write("%d " % (self.am_servers[i][j]))
			sys.stdout.write("\n")


class Jellyfish:

	def __init__(self, num_servers, num_switches, num_ports):
		self.servers = []
		self.switches = []
		# corresponding unweighted adjacency matrix
		self.am_servers = [[9 for i in range(num_switches + num_servers)] for j in range(num_switches + num_servers)]
		self.generate(num_servers, num_switches, num_ports)

	def generate(self, num_servers, num_switches, num_ports):
		sys.stdout.write("Generating Jellyfish topology: %d servers, %d switches, %d ports per switch" % (num_servers, num_switches, num_ports))
		avail_ports = []
		avail_switch_set = set()
		avail_switch_set2 = set()
		
		# initalize node and add to the list
		for switch in range(num_switches):
			node = Node(switch,"switch")
			self.switches.append(node)
			avail_ports.append(num_ports)
			avail_switch_set.add(switch)
			avail_switch_set2.add(switch)
			
		#connect switch to server
		for server in range(num_servers):
			node = Node(server,"server")
			self.servers.append(node)
			self.servers[server].add_edge(self.switches[server%num_switches])
			avail_ports[server%num_switches]-=1
		
		switch_with_1_more_port = num_switches
		switch_with_2_more_port = num_switches
		
		useless_outside_loop_times = 0
		# if 100 times we always random initiate switch 1,2 and switch 1,2 is a neighbor, we tend to assume there is no node can be linked. BTW, it's not a good implementation. I think maybe we should make a hashmap{key:switch1,value:a list[the possible switch that switch1 can linked(avail_port>0 && not neighbor)]}
		while switch_with_1_more_port>1 and useless_outside_loop_times<10:
			random_switch1 = random.randrange(len(avail_switch_set))
			random_switch2 = random_switch1
			# prevent all the available switch2 is the neighbor of switch1
			useless_inner_loop_times = 0
			
			switch1=-1
			switch2=-1
			while(random_switch2==random_switch1):
				random_switch2 = random.randrange(len(avail_switch_set))
				switch1 = list(avail_switch_set)[random_switch1]
				switch2 = list(avail_switch_set)[random_switch2]
				if useless_inner_loop_times > 10:
					break
				if self.switches[switch1].is_neighbor(self.switches[switch2]):
					useless_inner_loop_times += 1
					continue
			if useless_inner_loop_times>10:
				useless_outside_loop_times += 1
				continue
			# it means still has node can be linked with edge
			useless_outside_loop_times = 0

			if avail_ports[switch1]<1:
				sys.stdout.write("error in 4")
			if avail_ports[switch2]<1:
				sys.stdout.write("error in 5")
			
			self.switches[switch1].add_edge(self.switches[switch2])
			avail_ports[switch1] -= 1
			avail_ports[switch2] -= 1

			if avail_ports[switch1] == 0:
				switch_with_1_more_port -= 1
				avail_switch_set.discard(switch1)
						
			if avail_ports[switch2] == 0:
				switch_with_1_more_port -= 1
				avail_switch_set.discard(switch2)
							
			if avail_ports[switch1] == 1:
				switch_with_2_more_port -=1
				avail_switch_set2.discard(switch1)
							
			if avail_ports[switch2] == 1:
				switch_with_2_more_port -=1
				avail_switch_set2.discard(switch2)


			if switch_with_1_more_port != len(avail_switch_set):
				sys.stdout.write("error in 1")
			
			if switch_with_2_more_port != len(avail_switch_set2):
				sys.stdout.write("error in 2")

		while switch_with_2_more_port !=0:
			set2_index = random.randrange(switch_with_2_more_port)
			i = list(avail_switch_set2)[set2_index]

			if avail_ports[i]<2:
				sys.stdout.write("error in 3")

			random_node1 = random.randrange(num_switches)
			while random_node1 == i:
				random_node1 = random.randrange(num_switches)
				# node1 should not be the neighbor
				if(self.switches[random_node1].is_neighbor(self.switches[i])):
					random_node1 == i
					continue
				# pick a random edge and spit it
				if len(self.switches[random_node1].edges)==0:
					random_node1 == i
					continue
				random_edge_index = random.randrange(len(self.switches[random_node1].edges))
				random_edge = self.switches[random_node1].edges[random_edge_index]
				if random_node1 == random_edge.lnode.id :
					random_node2 = random_edge.rnode.id
				# if lnode is node1, then node2 = rnode; if lnode is not node1, then node2 = lnode
				else:
					random_node2 = random_edge.lnode.id
				# node should not be server and neighbor
				if random_edge.lnode.type=="server" or random_edge.rnode.type=="server" or self.switches[random_node2].is_neighbor(self.switches[i]):
					random_node1 == i
					continue
				self.switches[random_node1].remove_edge(random_edge)
				self.switches[i].add_edge(self.switches[random_node1])
				self.switches[i].add_edge(self.switches[random_node2])
				avail_ports[i] -= 2
				if avail_ports[i] <= 0:
					switch_with_1_more_port -= 1
					avail_switch_set.discard(i)
					
				if avail_ports[i] <= 1:
					switch_with_2_more_port -= 1
					avail_switch_set2.discard(i)
		sys.stdout.write(" done\n")

# 	def draw(self):
# 		G = nx.Graph()
# 		sizes = []

# 		for switch in self.switches:
# 			G.add_node(switch.id)
# 			sizes.append(20)
# 			for edge in switch.edges:
# 					G.add_edge(edge.lnode.id, edge.rnode.id)

# 		for server in self.servers:
# 			G.add_node(server.id+10000)
# 			sizes.append(5)
# 			for edge in server.edges:
# 				G.add_edge(edge.lnode.id+10000, edge.rnode.id)
# 		pos = nx.kamada_kawai_layout(G)
# 		nx.draw(G,pos, with_labels=True)
# 		plt.savefig("figure/jellyfish.png")
	
# 	def genAdMatrix(self):
# 		nodes = self.servers + self.switches
# 		row = 0
# 		for node1 in nodes:
# 			col = 0
# 			for node2 in nodes:
# 				if node1.is_neighbor(node2):
# 					if row != col:
# 						self.am_servers[row][col] = 1
# 					else:
# 						self.am_servers[row][col] = 0
# 				col = col + 1
# 			row = row + 1
	
# 	def showAdMatrix(self):
# 		for i in range(len(self.am_servers)):
# 			for j in range(len(self.am_servers[0])):
# 				sys.stdout.write("%d " % (self.am_servers[i][j]))
# 			sys.stdout.write("\n")

# MAX = float('inf')
	
# def dijkstra(matrix, start_node):
#     matrix_length = len(matrix)
#     used_node = [False] * matrix_length
#     distance = [MAX] * matrix_length
    
#     distance[start_node] = 0
    
#     while used_node.count(False):
#         min_value = float('inf')
#         min_value_index = 999
        
#         for index in range(matrix_length):
#             if not used_node[index] and distance[index] < min_value:
#                 min_value = distance[index]
#                 min_value_index = index
        
#         used_node[min_value_index] = True

#         for index in range(matrix_length):
#             distance[index] = min(distance[index], distance[min_value_index] + matrix[min_value_index][index])

#     return distance
    


# print("\n---fattree---\n")    
# fattree = Fattree(14)
# fattree.draw()
# plt.clf()
# # print("ft server: %d" % (len(fattree.servers)))
# fattree.genAdMatrix()

# result0 = []
# nodeNum = len(fattree.servers)
# for i in range(nodeNum):
# 	# print("i: %d\n" % (i))
# 	start = i + 1
# 	result0 = result0 + dijkstra(fattree.am_servers, i)[start:nodeNum+1]
# 	for i in range(10):
# 		print("%d: %d\n" % (i, result0.count(i)))

# for i in range(10):
# 	print("%d: %d\n" % (i, result0.count(i)))

# print("\n---jellyfish---\n")
# jellyfish = Jellyfish(686, 245, 14)
# jellyfish.draw()
# plt.clf()
# jellyfish.genAdMatrix()

# result = []
# nodeNum = len(jellyfish.servers)
# for i in range(nodeNum):
# 	# print("i: %d\n" % (i))
# 	start = i + 1
# 	result = result + dijkstra(jellyfish.am_servers, i)[start:nodeNum+1]

# for i in range(10):
# 	print("%d: %d\n" % (i, result.count(i)))
	

# x_data = ['2','3','4','5','6']
# y_data = []
# y2_data = []
# total_num = 0
# for i in range(10):
# 	total_num += result.count(i)
# for i in range(2,7):
# 	y_data.append(result0.count(i)/total_num)
# for i in range(2,7):
# 	y2_data.append(result.count(i)/total_num)
# print(y_data)
# print(y2_data)

# # y_data = [2058/235634, 42/235634, 14406/235634, 637/235634, 218491/235634]
# # y2_data = [2065/235634, 16553/235634, 78201/235634, 129197/235634, 9618/235634]

# x_width = range(0, len(x_data))
# x2_width = [i+0.3 for i in x_width]

# plt.bar(x_width, y_data, lw=0.5, fc="r", width=0.3, label="fattree")
# plt.bar(x2_width, y2_data, lw=0.5, fc="b", width=0.3, label="jellyfish")

# plt.xticks(range(0,5), x_data)
# plt.legend()
# #plt.show()
# plt.savefig("figure/1c.png")
# plt.clf()
	




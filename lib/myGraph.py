# coding: utf-8

import tree.tree as mod_tree

import uuid
import utilities
import logbasic
import datetime

class SubGraph(object):
	def __init__(self, ip):
		self.user = ip
		self.ua_trees_d = {}	# Tree dict. {ua: [webtrees]}

	def all_trees(self):
		cnt = 0
		for item in self.ua_trees_d.values():
			cnt += len(item)
		return cnt

class NewTreeNeeded(Exception):
	pass
	
class Graph(object):
	def __init__(self):
		self.subgraphs = []
		self.junk_nodes = []

	def get_subgraph(self, ip):
		for sg in self.subgraphs:
			if sg.user == ip:
				return sg
		return None

	def all_trees(self):
		all_trees = []
		for sg in self.subgraphs:
			for key in sg.ua_trees_d.keys():
				trees = sg.ua_trees_d[key]
			all_trees += trees
		return all_trees

	def add_node(self, new_node):
		""" Create the referrer trees depending on 
			nodes' referrer relationships.
		"""
		# Search for corresponding subgraph
		if new_node.user_ip is None:
			print 'Source IP is lost in request/response pair.'
			exit(-1)

		subgraph = self.get_subgraph(new_node.user_ip)
		if subgraph == None:
			subgraph = SubGraph(new_node.user_ip)
			self.subgraphs.append(subgraph)


		try:
			# Start linking
			if new_node.user_agent is not None:
				if new_node.user_agent in subgraph.ua_trees_d.keys():	
					linked_flag = False
					for tree in subgraph.ua_trees_d[new_node.user_agent][::-1]:
						# Session idle time of 15 minutes used
						if new_node.start_time - tree.nodes[-1].start_time <= datetime.timedelta(minutes = 15):
							# Find its predecessor
							pred_id = None
							if new_node.referrer:
								for item in tree.nodes[::-1]:
									#if utilities.cmp_url(new_node.referrer, item.url, 'loose'):
									if utilities.cmp_url(new_node.referrer, item.url, 'strict'):
										pred_id = item.identifier
										break
							if pred_id != None:
								# Predecessor found...
								tree.add_node(new_node, pred_id)
								linked_flag = True
								break
					# After all the trees are checked:	
					if not linked_flag:
						raise NewTreeNeeded
				else:
					# new user agent index and new tree
					raise NewTreeNeeded

		except NewTreeNeeded:
			if new_node.is_root():
				if int(new_node.status) == 200:
					new_tree = mod_tree.Tree()
					new_tree.add_node(new_node, parent=None)
					# Update the graph
					try:
						subgraph.ua_trees_d[new_node.user_agent].append(new_tree)
					except:
						subgraph.ua_trees_d[new_node.user_agent] = [new_tree]
			else:
				self.junk_nodes.append(new_node)
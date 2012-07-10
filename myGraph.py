# coding: utf-8

from myWeb import WebObject
import tree.node as mod_node
import tree.tree as mod_tree

import uuid
import utilities
import logbasic
import datetime


class Node(mod_node.Node, WebObject):
	"""docstring for WebNode"""
	def __init__(self):
		nid = str(uuid.uuid1())
		mod_node.Node.__init__(self, 'nd_'+nid, nid)
		WebObject.__init__(self)


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


def get_value(dict, key):
	try:
		value = dict[key]
		if value == 'N/A':
			raise KeyError
	except KeyError:
		value = None
	return value
	
def create_node_from_rr(rr):
	new_node = Node()
	new_node.user_ip = get_value(rr, 'source_ip')
	sdt = get_value(rr, 'time')
	if sdt is not None:
		new_node.start_time = logbasic.parse_time(sdt)
	dns = get_value(rr, 'dns')
	connect = get_value(rr, 'connect')
	send = get_value(rr, 'send')
	wait = get_value(rr, 'wait')
	receive = get_value(rr, 'receive')
	timings = [dns, connect, send, wait, receive]
	timings = [int(i) for i in timings if i != None]
	new_node.total_time = datetime.timedelta(milliseconds = sum(timings))
	rt = get_value(rr, 'receive')
	new_node.receiving_time = rt!=None and int(rt) or 0
	new_node.url = get_value(rr, 'url')
	new_node.status = int(get_value(rr, 'response_status'))
	rbz = get_value(rr, 'response_body_size')
	new_node.size = rbz != None and int(rbz) or 0
	new_node.type = get_value(rr, 'response_content_type')
	new_node.re_url = get_value(rr, 'redirect_url')
	new_node.user_agent = get_value(rr, 'user_agent_id')
	new_node.referrer = get_value(rr, 'referrer')

	return new_node
	
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
						if new_node.start_time - tree[tree.root].start_time \
											<= datetime.timedelta(minutes = 30):
							# Find its predecessor in the past xx mins...
							pred_id = None
							tree.nodes.sort(lambda x,y: cmp(x.start_time, y.start_time), None, False)

							if new_node.referrer:
								for item in tree.nodes[::-1]:
									if utilities.cmp_url(new_node.referrer, item.url, 'loose'):
										# refer to 'utilities.py' for details about 'loose' parameter
										pred_id = item.identifier
										break
							if pred_id:
								# Predecessor found...
								tree.add_node(new_node, pred_id)
								linked_flag = True
								break
						else:
							break

					# After all the trees are checked:	
					if not linked_flag:
						raise NewTreeNeeded
				else:
					# new user agent index and new tree
					raise NewTreeNeeded

		except NewTreeNeeded:
			if new_node.is_root():
				if new_node.status == 200:
					new_tree = mod_tree.Tree()
					new_tree.add_node(new_node, None)
					linked_flag = True
					# Update the graph
					try:
						subgraph.ua_trees_d[new_node.user_agent].append(new_tree)
					except:
						subgraph.ua_trees_d[new_node.user_agent] = [new_tree]
			else:
				self.junk_nodes.append(new_node)

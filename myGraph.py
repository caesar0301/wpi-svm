# coding: utf-8
from myTree import Tree, Node
import utilities
import logbasic
import datetime

def get_value(dict, key):
	try:
		value = dict[key]
		if value == 'N/A':
			raise KeyError
	except KeyError:
		value = None
	return value

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

	def get_subgraph(self, ip):
		for sg in self.subgraphs:
			if sg.user == ip:
				return sg
		return None

	def add_node(self, node):
		# Search for corresponding subgraph
		if node.user_ip is None:
			print 'Source IP is lost in request/response pair.'
			exit(-1)
		subgraph = self.get_subgraph(node.user_ip)
		if subgraph == None:
			subgraph = SubGraph(node.user_ip)
			self.subgraphs.append(subgraph)
		try:
			# Start linking
			linked_flag = False
			if node.user_agent and node.user_agent in subgraph.ua_trees_d.keys():
				for tree in subgraph.ua_trees_d[node.user_agent][::-1]:
					if node.start_time - tree[tree.root].start_time <= datetime.timedelta(minutes = 30):
						# Find its predecessor in the past 30 mins...
						predecessor = None
						# try with referrer...
						if node.referrer:
							if utilities.search_url(node.referrer, tree.ref_node_d.keys()):
								predecessor = tree.ref_node_d[node.referrer]
							elif utilities.search_url(node.referrer, tree.url_node_d.keys()):
								# Referrer, last chance...
								predecessor = tree.url_node_d[node.referrer]
								tree.ref_node_d[node.referrer] = predecessor
								# Add this node to the tree or continue to search.	
						if predecessor:
							# Predecessor found...
							tree.add_node(node, predecessor)
							tree.url_node_d[node.url] = node.identifier
							linked_flag = True
							break
					else:	break
				# After all the trees are checked:	
				if not linked_flag:
					raise NewTreeNeeded	
			elif node.user_agent is not None:
					# new user agent index and new tree
					raise NewTreeNeeded
		except NewTreeNeeded:
			if node.is_root():
				new_tree = Tree()
				new_tree.add_node(node, None)
				new_tree.url_node_d[node.url] = node.identifier
				new_tree.ref_node_d[node.url] = node.identifier
				linked_flag = True
				# Update the graph
				try:
					subgraph.ua_trees_d[node.user_agent].append(new_tree)
				except:
					subgraph.ua_trees_d[node.user_agent] = [new_tree]
					
	def all_trees(self):
		all_trees = []
		for sg in self.subgraphs:
			for key in sg.ua_trees_d.keys():
				trees = sg.ua_trees_d[key]
			all_trees += trees
		return all_trees
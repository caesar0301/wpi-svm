# coding: utf-8
# Author: chenxm, 2012-06-03
import argparse, re, datetime

import logbasic as basic
from myweb import WebPage
from mytree import Node, Tree
import utilities

def get_value(dict, key):
	try:
		value = dict[key]
		if value == 'N/A':
			raise KeyError
	except KeyError:
		value = None
	return value
	
def check_options(s):
	""" This is optional for checking string if signatures exist
	only check string before '?'
	"""
	# cut string
	cut_r = re.compile(r'([^\?&=]+)')
	cut_match = re.match(cut_r, s)
	if cut_match != None:
		str_cut = cut_match.group(1)
	else:
		str_cut = s
	key_word_r = re.compile(r'(.*(ads|analysis|adserver|ad|widget|embed|banner|cdn).*\.?)+')
	key_word_match = re.match(key_word_r, str_cut)
	if key_word_match == None:
		return True
	else:
		return False
	
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
					# Find its predecessor
					predecessor = None
					# try with referrer
					if node.referrer:
						if utilities.search_url(node.referrer, tree.ref_node_d.keys()):
							predecessor = tree.ref_node_d[node.referrer]
						elif utilities.search_url(node.referrer, tree.url_node_d.keys()):
							# Referrer, last chance
							predecessor = tree.url_node_d[node.referrer]
							tree.ref_node_d[node.referrer] = predecessor
					# Add this node to the tree or continue to search	
					if predecessor:
						tree.add_node(node, predecessor)
						tree.url_node_d[node.url] = node.identifier
						linked_flag = True
						break
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
						
def construct_trees(all_nodes):
	new_graph = Graph()
	print 'processing nodes...'
	for node in all_nodes:
		new_graph.add_node(node)
	print 'graph ready...'
	print 'finding pages...'
	all_trees = []
	for sg in new_graph.subgraphs:
		for key in sg.ua_trees_d.keys():
			trees = sg.ua_trees_d[key]
		all_trees += trees
	return all_trees
	
def compare_time(ts1, ts2):
	def parse_time(ts):
		time_re = re.compile(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d{3})')
		match = time_re.match(ts)
		if match:
			year = int(match.group(1))
			month = int(match.group(2))
			day = int(match.group(3))
			hour = int(match.group(4))
			minute = int(match.group(5))
			seconds = int(match.group(6))
			microseconds = int(match.group(7))*1000
			dt = datetime.datetime(year, month, day, hour, minute, seconds, microseconds)
			return dt
		else:
			return None	
	dt1 = parse_time(ts1)
	dt2 = parse_time(ts2)
	return dt1 - dt2
	
def process_tree(tree, K, T):
	t_refs = tree.ref_node_d.values()	# We choose all the referred nodes as main object candidates
	main_obj_cands = []
	for i in t_refs:
		moc = tree[i]
		if moc.is_root and len(moc.fpointer) >= K:
			# HTML object with embedded objects greater than K
			main_obj_cands.append(moc)
	pages = []
	if len(main_obj_cands) > 0:
		main_obj_cands.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)	# ordered by +time
		cand_ids = [i.identifier for i in main_obj_cands]
		# Find final page roots
		real_roots = []
		for cand in main_obj_cands:
			cand_pred_id = cand.bpointer
			new_root = None
			if cand_pred_id is not None:
				cand_pred = tree[cand_pred_id]
				if compare_time(cand.start_time, cand_pred.start_time) >= datetime.timedelta(seconds = T):
					# Meet idle time limit
					if check_options(cand.url):	# host vs url
						# optional keywork checking
						new_root = cand
			elif check_options(cand.url):
					new_root = cand
			if new_root is None:
				# Do not make this node as root
				# but it still exists on the tree
				continue
			else:
				real_roots.append(new_root)
		real_roots_ids = [i.identifier for i in real_roots]
		for rootid in real_roots_ids:
			new_page = WebPage()
			new_page.add_obj(tree[rootid], True)
			pages.append(new_page)
			for nodeid in tree.expand_tree(rootid, filter = lambda x: x not in real_roots_ids):
				new_page.add_obj(tree[nodeid])
	return pages
			
def main():
	parser = argparse.ArgumentParser(description='Page reconstruction from weblog using StreamStructure algorithm proposed by S. Ihm on IMC 2011.')
	parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
	parser.add_argument('-k', type=int, default = 2, help= 'T parameter')
	parser.add_argument('-t', type=int, default = 5, help= 'T parameter')
	parser.add_argument('-o', '--output', type=str, help= 'Output file')
	args = parser.parse_args()
	log_file = args.logfile
	K = args.k
	T = args.t
	output = args.output
	print 'K = %d, T = %.2f' % (K, T)
	print 'reading log...'
	all_rr = basic.read(log_file)
	print 'processing rrp...'
	all_nodes = []
	for rr in all_rr:
		new_node = Node("rr_%d" % all_rr.index(rr))
		new_node.user_ip = get_value(rr, 'source_ip')
		new_node.start_time = get_value(rr, 'time')
		dns = get_value(rr, 'dns')
		connect = get_value(rr, 'connect')
		send = get_value(rr, 'send')
		wait = get_value(rr, 'wait')
		receive = get_value(rr, 'receive')
		timings = [dns, connect, send, wait, receive]
		timings = [int(i) for i in timings if i != None]
		new_node.total_time = sum(timings)
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
		all_nodes.append(new_node)
	all_trees = construct_trees(all_nodes)
	print 'Trees:', len(all_trees)
	all_pages = []
	for tree in all_trees:
		all_pages += process_tree(tree, K, T)
	print 'Pages:', len(all_pages)
	all_urls = [i.root.url for i in all_pages]
	if output is None:
		filename = log_file + '.ssurl'
	else:
		filename = output
	ofile = open(filename, 'wb')
	ofile.write('\n'.join(all_urls))
	ofile.close()		
		
if __name__ == "__main__":
	main()
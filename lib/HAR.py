import json,argparse
import os, uuid, random, datetime
import sys
import codecs

from myWeb import WebObject
from myWeb import WebPage

import tree.node as mod_node
import tree.tree as mod_tree

import utilities as utilities
import logbasic as logbasic

def parse_field(dict, key):
	invalid_values = ['', -1]
	try:
		value = dict[key]
		if value in invalid_values:
			raise KeyError
	except KeyError:
		value = None
	return value

class NewTreeNeeded(Exception):
	pass

class NodeFromHar(mod_node.Node, WebObject):
	def __init__(self, har_ent):
		nid = str(uuid.uuid1())
		mod_node.Node.__init__(self, 'nd_'+nid, nid)
		WebObject.__init__(self)

		self.pageid = har_ent['pageref']
		self.user_ip = '0.0.0.0'	# tmp

		sdt = parse_field(har_ent, 'startedDateTime')
		if sdt is not None:
			self.start_time = logbasic.time_str2dt(sdt)

		timings = parse_field(har_ent, 'timings')
		if timings is not None:
			dns = parse_field(timings, 'dns')
			connect = parse_field(timings, 'connect')
			send = parse_field(timings, 'send')
			wait = parse_field(timings, 'wait')
			receive = parse_field(timings, 'receive')
			timings = [dns, connect, send, wait, receive]
			timings = [int(i) for i in timings if i != None]
			self.total_time = datetime.timedelta(milliseconds = sum(timings))
			if receive is not None:
				self.receiving_time = int(receive)

		request = parse_field(har_ent, 'request')
		if request is not None:
			self.url = parse_field(request, 'url')
			headers = parse_field(request, 'headers')
			if headers is not None:
				for field in headers:
					if field['name'] == 'Referer':
						self.referrer = field['value']
					if field['name'] == 'User-Agent':
						self.user_agent = field['value']

		response = parse_field(har_ent, 'response')
		if response is not None:
			self.status = int(parse_field(response, 'status'))
			bds = parse_field(response, 'bodySize')
			if bds != None:
				self.size = int(bds)
			content = parse_field(response, 'content')
			if content is not None:
				self.type = parse_field(content, 'mimeType')
			headers = parse_field(response, 'headers')
			for field in headers:
				if field['name'] == 'Location':
					self.re_url = field['value']

def parse_pages_har(harfolder):
	print 'Processing har files...'
	# Processing all HAR file under the folder
	all_real_pages = []
	all_objects = []
	for root, dirs, files in os.walk(harfolder):
		for file in files:
			suffix = file.rsplit('.', 1)[1]
			if suffix != 'har':
				continue

			inputfile = os.path.join(root, file)
			# Open HAR file
			har_log = json.load(codecs.open(inputfile, 'rb', 'utf-8'))['log']
			har_pages = har_log['pages']
			har_objects = har_log['entries']

			# Extract web objects and order them in time
			allnodes = []
			for i in har_objects:
				new_node = NodeFromHar(i)		# new node
				allnodes.append(new_node)
			allnodes.sort(lambda x,y: cmp(x, y), lambda x: x.start_time, False)
			
			all_objects += allnodes
			
			# Find valid trees from raw web objects
			trees = []
			junk_nodes = []		# who can't find referrer and is not the type of root
			tot = 0
			for new_node in allnodes:
				tot += 1

				try:
					# Start linking
					linked_flag = False
					for tree in trees:
						pred_id = None
						if new_node.referrer:
							for item in tree.nodes[::-1]:
								if utilities.cmp_url(new_node.referrer, item.url, 'strict'):
									pred_id = item.identifier
									break
						if pred_id:
							# Predecessor found...
							tree.add_node(new_node, pred_id)
							linked_flag = True
							break
						# After all the trees are checked:	
					if not linked_flag:
						raise NewTreeNeeded

				except NewTreeNeeded:
					if new_node.is_root():
						if new_node.status == 200:
							new_tree = mod_tree.Tree()		# new tree
							new_tree.add_node(new_node, None)
							linked_flag = True
							trees.append(new_tree)
					else:
						junk_nodes.append(new_node)

			# Sort trees in the order of ascending time
			trees.sort(lambda x,y: cmp(x,y), lambda x: x[x.root].start_time, False)

			# little trick: treat a tree with one node as the invalid
			# and add its nodes to 'junk_nodes'
			valid_trees = []
			for tree in trees:
				if len(tree.nodes) > 1:
					valid_trees.append(tree)
				else:
					junk_nodes += tree.nodes

			#log('{0} {1} {2}'.format(tot, len(junk_nodes), input))

			# find real page(s) from valid trees.
			real_pages = []
			last = None
			for tree in valid_trees:
				# one tree -> one page
				new_page = WebPage()					# Treat the tree with more than
													# one nodes as a valid tree
				new_page.root = tree[tree.root]
				new_page.objs = tree.nodes
				real_pages.append(new_page)
				last = tree

			# Options: process junk web objects:
			# Add the each object to the nearest
			# web page of 'real_pages'
			junk2 = 0
			for node in junk_nodes:
				found_flag = False
				for page in real_pages[::-1]:
					if cmp(page.root.start_time, node.start_time) < 0:
						found_flag = True
						break
				if found_flag:
					page.objs.append(node)
				else:
					junk2 += 1

			all_real_pages += real_pages[0:1]
			# little trick: with foreknowledge, the first page is the real page
			# so we obtain the first one and drop the others as invalid ones. 

	return all_real_pages, all_objects
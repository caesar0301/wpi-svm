#coding: utf-8
# This program extracts features as the input of LIBSVM from HAR file 
# Author: chenxm


import json, re, math, argparse
import os, uuid, random, datetime
import sys

import lib.tree.node as mod_node
import lib.tree.tree as mod_tree

from lib.myWeb import *
import lib.logbasic as logbasic
import lib.utilities as utilities

(_ROOT, _DEPTH, _WIDTH) = range(3)

log_file = 'log/'+sys.argv[0].replace('.', '_')+'.log'

def log(line):
	global log_file

	print line
	log_h = open(log_file, 'ab')
	log_h.write(line+'\n')
	log_h.flush()
	log_h.close()

class NewTreeNeeded(Exception):
	pass


class MyNode(mod_node.Node, WebObject):
	"""docstring for WebNode"""
	def __init__(self, har_ent):
		nid = str(uuid.uuid1())
		mod_node.Node.__init__(self, 'nd_'+nid, nid)
		WebObject.__init__(self)

		self.pageid = har_ent['pageref']

		sdt = utilities.parse_field(har_ent, 'startedDateTime')
		if sdt is not None:
			self.start_time = logbasic.parse_time(sdt)
		timings = utilities.parse_field(har_ent, 'timings')
		if timings is not None:
			dns = utilities.parse_field(timings, 'dns')
			connect = utilities.parse_field(timings, 'connect')
			send = utilities.parse_field(timings, 'send')
			wait = utilities.parse_field(timings, 'wait')
			receive = utilities.parse_field(timings, 'receive')
			timings = [dns, connect, send, wait, receive]
			timings = [int(i) for i in timings if i != None]
			self.total_time = datetime.timedelta(milliseconds = sum(timings))
			if receive is not None:
				self.receiving_time = int(receive)
		request = utilities.parse_field(har_ent, 'request')
		response = utilities.parse_field(har_ent, 'response')
		if request is not None:
			self.url = utilities.parse_field(request, 'url')
			headers = utilities.parse_field(request, 'headers')
			if headers is not None:
				for field in headers:
					if field['name'] == 'Referer':
						self.referrer = field['value']
		if response is not None:
			self.status = utilities.parse_field(response, 'status')
			self.size = utilities.parse_field(response, 'bodySize')
			content = utilities.parse_field(response, 'content')
			if content is not None:
				self.type = utilities.parse_field(content, 'mimeType')
			headers = utilities.parse_field(response, 'headers')
			for field in headers:
				if field['name'] == 'Location':
					self.re_url = field['value']
				
class MyPage(WebPage):
	def __init__(self, id = None):
		WebPage.__init__(self)
		if id is None:
			id = uuid.uuid4().hex

		self.id = id


def process_har_file(input, urls):
	# Open HAR file
	ifile = open(input, 'rb')
	uni_str = unicode(ifile.read(), 'utf-8', 'replace')
	har_log = json.loads(uni_str)['log']
	har_pages = har_log['pages']
	har_objects = har_log['entries']

	# Extract web objects and order them in time
	allnodes = []
	for i in har_objects:
		new_node = MyNode(i)		# new node
		allnodes.append(new_node)
	allnodes.sort(lambda x,y: cmp(x, y), lambda x: x.start_time, False)

	
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
						if utilities.cmp_url(new_node.referrer, item.url, 'loose'):
							# refer to 'utilities.py' for details about 'loose' parameter
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

	# Find page candidates from valid trees:
	# If the url of page candidate exsits in the groundtruth file,
	# it's considered to be valid.
	pages = []

	# for tree in valid_trees:
	# 	candids = [o.identifier for o in tree.nodes if o.is_root() and o.status==200]

	# 	for id in candids:
	# 		nodeids = [i for i in tree.expand_tree(id, filter = lambda x: x == id or x not in candids)]

	# 		if len(nodeids) > 0:
	# 			# little trick: do not cut the tree with only one node
	# 			new_page = MyPage()
	# 			new_page.add_obj(tree[id], True)
	# 			pages.append(new_page)
	# 			for node in nodeids:
	# 				new_page.add_obj(tree[node])

	# 			if utilities.search_url(new_page.root.url, urls) is True:
	# 				new_page.isvalid = True
	# 			if tree[id].bpointer is not None:
	# 				new_page.ref = tree[tree[id].bpointer]
	# pages.sort(lambda x,y: cmp(x,y), lambda x: x.root.start_time, False)

	for tree in valid_trees:
		###### Detect valid HTML element to be Main Object Candidates (MOCs)
		mocs = []
		for node in tree.expand_tree(mode=_WIDTH):	# must be _WIDTH
			if tree[node].is_root() and int(tree[node].status) == 200:
				mocs.append(node)

		tmp = []
		for moc in mocs[::-1]:
			bp = tree[moc].bpointer
			if bp is None:
				tmp.append(moc)
			else:
				valid_nodes = 0
				for i in tree.expand_tree(moc,filter=lambda x: x==moc or x not in tmp):
					valid_nodes += 1
				# little trick: do not cut the sub tree with only one node
				if valid_nodes>1:
					tmp.append(moc)
		mocs = tmp

		real = []
		for moc in mocs:
			if utilities.search_url(tree[moc].url, urls) is True:
				real.append(moc)

		for rootid in mocs[:]:
			new_page = WebPage()
			pages.append(new_page)
			for nodeid in tree.expand_tree(rootid, filter = lambda x: x==rootid or x not in real):
				if nodeid == rootid:
					new_page.add_obj(tree[nodeid], root=True)
				else:
					new_page.add_obj(tree[nodeid])
			if new_page.root.identifier in real:
				new_page.isvalid = True
			if tree[rootid].bpointer is not None:
				new_page.ref = tree[tree[rootid].bpointer]

	pages.sort(lambda x,y: cmp(x,y), lambda x: x.root.start_time, False)
	print('#Pages-level objs:%d' % len(pages))

	#################################################
	junk2 = len(junk_nodes)
	# Options: process junk web objects:
	# Add the each object to the nearest valid
	# web page.
	
	for node in junk_nodes:
		found_flag = False
		for page in pages[::-1]:
			if cmp(page.root.start_time, node.start_time) < 0:
				found_flag = True
				break
		if found_flag:
			page.junk_objs.append(node)
			junk2 -= 1

	log('{0} {1} {2} {3}'.format(len(valid_trees), len(pages), junk2, input))

	return pages


def main():
	global log_file
	if os.path.exists(log_file):
		os.remove(log_file)
		
	parser = argparse.ArgumentParser(description='This program extracts features \
												as the input of LIBSVM from HAR file ')
	parser.add_argument('harfolder', type=str, help= 'file folder containing HAR \
												file(s). All the HAR files under \
												this folder will be processed.')
	parser.add_argument('pagefile', type=str, help= 'File containing valid page urls.')

	args = parser.parse_args()
	harfolder = args.harfolder
	foldername = os.path.split(harfolder.rstrip('/\\'))[1]
	dumpfile = foldername+'.libsvm'
	
	# Read gt urls from 'gt' parameter.
	gtfile = args.pagefile
	gturls = [i for i in open(gtfile, 'rb') if i.strip('\r\n') != '']

	# Processing all HAR file under the folder
	all_pages = []
	for root, dirs, files in os.walk(harfolder):
		for file in files[:]:
			suffix = file.rsplit('.', 1)[1]
			if suffix != 'har':
				continue
			all_pages += process_har_file(os.path.join(root, file), gturls)
	all_pages.sort(lambda x,y: cmp(x,y), lambda x: x.root.start_time, False)
	log('#Pages-level objs:%d' % len(all_pages))

	# dump LIBSVM instances
	all_instances = []
	inst_pos = 0
	inst_neg = 0
	for pc in all_pages:
		if pc.isvalid:
			log('{0} {1}'.format(pc.root.url, len(pc.objs)))
			label = 1
			inst_pos += 1
		else:
			label = -1
			inst_neg += 1

		pf = PageFeature(pc)
		all_instances.append(pf.assemble_instance(label))

	log('pos#: {0}, neg#: {1}'.format(inst_pos, inst_neg))
	log('write to file "{0}"'.format(dumpfile))
	
	# Write to file
	ofile = open(dumpfile, 'wb')
	ofile.write(''.join(all_instances))
	ofile.close()


if __name__ == '__main__':
	main()

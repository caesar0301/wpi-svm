#coding: utf-8
# This program extracts real page urls of HAR files
# Author: chenxm

import json, re, math, argparse
import os, uuid, random, datetime
import sys

sys.path.append('..')
import lib.tree.node as mod_node
import lib.tree.tree as mod_tree

from lib.myWeb import *
import lib.logbasic
import lib.utilities

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


def process_har_file(input):
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

	# find real page(s) from valid trees.
	real_pages = []
	last = None
	for tree in valid_trees:
		# one tree -> one page
		new_page = MyPage()					# Treat the tree with more than
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

	return real_pages



def main():
	parser = argparse.ArgumentParser(description='This program extracts real page \
												urls of HAR files as groundtruth.')
	parser.add_argument('harfolder', type=str, help= 'file folder containing HAR \
												file(s). All the HAR files under \
												this folder will be processed.')

	args = parser.parse_args()
	harfolder = args.harfolder

	# Processing all HAR file under the folder
	all_real_pages = []
	for root, dirs, files in os.walk(harfolder):
		for file in files:
			suffix = file.rsplit('.', 1)[1]
			if suffix != 'har':
				continue

			all_real_pages += process_har_file(os.path.join(root, file))[0:1]
			# little trick: with foreknowledge, the first page is the real page
			# so we obtain the first one and drop the others as invalid ones. 

	# Write to file
	dumpfile = 'pagetime_gt.txt'
	ofile = open(dumpfile, 'wb')
	for page in all_real_pages:
		ofile.write(str(page.total_seconds())+'\n')
	ofile.close()

main()
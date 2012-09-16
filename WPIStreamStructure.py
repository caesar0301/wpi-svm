# coding: utf-8
# Author: chenxm, 2012-06-03
import argparse, re, datetime
from subprocess import *
import os, sys

import lib.logbasic as basic
from lib.myWeb import WebPage
from lib.myGraph import *
import lib.utilities as utilities

(_ROOT, _DEPTH, _WIDTH) = range(3)

this_log = './log/'+sys.argv[0].replace('.', '_')+'.log'
log_h = open(this_log, 'wb')

def log(line):
	global log_h
	print line
	log_h.write(line+'\n')

def process_tree(tree, k, t):
	mocs = []
	for node in tree.expand_tree(mode=_WIDTH):	# must be _WIDTH
		if tree[node].is_root() and int(tree[node].status) == 200:
			mocs.append(node)

	valid = []
	for moc in mocs[::-1]:
		root = tree[moc]
		bp = tree[moc].bpointer
		if bp is None:
			valid.append(moc)
		else:
			pred = tree[bp]
			all_nodes = []
			for i in tree.expand_tree(moc,filter=lambda x: x==moc or x not in valid):
				all_nodes.append(i)

			if len(all_nodes)>k:
				if root.start_time - pred.start_time >= datetime.timedelta(seconds=t):
					valid.append(moc)

	###### parse pages
	pages = []
	for rootid in valid[::-1]:
		new_page = WebPage()
		new_page.add_obj(tree[rootid], True)
		pages.append(new_page)
		for nodeid in tree.expand_tree(rootid, filter = lambda x: x==rootid or x not in valid):
			new_page.add_obj(tree[nodeid])

	return pages


def main():
	parser = argparse.ArgumentParser(description='Page reconstruction from weblog using StreamStructure algorithm proposed by S. Ihm on IMC 2011.')
	parser.add_argument('-k', type=int, default = 2, help= 'T parameter')
	parser.add_argument('-t', type=int, default = 5, help= 'T parameter')
	parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
	args = parser.parse_args()
	log_file = args.logfile
	detected_pageurl = log_file+'.page.tmp'
	K = [args.k]
	T = [args.t]

	print 'Reading log...'
	all_lines = basic.read(log_file)

	print 'Processing rrp...'
	all_nodes = []
	for line in all_lines:
		all_nodes.append(basic.NodeFromLog(line))
	all_nodes.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)

	###### construct trees

	print 'Creating graph...'
	new_graph = Graph()
	for node in all_nodes:
		new_graph.add_node(node)
	trees = new_graph.all_trees()
	junk_nodes = new_graph.junk_nodes
	# little trick: treat a tree with one node 
	# as the invalid and add its nodes to 'junk_nodes'
	valid_trees = []
	for tree in trees:
		if len(tree.nodes) > 1:
			valid_trees.append(tree)
		else:
			junk_nodes += tree.nodes

	print('valid trees: {0}, junk_nodes: {1}'.format(len(valid_trees), len(junk_nodes)))

	###### cut pages
	K = [1]
	T = [i/10.0 for i in range(2, 200, 2)]

	for k in K:
		for t in T:
			log('#############')
			log('K = %d, T = %.2f' % (k, t))

			all_pages = []
			for tree in valid_trees:
				all_pages += process_tree(tree, k, t)

			log('Pages:%d' % len(all_pages))
			
			all_urls = [i.root.url for i in all_pages]
			ofile = open(detected_pageurl, 'wb')
			ofile.write('\n'.join(all_urls))
			ofile.close()

			page_gt = log_file.split('.')[0]+'.page'
			cmd = 'python tools/check_urls.py "{0}" "{1}"'.format(detected_pageurl, page_gt)
			f = Popen(cmd, shell=True, stdout=PIPE).stdout
			for line in f:
				log(line.strip(" \r\n"))

if __name__ == '__main__':
	main()

log_h.close()

# coding: utf-8
# Author: chenxm, 2012-06-03
import argparse, re, datetime

import logbasic as basic
from myWeb import WebPage
from myGraph import *
import utilities
	
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
		#print main_obj_cands
		# Find final page roots
		real_roots = []
		for cand in main_obj_cands:
			cand_pred_id = cand.bpointer
			new_root = None
			#print cand_pred_id
			if cand_pred_id is not None:
				cand_pred = tree[cand_pred_id]
				#print cand.start_time - cand_pred.start_time
				if cand.start_time - cand_pred.start_time >= datetime.timedelta(seconds = T):
					new_root = cand
			#print new_root
			if new_root is None:
				# Do not make this node as root
				# but it still exists on the tree
				continue
			else:
				real_roots.append(new_root)
		real_roots_ids = [i.identifier for i in real_roots]
		#print real_roots_ids
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
		all_nodes.append(create_node_from_rr(rr))
	all_nodes.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)
		
	new_graph = Graph()
	print 'processing nodes...'
	for node in all_nodes:
		new_graph.add_node(node)
	print 'graph ready...'
	print 'finding pages...'
	all_trees = new_graph.all_trees()
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
# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import json, re
import hashlib
import argparse

from myWeb import WebPage, PageFeature
import logbasic as basic
from myGraph import *
import utilities
			
def get_value(dict, key):
	try:
		value = dict[key]
		if value == 'N/A':
			raise KeyError
	except KeyError:
		value = None
	return value
	
def process_tree(tree):
	t_refs = tree.ref_node_d.values()	# We choose all the referred nodes as main object candidates
	main_obj_cands = []
	for i in t_refs:
		if tree[i].is_root():
			main_obj_cands.append(tree[i])
	pages = []
	if len(main_obj_cands) > 0:
		main_obj_cands.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)	# ordered by +time
		cand_ids = [i.identifier for i in main_obj_cands]
		# Find final page roots
		roots = []
		for cand in main_obj_cands:
			cand_pred_id = cand.bpointer
			cand_pred = None
			if cand_pred_id is not None:
				cand_pred = tree[cand_pred_id]
			roots.append((cand, cand_pred))
		rootids = [i[0].identifier for i in roots]
		for root in roots:
			new_page = WebPage()
			new_page.root = root[0]
			new_page.ref = root[1]
			new_page.add_obj(root[0], True)
			pages.append(new_page)
			for nodeid in tree.expand_tree(root[0].identifier, filter = lambda x: x not in rootids):
				new_page.add_obj(tree[nodeid])
	return pages
					
def process_log(logfile, gt_urls):
	""" Processing log file
	logfile: name of logfile
	gt_urls: name of file storing valid urls to deduce the labels of instances
	outfile: name of output file
	"""
	valid_urls = open(gt_urls, 'rb').read().split('\n')
	print 'reading log...'
	all_rr = basic.read(logfile)
	
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
		all_pages += process_tree(tree)
	print 'Pages:', len(all_pages)
	
	def gen_label(urls, url):
		for i in urls:
			if utilities.remove_url_prefix(url) == utilities.remove_url_prefix(i):
				return 1
		return -1
	
	all_instances = []
	instances_pos = []
	instances_neg = []
	pos_cnt = 0
	neg_cnt = 0	
	for page in all_pages:
		# log page cands' urls
		##################################
		urlfile = open(logfile+'.instance.url', 'ab')
		urlfile.write(page.root.url+'\n')
		urlfile.close()
		##################################
		pf = PageFeature(page)
		label = gen_label(valid_urls, page.root.url)
		# Rewrite label
		if len(page.objs) <= 1:
			label = -1

		instance = pf.assemble_instance(label)
		if label == 1:
			instances_pos.append(instance)
		else:
			instances_neg.append(instance)
	all_instances = instances_pos + instances_neg
	print 'positive#: ', len(instances_pos)
	print 'negtive#: ', len(instances_neg)
	##################################
	ofile = open(logfile+'.instance', 'wb')
	ofile.write(''.join(all_instances))
	ofile.close()
	##################################
	print 'writing instances to "%s.instance"' % logfile
	print 'writing candidate URLs to "%s.instance.url"' % logfile
	
def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from log. Output = logfile.instance')
	parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
	parser.add_argument('urlfile', type=str, help= 'Groudtruth urls used to deduce labels of instances.')

	args = parser.parse_args()
	process_log(args.logfile, args.urlfile)

if __name__ == "__main__":
	main()
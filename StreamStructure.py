# coding: utf-8
# Author: chenxm, 2012-06-03
import argparse, re, datetime
from subprocess import *

import logbasic as basic
from myWeb import WebPage
from myGraph import *
import utilities

def log(line):
    print line
    log_file = open('SSLog.txt', 'ab')
    log_file.write(line+'\n')
    log_file.flush()
    log_file.close()
	
def process_tree(tree, K, T, V = None):
	###### parse page root cands

	mocs = []		# main object cands
	for i in tree.nodes:
		if i.is_root and len(i.fpointer) >= K:
			# HTML object with embedded objects greater than K
			mocs.append(i)

	###### parse pages
	pages = []
	if len(mocs) > 0:
		mocs.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)	# ordered by +time
		cand_ids = [i.identifier for i in mocs]

		# Find final page roots
		real_roots = []
		for cand in mocs:
			cand_pred_id = cand.bpointer
			new_root = None
			if cand_pred_id is not None:
				cand_pred = tree[cand_pred_id]
				if cand.start_time - cand_pred.start_time >= datetime.timedelta(seconds = T):
					if V is not None:
						pass
					else:
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
			
parser = argparse.ArgumentParser(description='Page reconstruction from weblog using StreamStructure algorithm proposed by S. Ihm on IMC 2011.')
parser.add_argument('-k', type=int, default = 2, help= 'T parameter')
parser.add_argument('-t', type=int, default = 5, help= 'T parameter')
    parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
args = parser.parse_args()
log_file = args.logfile
detected_pageurl = log_file+'.page.tmp'
K = [args.k]
T = [args.t]

print 'reading log...'
all_rr = basic.read(log_file)

print 'processing rrp...'
all_nodes = []
for rr in all_rr:
	all_nodes.append(create_node_from_rr(rr))
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

###### cut pages
#K = [1,2,3,4,5]
#T = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10]
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

                    page_gt = 'E:/Cloud/SkyDrive/data/icnc2013/manual.log.instance.page'
                    cmd = 'check_urls.py "{0}" "{1}"'.format(detected_pageurl, page_gt)
                    f = Popen(cmd, shell=True, stdout=PIPE).stdout
                    for line in f:
                            log(line.strip(" \r\n"))

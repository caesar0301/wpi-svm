# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import json, re, sys, os
import hashlib, argparse

from myWeb import WebPage, PageFeature
import logbasic as basic
from myGraph import *
import utilities

log_file = sys.argv[0].replace('.', '_')+'.log'

def log(line):
    global log_file

    print line
    log_h = open(log_file, 'ab')
    log_h.write(line+'\n')
    log_h.flush()
    log_h.close()

			
def get_value(dict, key):
	try:
		value = dict[key]
		if value == 'N/A':
			raise KeyError
	except KeyError:
		value = None
	return value


class MyPage(WebPage):
	def __init__(self, id = None):
		WebPage.__init__(self)
		if id is None:
			id = uuid.uuid4().hex

		self.id = id
		self.isvalid = False

					
def process_log(logfile, gt_urls):
	valid_urls = [i.strip('\r\n') for i in open(gt_urls, 'rb')]
	
	###### preprocess log
	print 'Reading log...'
	all_rr = basic.read(logfile)
	all_nodes = []
	for rr in all_rr:
		all_nodes.append(create_node_from_rr(rr))
	all_nodes.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)
		
	###### construct link trees

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
	
	log('valid trees: {0}, junk_nodes: {1}'.format(len(valid_trees), len(junk_nodes)))
	
	###### parse page cands
	all_pages = []
	for tree in valid_trees:
		candids = [o.identifier for o in tree.nodes if o.is_root()]

		for id in candids:
			nodeids = [i for i in tree.expand_tree(id, filter = lambda x: x not in candids) if i not in candids]
			if len(nodeids) > 0:
				# little trick: do not cut the tree with only one node
				new_page = MyPage()
				new_page.add_obj(tree[id], True)
				all_pages.append(new_page)
				for node in nodeids:
					new_page.add_obj(tree[node])
				if utilities.search_url(new_page.root.url, valid_urls) is True:
					new_page.isvalid = True
				if tree[id].bpointer is not None:
					new_page.ref = tree[tree[id].bpointer]

	all_pages.sort(lambda x,y: cmp(x,y), lambda x: x.root.start_time, False)
	log('Pages:%d' % len(all_pages))
	
	junk2 = len(junk_nodes)
	for node in junk_nodes:
		found_flag = False
		for page in all_pages[::-1]:
			if cmp(page.root.start_time, node.start_time) < 0:
				found_flag = True
				break
		if found_flag:
			page.junk_objs.append(node)
			junk2 -= 1

	###### extract instances

	all_instances = []
	instance_pos_url = []
	pos_cnt = 0
	neg_cnt = 0	
	for page in all_pages:
		pf = PageFeature(page)
		if page.isvalid:
			log('{0} {1}'.format(page.root.url, len(page.objs)))
			instance_pos_url.append(page.root.url)
			label = 1
			pos_cnt += 1
		else:
			label = -1
			neg_cnt += 1
		instance = pf.assemble_instance(label)
		all_instances.append(instance)
	log('pos:{0}, neg:{1}'.format(pos_cnt, neg_cnt))

	return all_instances, instance_pos_url


	
def main():
	global log_file
	if os.path.exists(log_file):
		os.remove(log_file)

	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from log. Output = logfile.instance')
	parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
	parser.add_argument('urlfile', type=str, help= 'Groudtruth urls used to deduce labels of instances.')

	args = parser.parse_args()
	logfile = args.logfile
	urlfile = args.urlfile
	log_instance = logfile+'.instance'
	instance_page = log_instance+'.page'

	(instances, pageurls) = process_log(logfile, urlfile)

	######  write to file
	ofile = open(log_instance, 'wb')
	ofile.write(''.join(instances))
	ofile.flush()
	ofile.close()

	# ofile = open(instance_page, 'wb')
	# ofile.write('\n'.join(pageurls))
	# ofile.flush()
	# ofile.close()

	log('writing instances to "%s"' % log_instance)
	#log('writing pages to "%s"' % instance_page)

if __name__ == "__main__":
	main()

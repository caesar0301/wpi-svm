# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import sys, os
import argparse
import re

from myWeb import WebPage
import logbasic as basic
import utilities
import svm
import har

(_ROOT, _DEPTH, _WIDTH) = range(3)

def get_svm_pages(all_objects, valid_urls, predicted_file):

	(valid_trees, all_pages, junk_nodes) = svm.parse_pages_svm(all_objects, valid_urls)

	# read pridicted lables
	all_labels = [i.rstrip(' \r\n') for i in open(predicted_file, 'rb')]
	tp_pages = []
	fp_pages = []

	print len(all_pages), len(all_labels)
	assert len(all_pages) == len(all_labels)

	for i in range(0, len(all_pages)):
		if all_labels[i] == '1':
			if all_pages[i].isvalid:
				tp_pages.append(all_pages[i])
			else:
				fp_pages.append(all_pages[i])

	pos_pages = tp_pages + fp_pages
	tp_roots = [i.root.identifier for i in tp_pages]
	fp_roots = [i.root.identifier for i in fp_pages]
	pos_roots = [i.root.identifier for i in pos_pages]

	# recut trees using predicted page candidates
	print 'Predicted pos:', len(pos_roots)
	recut_pos_pages = []
	for tree in valid_trees:
		local_pos_roots = [i for i in tree.expand_tree(filter = lambda x: x in pos_roots)]
		for root in local_pos_roots:
			new_page = WebPage()
			new_page.add_obj(tree[root], root=True)
			for node in tree.expand_tree(root, filter = lambda x: x==root or x not in local_pos_roots):
				new_page.add_obj(tree[node])
			recut_pos_pages.append(new_page)
			

	recut_pos_pages.sort(lambda x,y: cmp(x,y), lambda x: x.root.start_time, False)

	# add junk nodes to recut pos pages
	junk2 = len(junk_nodes)
	for node in junk_nodes:
		found_flag = False
		for page in recut_pos_pages[::-1]:
			if cmp(page.root.start_time, node.start_time) < 0:
				found_flag = True
				break
		if found_flag:
			page.junk_objs.append(node)
			junk2 -= 1

	recut_tp_pages = []
	recut_fp_pages = []
	for page in recut_pos_pages:
		if page.root.identifier in tp_roots:
			recut_tp_pages.append(page)
		elif page.root.identifier in fp_roots:
			recut_fp_pages.append(page)

	return recut_pos_pages, recut_tp_pages


def pagetime(all_real_pages, recut_tp_pages):
	real_pages = {}
	tp_pages = {}
	for page in all_real_pages:
		real_pages[page.root] = page.total_seconds()
	for page in recut_tp_pages:
		tp_pages[page.root] = page.total_seconds()

	ret = []
	for root in real_pages.keys():
		if root in tp_pages:
			ret.append((real_pages[root], tp_pages[root]))

	return ret



def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from log. Output = logfile.instance')
	parser.add_argument('harfolder', type=str, help= '')
	parser.add_argument('predictfile', type=str, help= '')

	args = parser.parse_args()
	harfolder = args.harfolder
	predicted_file = args.predictfile

	# Ground truth
	(all_real_pages, all_objects) = har.parse_pages_har(harfolder)
	valid_urls = [i.root.url for i in all_real_pages]

	# Reset nodes. One whole day wasted...Shit!@@
	for node in all_objects:
		node.bpointer = None
		node.fpointer = []
	
	# detected pages with SVM
	(recut_pos_pages, recut_tp_pages) = get_svm_pages(all_objects, valid_urls, predicted_file)


	timetuple = pagetime(all_real_pages, recut_tp_pages)

	# page timings
	pagetimings = ['{0} {1}'.format(i[0], i[1]) for i in timetuple if i[0]>0 and i[1]>0]
	ofile = open('m_pagetime.txt', 'wb')
	ofile.write('\n'.join(pagetimings))
	ofile.close()




if __name__ == "__main__":
	main()

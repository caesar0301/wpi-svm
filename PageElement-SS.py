# coding: utf-8
# Author: chenxm, 2012-07-14
import json, re, sys, os
import hashlib, argparse

from lib.myWeb import WebPage, PageFeature
import lib.logbasic as basic
from lib.myGraph import *
import lib.utilities as utilities
import lib.HAR as HAR
import WPIStreamStructure as SS

(_ROOT, _DEPTH, _WIDTH) = range(3)

def get_ss_pages(all_objects, valid_pages):
	k = 1
	t = 10

	all_objects.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)

	###### construct link trees
	print 'Creating graph...'
	new_graph = Graph()
	for node in all_objects:
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

	###### parse page cands
	all_pages = []
	for tree in valid_trees:
		all_pages += SS.process_tree(tree,k, t)

	all_pages.sort(lambda x,y: cmp(x,y), lambda x: x.root.start_time, False)
	print('Pages:%d' % len(all_pages))

	# add junk nodes to recut pos pages
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

	tp_pages = []
	fp_pages = []
	for page in all_pages:
		if page.root.identifier in valid_pages:
			tp_pages.append(page)
		else:
			fp_pages.append(page)
	return all_pages, tp_pages


def check_objects(all_real_pages, pos_pages):
	all_objects = []
	for page in all_real_pages:
		all_objects += page.objs + page.junk_objs

	real_obj_root_d = {}	# {object: root}
	svm_obj_root_d = {}

	for page in all_real_pages:
		objs = page.objs + page.junk_objs
		all_objects += objs
		for obj in objs:
			real_obj_root_d[obj] = page.root

	for page in pos_pages:
		objs = page.objs + page.junk_objs
		for obj in objs:
			svm_obj_root_d[obj] = page.root

	classified_right = []
	classified_wrong = []
	missed = []
	for key in real_obj_root_d.keys():
		try:
			if real_obj_root_d[key] == svm_obj_root_d[key]:
				classified_right.append(key)
			else:
				classified_wrong.append(key)
		except KeyError:
			missed.append(key)

	return classified_right, classified_wrong, missed

	

def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from log. Output = logfile.instance')
	parser.add_argument('harfolder', type=str, help= '')

	args = parser.parse_args()
	harfolder = args.harfolder

	# Ground truth
	(all_real_pages, all_objects) = HAR.parse_pages_har(harfolder)
	valid_pages = [i.root.identifier for i in all_real_pages]

	for node in all_objects:
		node.bpointer = None
		node.fpointer = []

	# detected pages with SVM
	(pos_pages, tp_pages) = get_ss_pages(all_objects, valid_pages)

	# objects status
	print 'real pages:',len(all_real_pages)
	print 'detected pages:', len(pos_pages)

	(classified_right, classified_wrong, missed) = \
			check_objects(all_real_pages, pos_pages)

	print 'right {0} wrong {1} missed {2}'.format(len(classified_right), len(classified_wrong), len(missed))

	def which_type(obj):
		subtype_re = {
			r'.*(jpeg|jpg|gif|png|bmp|ppm|pgm|pbm|pnm|tiff|exif|cgm|svg).*': 'image',
			r'.*(flash|flv).*': 'flash',
			r'.*(css).*': 'css',
			r'.*(javascript|js).*': 'js',
			r'.*(html|htm).*': 'html',
		}
		if obj.type != None:
			for regex in subtype_re.keys():
				if re.match(re.compile(regex, re.I), obj.type):
					return subtype_re[regex]
				else:
					continue
		return 'others'

	def stat(objects):
		html = 0
		js = 0
		css = 0
		flash = 0
		image = 0
		others = 0
		for obj in objects:
			objtype = which_type(obj)
			if objtype == 'html':
				html += 1
			elif objtype == 'js':
				js += 1
			elif objtype =='css':
				css += 1
			elif objtype == 'flash':
				flash += 1
			elif objtype == 'image':
				image += 1
			elif objtype == 'others':
				others += 1
		print 'html {0} js {1} css {2} flash {3} image {4} others{5}'.\
				format(html, js, css, flash,image,others)

	stat(classified_right)
	stat(classified_wrong)
	stat(missed)


if __name__ == "__main__":
	main()

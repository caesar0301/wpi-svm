# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import sys, os
import argparse
import re

from lib.myWeb import WebPage
import lib.logbasic as basic
import lib.utilities as utilities
import lib.svm as svm
import lib.HAR as har

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


def check_objects(all_real_pages, recut_pos_pages):
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

	for page in recut_pos_pages:
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

	# Ground truth pagetime
	dumpfile = 'pagetime_gt.txt'
	ofile = open(dumpfile, 'wb')
	for page in all_real_pages:
		ofile.write(str(page.total_seconds())+'\n')
	ofile.close()
	
	# detected pages with SVM
	(recut_pos_pages, recut_tp_pages) = get_svm_pages(all_objects, valid_urls, predicted_file)

	# page timings
	# pagetimings = [str(i.total_seconds()) for i in recut_pos_pages if i.total_seconds() > 0]
	# ofile = open('pagetime_svm_pos.txt', 'wb')
	# ofile.write('\n'.join(pagetimings))
	# ofile.close()

	# pagetimings = [str(i.total_seconds()) for i in recut_tp_pages if i.total_seconds() > 0]
	# ofile = open('pagetime_svm_tp.txt', 'wb')
	# ofile.write('\n'.join(pagetimings))
	# ofile.close()

	# objects status
	(classified_right, classified_wrong, missed) = \
			check_objects(all_real_pages, recut_pos_pages)

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

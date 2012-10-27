# coding: utf-8
# Author: chenxm, 2012-07-14
import json, re, sys, os
import hashlib, argparse

sys.path.append('..')
from lib.myWeb import WebPage, PageFeature
import lib.logbasic as basic
from lib.myGraph import *
import lib.utilities as utilities
import lib.har as HAR

(_ROOT, _DEPTH, _WIDTH) = range(3)

def get_time_pages(all_objects, valid_pages):
	t = 4.4	##################

	all_objects.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)

	all_pages = []
	last_page = None
	last_node = None
	for node in all_objects:
		if last_page is None:
			new_page = WebPage()
			all_pages.append(new_page)
			new_page.add_obj(node, root = True)
			last_page = new_page
		else:
			if node.start_time - last_node.start_time >= datetime.timedelta(seconds=t):
				new_page = WebPage()
				all_pages.append(new_page)
				new_page.add_obj(node, root = True)
				last_page = new_page
			else:
				last_page.add_obj(node)
		last_node = node

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
	(pos_pages, tp_pages) = get_time_pages(all_objects, valid_pages)

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

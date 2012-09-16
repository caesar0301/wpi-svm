# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import json, re, sys, os
import hashlib, argparse

from lib.myWeb import PageFeature
import lib.logbasic as basic
import lib.svm as svm
from lib.utilities import Logger

###### logger
this_log = './log/'+sys.argv[0].replace('.', '_')+'.log'
print 'Log file: %s' % this_log
log_h = Logger(this_log)

					
def process_log(logfile):
	###### preprocess log
	print 'Processing HTTP logs...'
	all_lines = basic.read(logfile)
	all_nodes = []
	for line in all_lines:
		all_nodes.append(basic.NodeFromLog(line))
	all_nodes.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)
	return all_nodes

def gen_instances(all_nodes, valid_urls):
	global log_h

	# Parse pages for SVM
	(valid_trees, all_pages, junk_nodes) = svm.parse_pages_svm(all_nodes, valid_urls)
	
	###### add junk
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

	print len(all_pages)

	all_instances = []
	instance_pos_url = []
	pos_cnt = 0
	neg_cnt = 0	
	for page in all_pages:
		pf = PageFeature(page)
		if page.isvalid:
			#log('{0} {1}'.format(page.root.url, len(page.objs)))
			instance_pos_url.append(page.root.url)
			label = 1
			pos_cnt += 1
		else:
			label = -1
			neg_cnt += 1
		instance = pf.assemble_instance(label)
		all_instances.append(instance)

	log_h.log('#Page:{0}\n#Non-page:{1}'.format(pos_cnt, neg_cnt))

	return all_instances, instance_pos_url


	
def main():
	global log_h
	
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from log. Output = logfile.instance')
	parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
	parser.add_argument('urlfile', type=str, help= 'Groudtruth urls used to deduce labels of instances.')

	args = parser.parse_args()
	logfile = args.logfile
	urlfile = args.urlfile
	log_instance = logfile+'.libsvm'
	instance_page = log_instance+'.page'

	###### valid URLs
	valid_urls = [tuple(i.rstrip('\r \n').split('\t')) for i in open(urlfile, 'rb')]

	###### process log
	all_nodes = process_log(logfile)

	###### parse pages
	(instances, pageurls) = gen_instances(all_nodes, valid_urls)

	######  write to file
	ofile = open(log_instance, 'wb')
	ofile.write(''.join(instances))
	ofile.flush()
	ofile.close()

	ofile = open(instance_page, 'wb')
	ofile.write('\n'.join(pageurls))
	ofile.flush()
	ofile.close()

	log_h.log('writing instances to "%s"' % log_instance)
	#log('writing pages to "%s"' % instance_page)
	log_h.close()

if __name__ == "__main__":
	main()

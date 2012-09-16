import argparse, sys
from subprocess import *

import lib.logbasic as logbasic
from lib.myGraph import *
from lib.myWeb import WebPage, WebObject
from lib.utilities import Logger

parser = argparse.ArgumentParser(description='Page reconstruction from weblog using time-based approach.')
parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
args = parser.parse_args()
input_file = args.logfile
detected_pageurl = input_file+'.page.tmp'

###### logging
this_log = './log/'+sys.argv[0].replace('.', '_')+'.log'
log_h = Logger(this_log)
print 'log file: %s' % this_log

###### read HTTP log
print 'Reading log...'
all_lines = logbasic.read(input_file)

print 'Processing rrp...'
all_nodes = []
for line in all_lines:
	all_nodes.append(logbasic.NodeFromLog(line))
all_nodes.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)

print len(all_nodes)

T = [i/10.0 for i in range(2, 200, 2)]
for t in T:
	log_h.log('########################\n')
	log_h.log(str(t))
	all_pages = []
	last_page = None
	last_node = None
	for node in all_nodes:
		if last_page is None and node.is_root():
			new_page = WebPage()
			all_pages.append(new_page)
			new_page.add_obj(node, root = True)
			last_page = new_page
		else:
			if node.is_root() and \
node.start_time - last_node.start_time >= datetime.timedelta(seconds=t):
				new_page = WebPage()
				all_pages.append(new_page)
				new_page.add_obj(node, root = True)
				last_page = new_page
			else:
				last_page.add_obj(node)
		last_node = node

	print len(all_pages)

	all_urls = [i.root.url for i in all_pages]
	ofile = open(detected_pageurl, 'wb')
	ofile.write('\n'.join(all_urls))
	ofile.close()

	page_gt = input_file.split('.')[0]+'.page'
	cmd = 'python tools/check_urls.py "{0}" "{1}"'.format(detected_pageurl, page_gt)
	f = Popen(cmd, shell=True, stdout=PIPE).stdout
	for line in f:
		log_h.log(line.strip(" \r\n"))

log_h.close()
import argparse, sys
from subprocess import *

sys.path.append('..')
import lib.logbasic as logbasic
from lib.myGraph import *
from lib.myWeb import WebPage, WebObject
from lib.utilities import Logger

parser = argparse.ArgumentParser(description='Page reconstruction from weblog using type-based approach.')
parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
args = parser.parse_args()
input_file = args.logfile
detected_pageurl = input_file+'.page.tmp'

###### logging
this_log = './log/'+sys.argv[0].replace('.', '_')+'.log'
log_h = Logger(this_log)
print 'log file: %s' % this_log

print 'Reading log...'
all_lines = logbasic.read(input_file)

print 'Processing rrp...'
all_nodes = []
for line in all_lines:
	all_nodes.append(logbasic.NodeFromLog(line))
all_nodes.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)

all_pages = []
last_page = None
for node in all_nodes:
	if node.is_root():
		new_page = WebPage()
		new_page.add_obj(node, root = True)
		all_pages.append(new_page)
		last_page = new_page
	else:
		if last_page is not None:
			last_page.add_obj(node)

print len(all_nodes)
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
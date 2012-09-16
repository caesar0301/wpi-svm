#coding: utf-8
# This program extracts real page urls of HAR files
# Author: chenxm

import argparse
import sys, os

import lib.HAR as HAR

log_file = 'log/'+sys.argv[0].replace('.', '_')+'.log'
log_h = open(log_file, 'wb')

def log(line):
    global log_h
    print line
    log_h.write(line+'\n')

def main():
	parser = argparse.ArgumentParser(description='This program extracts real page \
												urls of HAR files as groundtruth.')
	parser.add_argument('harfolder', type=str, help= 'File folder containing HAR \
												file(s). All the HAR files under \
												this folder will be processed.')
	parser.add_argument('output', type=str, help= 'Output data.')

	args = parser.parse_args()
	harfolder = args.harfolder
	dumpfile = args.output

	(all_pages, all_objs) = HAR.parse_pages_har(harfolder)

	# Write to file
	if os.path.exists(dumpfile):
		os.remove(dumpfile)
	ofile = open(dumpfile, 'wb')
	
	i = 0	# counter
	for p in all_pages:
		if p.root:
			i += 1
			ofile.write("{0}\t{1}\n".format(p.root.url, p.root.start_time))

	print('write {0} real pages to: {1}'.format(i, dumpfile))
	ofile.flush()
	ofile.close()


if __name__ == '__main__':
	main()

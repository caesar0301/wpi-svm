#coding: utf-8
# This program extracts features as the input of LIBSVM from HAR file 
# Author: chenxm

import json, re, math, argparse, os
from myweb import WebObject as WO
from myweb import WebPage as PageCand
from myweb import PageFeature as Feature

class WebObject(WO):
	""" Defining the class for web objects extracted from HAR file.
	"""
	def __init__(self, har_ent):
		""" har_ent: web entry of HAR file
		"""
		WO.__init__(self)
		self.start_time = None
		self.total_time = har_ent['time']
		self.receiving_time = har_ent['timings']['receive']
		request = har_ent['request']
		response = har_ent['response']
		self.url = request['url']
		self.status = response['status']
		self.size = response['bodySize']
		self.type = response['content']['mimeType']
		self.referrer = None
		for field in request['headers']:
			if field['name'] == 'Referer':
				self.referrer = field['value']
		self.re_url = None
		for field in response['headers']:
			if field['name'] == 'Location':
				self.re_url = field['value']
				
def process_har_file(input, output):
	""" Processing HAR file
	input: the relative or absolute filename of HAR file
	output: the output filename including instances as input of LIBSVM
	"""
	# Open HAR file
	ifile = open(input, 'rb')
	uni_str = unicode(ifile.read(), 'utf-8', 'replace')
	har_log = json.loads(uni_str)['log']
	web_pages = har_log['pages']
	print 'web pages# ', len(web_pages)
	web_objects = har_log['entries']
	print 'web objects# ', len(web_objects)

	page_cands = []
	junk_html_objs = []
	junk_nonhtml_objs = []
	for obj in web_objects:
		wo = WebObject(obj)
		if wo.is_root():
			if wo.status in [200]:	#?? 301, 302
				new_page_c = PageCand(wo)
				page_cands.append(new_page_c)
			else:
				junk_html_objs.append(wo)
		else:
			found = False
			for pc in page_cands:
				if pc.own_this(wo):
					pc.add_obj(wo)
					found = True
					break
			if found is False:
				junk_nonhtml_objs.append(wo)

	# for pc in page_cands:
	# 	print pc.root.url
	# 	#print pc.root.status
	# 	print len(pc.objs)
	# print 'junks html:', len(junk_html_objs)
	# for i in junk_html_objs:
	# 	print i.status, i.referrer, i.re_url
	# print 'junks nonhtml:', len(junk_nonhtml_objs)
	# for i in junk_nonhtml_objs:
	# 	print i.url
	# 	print i.referrer
	
	all_instances = []
	for pc in page_cands:
		if page_cands.index(pc) == 0:
			label = 1
		else:
			label = 0
		pf = Feature(pc)
		instance = pf.assemble_instance(label)
		print instance
		all_instances.append(instance)
	ofile = open(output, 'wb')
	ofile.write('\n'.join(all_instances))
	ofile.close()

def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from HAR file')
	parser.add_argument('-f', '--input', type=str, help= 'a single HAR file as input')
	parser.add_argument('-b', '--batch', type=str, help= 'file folder containing HAR file(s). \
						All the HAR files under this folder will be processed.')
	parser.add_argument('-o', '--output', type=str, default = 'hardata', help= 'output file containing LIBSVM instances')

	args = parser.parse_args()
	input_file = args.input
	input_folder = args.batch
	output_file = args.output
	if input_file is None and input_folder is None:
		parser.print_help()
		exit(1)
	else:
		if input_file is not None:
			process_har_file(input_file, output_file)
		elif input_folder is not None:
			# Processing all HAR file under the folder
			for root, dirs, files in os.walk(input_folder):
				for file in files:
					suffix = file.rsplit('.', 1)[1]
					if suffix != 'har':
						continue
					process_har_file(os.path.join(root, file), output_file)


if __name__ == '__main__':
	main()
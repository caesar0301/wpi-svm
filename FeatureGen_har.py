#coding: utf-8
# This program extracts features as the input of LIBSVM from HAR file 
# Author: chenxm

import json, re, math, argparse, os, uuid, random
from myweb import WebObject
from myweb import WebPage
from myweb import PageFeature

def parse_field(dict, key):
	""" Simple dict wrapper
	dict: name of dict object
	key: name of key
	Return: dict[key] or None
	"""
	try:
		value = dict[key]
	except KeyError:
		value = None
	return value

class MyObject(WebObject):
	""" Defining the class for web objects extracted from HAR file.
	"""
	def __init__(self, har_ent):
		""" har_ent: web entry of HAR file
		"""
		WebObject.__init__(self)
		self.pageid = har_ent['pageref']
		self.start_time = None
		self.total_time = parse_field(har_ent, 'time')
		timings = parse_field(har_ent, 'timings')
		if timings is not None:
			self.receiving_time = parse_field(timings, 'receive')
		request = parse_field(har_ent, 'request')
		response = parse_field(har_ent, 'response')
		if request is not None:
			self.url = parse_field(request, 'url')
			headers = parse_field(request, 'headers')
			if headers is not None:
				for field in headers:
					if field['name'] == 'Referer':
						self.referrer = field['value']
		if response is not None:
			self.status = parse_field(response, 'status')
			self.size = parse_field(response, 'bodySize')
			content = parse_field(response, 'content')
			if content is not None:
				self.type = parse_field(content, 'mimeType')
			headers = parse_field(response, 'headers')
			for field in headers:
				if field['name'] == 'Location':
					self.re_url = field['value']
				
class MyPage(WebPage):
	"""
	"""
	def __init__(self, id = None):
		WebPage.__init__(self)
		if id is None:
			id = uuid.uuid4().hex
		self.id = id
				
def process_har_file(input):
	""" Processing HAR file
	input: the relative or absolute filename of HAR file
	Return: list of real pages identified by pageref in HAR file
		&&	list of page candidates
	"""
	# Open HAR file
	ifile = open(input, 'rb')
	uni_str = unicode(ifile.read(), 'utf-8', 'replace')
	har_log = json.loads(uni_str)['log']
	web_pages = har_log['pages']
	web_objects = har_log['entries']
	# find real pages which are recorded in HAR file.
	real_pages = []
	for item in web_pages:
		new_page = MyPage(item['id'])
		real_pages.append(new_page)
	for item in web_objects:
		wo = MyObject(item)
		found_page = None
		for i in real_pages:
			if i.id == wo.pageid:
				found_page = i
				break
		if found_page:
			found_page.add_obj(wo)	# all objects are added
			if wo.status == 200 and wo.is_root():
				if found_page.root is None:
					found_page.root = wo
		else:
			print 'HAR error: entry ref error.'
			assert(0)		
	# find page candidates
	page_cands = []
	junk_html_objs = []
	junk_nonhtml_objs = []
	all_objs = []
	for page in real_pages:
		all_objs += page.objs
	for wo in all_objs:
		if wo.is_root():
			if wo.status == 200:
				new_page_c = MyPage()
				new_page_c.root = wo
				new_page_c.add_obj(wo)
				page_cands.append(new_page_c)
			else:
				junk_html_objs.append(wo)
		else:
			found = False
			for pc in page_cands:
				if pc.own_this(wo, 'loose'):
					pc.add_obj(wo)
					found = True
					break
			if found is False:
				junk_nonhtml_objs.append(wo)
	return real_pages, page_cands

def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from HAR file')
	parser.add_argument('-f', '--input', type=str, help= 'a single HAR file as input')
	parser.add_argument('-d', '--dir', type=str, help= 'file folder containing HAR file(s). All the HAR files under this folder will be processed.')
	parser.add_argument('-b', '--balance', type=int, default = 0, help= '0(default) or 1, if balance the number of positive and negtive instances.')

	args = parser.parse_args()
	input_file = args.input
	input_folder = args.dir
	balanced = args.balance
	if input_file is None and input_folder is None:
		parser.print_help()
		exit(1)
	else:
		all_real_pages = []
		all_page_cands = []
		if input_file is not None:
			(rps, pcs) = process_har_file(input_file)
			all_real_pages += rps
			all_page_cands += pcs
		elif input_folder is not None:
			# Processing all HAR file under the folder
			for root, dirs, files in os.walk(input_folder):
				for file in files:
					suffix = file.rsplit('.', 1)[1]
					if suffix != 'har':
						continue
					(rps, pcs) = process_har_file(os.path.join(root, file))
					all_real_pages += rps
					all_page_cands += pcs
		# dump LIBSVM instances
		all_instances = []
		instances_pos = []
		instances_neg = []
		all_real_roots = [i.root for i in all_real_pages if i.root != None]
		for pc in all_page_cands:
			if pc.root in all_real_roots:
				label = 1
			else:
				label = -1
			pf = PageFeature(pc)
			instance = pf.assemble_instance(label)
			if label == 1:
				instances_pos.append(instance)
			else:
				instances_neg.append(instance)
		if balanced == 1:
			all_instances += instances_pos
			random.shuffle(instances_neg)
			instances_neg = instances_neg[:len(instances_pos)]
			all_instances += instances_neg
		else:
			all_instances += instances_pos
			all_instances += instances_neg
		print 'positive#: ', len(instances_pos)
		print 'negtive#: ', len(instances_neg)
		ofile = open('features_har', 'wb')
		ofile.write(''.join(all_instances))
		ofile.close()
		# dump urls
		# all_real_urls = [i.url for i in all_real_roots]
		# ofile = open('urls', 'wb')
		# ofile.write('\n'.join(all_real_urls))
		# ofile.close()


if __name__ == '__main__':
	main()
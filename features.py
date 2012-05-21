#coding: utf-8
# This program extracts features as the input of LIBSVM from HAR file 
# Author: chenxm

import json, re, math, argparse, os

class WebObject(object):
	""" Defining the class for web objects extracted from HAR file.
	"""
	def __init__(self, har_ent):
		""" har_ent: web entry of HAR file
		"""
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

	def is_root(self):
		""" Check if the object is a HTML file. 
		"""
		ct_re = re.compile(r'\w+\/(\w+)')
		ct_mch = ct_re.match(self.type)
		sub_t = None
		if ct_mch:
			sub_t = ct_mch.group(1)
		if sub_t in ['html', 'xhtml', 'xxhtml', 'shtml']:
			return True
		else:
			return False

class PageCand(object):
	""" Page candidate insists of a HTML file as root and following referring non-HTML objects.
	"""
	def __init__(self, root_obj):
		""" root_obj: a HTML object of :WebObject
		"""
		self.root = root_obj
		self.urls = [root_obj.url]
		self.objs = [root_obj]

	def own_this(self, obj):
		""" Checking if the obj belongs to this page.
		obj: an object of :WebObject
		"""
		for url in self.urls:
			if obj.referrer == url:
				return True
		return False

	def add_obj(self, obj):
		""" Add new object to this page
		obj: an object of :WebObject
		"""
		self.urls.append(obj.url)
		self.objs.append(obj)

class Feature(object):
	""" Extracting features of page candidates.
	"""
	def __init__(self, pc):
		""" pc: object of :PageCand
		"""
		self.owner = pc
		self.f_dict = {}
		self.__server_info()
		self.__page_info()
		self.__object_info()

	def assemble_instance(self, label):
		""" Assembling instances for learning and testing which would be used by LIBSVM.
		One instance looks like:
			<lable> <index1>:<value1> <index2>:<value2> ...
		label: the label of this instance which can be any real number
		"""
		attributes = [
			'size_of_all_objects',
			'downloading_time_of_all_objects',
			'size_of_html_candidate',
			'url_level_of_html_candidate',
			'downloading_time_of_html_candidate',
			'number_of_objects',
			'object_size_median',
			'object_size_average',
			'number_of_javascript_objects',
			'size_of_javascript_objects_median',
			'size_of_javascript_objects_average',
			'number_of_image_objects',
			'size_of_image_objects_median',
			'size_of_image_objects_average',
			'number_of_flash_objects',
			'size_of_flash_objects_median',
			'size_of_flash_objects_average',
			'number_of_css_objects',
			'size_of_css_objects_median',
			'size_of_css_objects_average',
			'number_of_unidentified_objects',
			'size_of_unidentified_objects_median',
			'size_of_unidentified_objects_average',
		]
		instance = str(label)
		for att in attributes:
			instance += ' %d:%d' % (attributes.index(att)+1, self.f_dict[att])
		features_f = open('features.txt', 'wb')
		features_f.write('\n'.join(attributes))
		features_f.close()
		return instance

	def __server_info(self):
		""" Extracting featrues about server
		"""
		self.f_dict['number_of_servers_contacted'] = 0
		self.f_dict['number_of_origins_contacted'] = 0
		self.f_dict['fraction_of_nonorigin_servers_contacted'] = .0

	def __page_info(self):
		""" Extracting features about all objects
		"""
		all_objects = self.owner.objs
		tot_size = 0
		for obj in all_objects:
			tot_size += obj.size
		self.f_dict['size_of_all_objects'] = tot_size
		self.f_dict['downloading_time_of_all_objects'] = 0
		html_candidate = self.owner.root
		self.f_dict['size_of_html_candidate'] = 0
		self.f_dict['url_level_of_html_candidate'] = 0
		self.f_dict['downloading_time_of_html_candidate'] = html_candidate.receiving_time

	def __object_info(self):
		""" Extracting features about every kind of objects
		"""
		all_objects = self.owner.objs
		subtype_re = {
			r'.*jpeg|jpg|gif|png|bmp|ppm|pgm|pbm|pnm|tiff|exif|cgm|svg.*': 'image',
			r'.*flash|flv.*': 'flash',
			r'.*css.*': 'css',
			r'.*javascript|js.*': 'js',
		}
		type_obj_dict = {
		'others': [],
		'image': [],
		'flash': [],
		'css': [],
		'js': [],
		}

		def which_type(obj):
			for regex in subtype_re.keys():
				if re.match(re.compile(regex, re.I), obj.type):
					return subtype_re[regex]
				else:
					continue
			return 'others'

		# Classifying objects
		for obj in all_objects:
			subtype = which_type(obj)
			type_obj_dict[subtype].append(obj)

		(number, median_size, average_size) = self.__pro_subtype_objects(all_objects)
		self.f_dict['number_of_objects'] = number
		self.f_dict['object_size_median'] = median_size
		self.f_dict['object_size_average'] = average_size

		(number, median_size, average_size) = self.__pro_subtype_objects(type_obj_dict['others'])
		self.f_dict['number_of_unidentified_objects'] = number
		self.f_dict['size_of_unidentified_objects_median'] = median_size
		self.f_dict['size_of_unidentified_objects_average'] = average_size

		(number, median_size, average_size) = self.__pro_subtype_objects(type_obj_dict['image'])
		self.f_dict['number_of_image_objects'] = number
		self.f_dict['size_of_image_objects_median'] = median_size
		self.f_dict['size_of_image_objects_average'] = average_size

		(number, median_size, average_size) = self.__pro_subtype_objects(type_obj_dict['flash'])
		self.f_dict['number_of_flash_objects'] = number
		self.f_dict['size_of_flash_objects_median'] = median_size
		self.f_dict['size_of_flash_objects_average'] = average_size

		(number, median_size, average_size) = self.__pro_subtype_objects(type_obj_dict['css'])
		self.f_dict['number_of_css_objects'] = number
		self.f_dict['size_of_css_objects_median'] = median_size
		self.f_dict['size_of_css_objects_average'] = average_size

		(number, median_size, average_size) = self.__pro_subtype_objects(type_obj_dict['js'])
		self.f_dict['number_of_javascript_objects'] = number
		self.f_dict['size_of_javascript_objects_median'] = median_size
		self.f_dict['size_of_javascript_objects_average'] = average_size

	def __pro_subtype_objects(self, obj_list):
		""" Processing objects of subtype.
		obj_list: the list of :WebObject instances
		Return: a tuple of (number_of_objects, median_size, average_size)
		"""
		def median(numbers):
			n = len(numbers)
			copy = numbers[:]
			copy.sort()
			if n & 1:
				return copy[n/2]
			else:
				return (copy[n/2-1] + copy[n/2]) / 2

		def average(numbers):
			return math.fsum(numbers)/len(numbers)

		numbers = [i.size for i in obj_list if i.size != -1]
		if len(numbers) == 0:
			count = 0
			med = 0
			ave = 0
		else:
			count = len(numbers)
			med = median(numbers)
			ave = average(numbers)
		return (count, med, ave)

def process_har_file(input, output):
	""" Processing HAR file
	input: the relative or absolute filename of HAR file
	output: the output filename
	Return: instances as input of LIBSVM
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

	for pc in page_cands:
		if page_cands.index(pc) == 0:
			label = 1
		else:
			label = 0
		pf = Feature(pc)
		instance = pf.assemble_instance(label)
		print instance
		ofile = open(output, 'ab')
		ofile.write(instance+'\n')
		ofile.close()

def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from HAR file')
	parser.add_argument('-f', '--input', type=str, help= 'a single HAR file as input')
	parser.add_argument('-b', '--batch', type=str, help= 'file folder containing HAR file(s). \
						All the HAR files under this folder will be processed.')
	parser.add_argument('-o', '--output', type=str, default = 'svmdata', help= 'output file containing LIBSVM instances')

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
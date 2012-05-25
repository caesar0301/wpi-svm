# -*- coding: utf-8 -*-
# This module constains some commom classes about web object and page
# Author: chenxm 2012-05-22
import re, math

class WebObject(object):
	""" Defining the class for web objects.
	"""
	def __init__(self):
		self.start_time = None
		self.total_time = None
		self.receiving_time = None
		self.url = None
		self.status = None
		self.size = None
		self.type = None
		self.referrer = None
		self.re_url = None
		self.user_agent = None
		self.user_ip = None

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
			
class WebPage(object):
	""" Page candidate insists of a HTML file as root and following referring non-HTML objects.
	"""
	def __init__(self):
		""" root_obj: a HTML object of :WebObject
		"""
		self.root = None
		self.urls = []
		self.objs = []

	def own_this(self, obj, rule = 'strict'):
		""" Checking if the obj belongs to this page.
		obj: an object of :WebObject
		"""
		if rule == 'strict':
			for url in self.urls:
				if obj.referrer and  obj.referrer == url:
					return True
		elif rule == 'loose':	
			for url in self.urls:
				pure_url = re.compile(r'^\w+://([^#\?]+)#?\??')
				if obj.referrer and url:
					match_ref = pure_url.match(obj.referrer)
					match_url = pure_url.match(url)
					if match_ref and match_url:
						if match_ref.group(1) == match_url.group(1):
							return True
		return False

	def add_obj(self, obj):
		""" Add new object to this page
		obj: an object of :WebObject
		"""
		self.urls.append(obj.url)
		self.objs.append(obj)
		
class PageFeature(object):
	""" Extracting features of web page.
	"""
	def __init__(self, pc):
		""" pc: object of :WebPage
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
			'downloading_time_of_object_median',
			'downloading_time_of_object_average',
			'number_of_javascript_objects',
			'size_of_javascript_objects_median',
			'size_of_javascript_objects_average',
			'downloading_time_of_javascript_median',
			'downloading_time_of_javascript_average',
			'number_of_image_objects',
			'size_of_image_objects_median',
			'size_of_image_objects_average',
			'downloading_time_of_image_median',
			'downloading_time_of_image_average',
			'number_of_flash_objects',
			'size_of_flash_objects_median',
			'size_of_flash_objects_average',
			'downloading_time_of_flash_median',
			'downloading_time_of_flash_average',
			'number_of_css_objects',
			'size_of_css_objects_median',
			'size_of_css_objects_average',
			'downloading_time_of_css_median',
			'downloading_time_of_css_average',
			'number_of_unidentified_objects',
			'size_of_unidentified_objects_median',
			'size_of_unidentified_objects_average',
			'downloading_time_of_unidentified_median',
			'downloading_time_of_unidentified_average',
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
		self.f_dict['size_of_html_candidate'] = html_candidate.size != None and html_candidate.size or 0
		self.f_dict['url_level_of_html_candidate'] = 0
		self.f_dict['downloading_time_of_html_candidate'] = html_candidate.receiving_time != None and html_candidate.receiving_time or 0

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
			if isinstance(obj.type, str):
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

		(number, median_size, average_size, median_time, average_time) = self.__pro_subtype_objects(all_objects)
		self.f_dict['number_of_objects'] = number
		self.f_dict['object_size_median'] = median_size
		self.f_dict['object_size_average'] = average_size
		self.f_dict['downloading_time_of_object_median'] = median_time
		self.f_dict['downloading_time_of_object_average'] = average_time

		(number, median_size, average_size, median_time, average_time) = self.__pro_subtype_objects(type_obj_dict['others'])
		self.f_dict['number_of_unidentified_objects'] = number
		self.f_dict['size_of_unidentified_objects_median'] = median_size
		self.f_dict['size_of_unidentified_objects_average'] = average_size
		self.f_dict['downloading_time_of_unidentified_median'] = median_time
		self.f_dict['downloading_time_of_unidentified_average'] = average_time

		(number, median_size, average_size, median_time, average_time) = self.__pro_subtype_objects(type_obj_dict['image'])
		self.f_dict['number_of_image_objects'] = number
		self.f_dict['size_of_image_objects_median'] = median_size
		self.f_dict['size_of_image_objects_average'] = average_size
		self.f_dict['downloading_time_of_image_median'] = median_time
		self.f_dict['downloading_time_of_image_average'] = average_time

		(number, median_size, average_size, median_time, average_time) = self.__pro_subtype_objects(type_obj_dict['flash'])
		self.f_dict['number_of_flash_objects'] = number
		self.f_dict['size_of_flash_objects_median'] = median_size
		self.f_dict['size_of_flash_objects_average'] = average_size
		self.f_dict['downloading_time_of_flash_median'] = median_time
		self.f_dict['downloading_time_of_flash_average'] = average_time

		(number, median_size, average_size, median_time, average_time) = self.__pro_subtype_objects(type_obj_dict['css'])
		self.f_dict['number_of_css_objects'] = number
		self.f_dict['size_of_css_objects_median'] = median_size
		self.f_dict['size_of_css_objects_average'] = average_size
		self.f_dict['downloading_time_of_css_median'] = median_time
		self.f_dict['downloading_time_of_css_average'] = average_time

		(number, median_size, average_size, median_time, average_time) = self.__pro_subtype_objects(type_obj_dict['js'])
		self.f_dict['number_of_javascript_objects'] = number
		self.f_dict['size_of_javascript_objects_median'] = median_size
		self.f_dict['size_of_javascript_objects_average'] = average_size
		self.f_dict['downloading_time_of_javascript_median'] = median_time
		self.f_dict['downloading_time_of_javascript_average'] = average_time

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

		count = len(obj_list)
		sizes = [i.size for i in obj_list if i.size >= 0]
		timings = [i.receiving_time for i in obj_list if i.receiving_time >= 0]
		if len(sizes) == 0:
			med_size = 0
			ave_size = 0
		else:
			med_size = median(sizes)
			ave_size = average(sizes)
		if len(timings) == 0:
			med_time = 0
			ave_time = 0
		else:
			med_time = median(timings)
			ave_time = average(timings)
		return (count, med_size, ave_size, med_time, ave_time)
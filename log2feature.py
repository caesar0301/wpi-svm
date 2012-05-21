# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import json, re
import hashlib

def read_log(log_file):
	""" Reading log file and return flows in JSON format.
	log_file: name of log file of web-logger
	Return: list of flow records
	"""
	all_lines = open(log_file, 'rb').readlines()
	flows = []
	for line in all_lines:
		uni_line = unicode(line, 'utf-8', 'replace')
		flow = json.loads(uni_line)
		flows.append(flow)
	flows.sort(lambda x,y: cmp(x['time_syn'], y['time_syn']), None, False)
	return flows
	
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
			
def parse_field(dict, key):
	try:
		value = dict[key]
	except KeyError:
		value = None
	return value
	
def remove_url_prefix(url):
	""" Remove the prefix of url
	url: input url string
	"""
	url_regex = re.compile(r"^(\w+:?//)?(.*)$", re.IGNORECASE)
	url_match = url_regex.match(url)
	if url_match:
		url = url_match.group(2)
	return url
	
def parse_content_type(data):
	""" Parsing the content type from mimetype string of HTTP header
	data: mimetype string of HTTP header
	"""
	mediatype_re = re.compile(r'^([\w\-+.]+)/([\w\-+.]+)(?:\s*;?)((?:\s*[^;]+\s*;?)*)\s*$')
	match = mediatype_re.match(data)
	content_type = None
	if match:
		type = match.group(1).lower()
		subtype = match.group(2).lower()
		content_type = "%s/%s" % (type, subtype)
	return content_type
	

def process_flow(flow):
	""" Processing a flow record of log file, which is represented by one line.
	Return: list of web objects
	"""	
	wo_list = []	# Web objects will be returned
	source_ip = flow['saddr']
	http_pairs = flow['http_pairs']
	for http_pair in http_pairs:
		new_wo = WebObject()
		request = parse_field(http_pair, 'request')
		response = parse_field(http_pair, 'response')
		if request is not None:
			req_fbt = parse_field(request, 'time_first_byte')
			host = parse_field(request, 'host')
			uri = parse_field(request, 'uri')
			user_agent = parse_field(request, 'user_agent')
			referrer = parse_field(request, 'referer')
		if response is not None:
			rsp_status = parse_field(response, 'status')
			rsp_fbt = parse_field(response, 'time_first_byte')
			rsp_lbt = parse_field(response, 'time_last_byte')
			content_length = parse_field(response, 'content_length')
			mime_type = parse_field(response, 'content_type')
			re_location = parse_field(response, 'location')
		# Set values to members of new web object
		new_wo.user_ip = source_ip	
		if req_fbt is not None:
			new_wo.start_time = req_fbt
		if None not in [req_fbt, rsp_lbt] and cmp(req_fbt, rsp_lbt) <= 0:
			new_wo.total_time = rsp_lbt - req_fbt
		if None not in [rsp_fbt, rsp_lbt] and cmp(rsp_fbt, rsp_lbt) <= 0:
			new_wo.receiving_time = rsp_lbt - rsp_fbt
		if None not in [host, uri]:
			new_wo.url = remove_url_prefix(host+uri)
		if rsp_status is not None:
			new_wo.status = rsp_status
		if content_length is not None:
			new_wo.size = content_length
		if mime_type is not None:
			new_wo.type = parse_content_type(mime_type)
		if re_location is not None:
			new_wo.re_url = remove_url_prefix(re_location)
		if user_agent is not None:
			new_wo.user_agent = user_agent
		if referrer is not None:
			new_wo.referrer = remove_url_prefix(referrer)
		wo_list.append(new_wo)
	return wo_list


def main():
	log_file = '/Users/chenxm/Rhett/github/dataset/groundtruth/china_top_50/weblog.txt'
	flows = read_log(log_file)
	for flow in flows:
		wos = process_flow(flow)
		for wo in wos:
			print wo.url

if __name__ == "__main__":
	main()
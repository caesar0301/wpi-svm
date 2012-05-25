# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import json, re
import hashlib
import argparse

from myweb import WebObject, WebPage, PageFeature

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
	flows.sort(lambda x,y: cmp(x['synt'], y['synt']), None, False)
	return flows
			
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
	source_ip = flow['sa']
	http_pairs = flow['pairs']
	for http_pair in http_pairs:
		new_wo = WebObject()
		request = parse_field(http_pair, 'req')
		response = parse_field(http_pair, 'res')
		if request is not None:
			req_fbt = parse_field(request, 'fbt')
			host = parse_field(request, 'host')
			uri = parse_field(request, 'uri')
			user_agent = parse_field(request, 'ua')
			referrer = parse_field(request, 'ref')
		else:
			req_fbt = None
			host = None
			uri = None
			user_agent = None
			referrer = None
		if response is not None:
			rsp_status = parse_field(response, 'sta')
			rsp_fbt = parse_field(response, 'fbt')
			rsp_lbt = parse_field(response, 'lbt')
			content_length = parse_field(response, 'conlen')
			mime_type = parse_field(response, 'contyp')
			re_location = parse_field(response, 'loc')
		else:
			rsp_status = None
			rsp_fbt = None
			rsp_lbt = None
			content_length = None
			mime_type = None
			re_location = None
		# Set values to members of new web object
		new_wo.user_ip = source_ip	
		new_wo.start_time = req_fbt != None and req_fbt or None
		if None not in [req_fbt, rsp_lbt] and cmp(req_fbt, rsp_lbt) <= 0:
			new_wo.total_time = rsp_lbt - req_fbt
		if None not in [rsp_fbt, rsp_lbt] and cmp(rsp_fbt, rsp_lbt) <= 0:
			new_wo.receiving_time = rsp_lbt - rsp_fbt
		if None not in [host, uri]:
			new_wo.url = remove_url_prefix(host+uri)
		new_wo.status = rsp_status != None and rsp_status or None
		new_wo.size = content_length != None and int(content_length) or 0
		new_wo.type = mime_type != None and parse_content_type(mime_type) or None
		new_wo.re_url = re_location != None and remove_url_prefix(re_location) or None
		new_wo.user_agent = user_agent != None and user_agent or None
		new_wo.referrer = referrer != None and remove_url_prefix(referrer) or None
		wo_list.append(new_wo)
	return wo_list
	
def process_web_object(res, wo):
	""" Processing each web object
	res: the dict resotring results. res has structure like {ip: {ua: [pages]}}
	wo: web object
	"""
	if wo.type and wo.is_root():
		if wo.status in [200]:
			new_page = WebPage()
			new_page.root = wo
			new_page.add_obj(wo)
			if wo.user_ip in res:
				ua_pages_dict = res[wo.user_ip]
				if wo.user_agent in ua_pages_dict:
					ua_pages_dict[wo.user_agent].append(new_page)
				else:
					ua_pages_dict[wo.user_agent] = [new_page]
			else:
				res[wo.user_ip] = {wo.user_agent: [new_page]}
	else:
		if wo.user_ip in res:
			ua_pages_dict = res[wo.user_ip]
			if wo.user_agent in ua_pages_dict:
				for page in ua_pages_dict[wo.user_agent][::-1]:
					if page.own_this(wo):
						page.add_obj(wo)
					
def process_log(logfile, gt_urls, outfile):
	""" Processing log file
	logfile: name of logfile
	gt_urls: name of file storing valid urls to deduce the labels of instances
	outfile: name of output file
	"""
	valid_urls = open(gt_urls, 'rb').read().split('\n')
	flows = read_log(logfile)
	all_wos = []
	for flow in flows:
		wos = process_flow(flow)
		all_wos += wos
	all_wos.sort(lambda x,y: cmp(x, y), lambda x: x.start_time, False)
	ip_data_d = {}
	for wo in all_wos:
		process_web_object(ip_data_d, wo)
	
	def gen_label(urls, url):
		for i in urls:
			if remove_url_prefix(url) == remove_url_prefix(i):
				return 1
		return 0
	
	all_instances = []
	cnt = 0
	for ua_data_d in ip_data_d.values():
		for page_arr in ua_data_d.values():
			for page in page_arr:
				pf = PageFeature(page)
				label = gen_label(valid_urls, page.root.url)
				if label == 1:
					cnt += 1
				instance = pf.assemble_instance(label)
				all_instances.append(instance)
	ofile = open(outfile, 'ab')
	ofile.write('\n'.join(all_instances))
	ofile.close()
	print cnt
	
def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from log of web-logger')
	parser.add_argument('logfile', type=str, help= 'log file of web-logger: \
						git@github.com:caesar0301/web-logger.git')
	parser.add_argument('gtfile', type=str, help= 'Groudtruth urls used to deduce labels of instances.')
	parser.add_argument('-o', '--output', type=str, default = 'log.f', help= 'output file containing LIBSVM instances')

	args = parser.parse_args()
	process_log(args.logfile, args.gtfile, args.output)

if __name__ == "__main__":
	main()
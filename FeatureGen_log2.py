# coding: utf-8
# This program extarcts features as input of LIBSVM from log file of web-logger:
# 	git@github.com:caesar0301/web-logger.git
# Author: chenxm, 2012-05-21
import json, re
import hashlib
import argparse

from myweb import WebObject, WebPage, PageFeature
import logbasic as basic

def read_log(log_file):
	""" Reading log file and return flows in JSON format.
	log_file: name of log file of web-logger
	Return: list of flow records
	"""
	all_rr = basic.read(log_file)
	return all_rr
			
def get_value(dict, key):
	try:
		value = dict[key]
		if value == 'N/A':
			raise KeyError
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
	

def process_rrp(rrlist):
	""" Processing
	Return: list of web objects
	"""	
	wo_list = []	# Web objects will be returned
	for rr in rrlist:
		new_wo = WebObject()
		# Set values to members of new web object
		new_wo.user_ip = get_value(rr, 'source_ip')
		new_wo.start_time = get_value(rr, 'time')
		dns = get_value(rr, 'dns')
		connect = get_value(rr, 'connect')
		send = get_value(rr, 'send')
		wait = get_value(rr, 'wait')
		receive = get_value(rr, 'receive')
		timings = [dns, connect, send, wait, receive]
		timings = [int(i) for i in timings if i != None]
		new_wo.total_time = sum(timings)
		rt = get_value(rr, 'receive')
		new_wo.receiving_time = rt!=None and int(rt) or 0
		new_wo.url = get_value(rr, 'url')
		new_wo.status = int(get_value(rr, 'response_status'))
		rbz = get_value(rr, 'response_body_size')
		new_wo.size = rbz != None and int(rbz) or 0
		new_wo.type = get_value(rr, 'response_content_type')
		new_wo.re_url = get_value(rr, 'redirect_url')
		new_wo.user_agent = get_value(rr, 'user_agent_id')
		new_wo.referrer = get_value(rr, 'referrer')
		wo_list.append(new_wo)
	return wo_list
	
def process_web_object(wo, res):
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
					if page.own_this(wo, 'l'):
						page.add_obj(wo)
						return None
				return wo
					
def process_log(logfile, gt_urls):
	""" Processing log file
	logfile: name of logfile
	gt_urls: name of file storing valid urls to deduce the labels of instances
	outfile: name of output file
	"""
	valid_urls = open(gt_urls, 'rb').read().split('\n')
	print 'reading log...'
	all_rr = read_log(logfile)
	print 'processing rrp...'
	all_wos = process_rrp(all_rr)
	all_wos.sort(lambda x,y: cmp(x, y), lambda x: x.start_time, False)
	print 'processing web objects...'
	ip_data_d = {}
	jks = []
	print 'all objs:', len(all_wos)
	for wo in all_wos:
		jwo = process_web_object(wo, ip_data_d)
		if jwo is not None:
			jks.append(jwo)
	print 'junks:', len(jks)
	
	def gen_label(urls, url):
		for i in urls:
			if remove_url_prefix(url) == remove_url_prefix(i):
				return 1
		return -1
	
	all_instances = []
	instances_pos = []
	instances_neg = []
	pos_cnt = 0
	neg_cnt = 0
	for ua_data_d in ip_data_d.values():
		for page_arr in ua_data_d.values():
			for page in page_arr:
				# log page cands' urls
				##################################
				urlfile = open(logfile+'.candurl', 'ab')
				urlfile.write(page.root.url+'\n')
				urlfile.close()
				##################################
				pf = PageFeature(page)
				label = gen_label(valid_urls, page.root.url)
				# Rewrite label
				if len(page.objs) <= 1:
					label = -1

				instance = pf.assemble_instance(label)
				if label == 1:
					instances_pos.append(instance)
				else:
					instances_neg.append(instance)
	all_instances = instances_pos + instances_neg
	print 'positive#: ', len(instances_pos)
	print 'negtive#: ', len(instances_neg)
	##################################
	ofile = open(logfile+'.instance', 'wb')
	ofile.write(''.join(all_instances))
	ofile.close()
	##################################
	print 'writing instances to "%s"' % logfile+'.instance'
	print 'writing candidate URLs to "%s"' % logfile+'.candurl'
	
def main():
	parser = argparse.ArgumentParser(description='Extracting features as the input of LIBSVM from log. Output = logfile.instance')
	parser.add_argument('logfile', type=str, help= 'log file containing the request/response pair')
	parser.add_argument('urlfile', type=str, help= 'Groudtruth urls used to deduce labels of instances.')

	args = parser.parse_args()
	process_log(args.logfile, args.urlfile)

if __name__ == "__main__":
	main()
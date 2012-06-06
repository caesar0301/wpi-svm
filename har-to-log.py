#-*- coding: utf-8 -*-
# Author: chenxm
import json, argparse, os
import re, uuid
import logbasic as basic

def parse_time(timestr):
	timere = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3,6})\+')
	match = timere.match(timestr)
	if match:
		return match.group(1)
	else:
		return None	
		
def parse_field(dict, key):
	""" Simple dict wrapper
	dict: name of dict object
	key: name of key
	Return: dict[key] or None
	"""
	invalid_values = ['', -1]
	try:
		value = dict[key]
		if value in invalid_values:
			raise KeyError
	except KeyError:
		value = None
	return value
	
class RRPair(object):
	def __init__(self):
		self.sdt = None
		self.dns = None
		self.connect = None
		self.send = None
		self.wait = None
		self.receive = None
		self.flowid = None
		self.uaid = None
		self.srcip = None
		self.srcport = None
		self.destip = None
		self.destport = None
		self.request_version = None
		self.response_version = None
		self.method = None
		self.status = None
		self.url = None
		self.referrer = None
		self.re_url = None
		self.request_header_size = None
		self.request_body_size = None
		self.response_header_size = None
		self.response_body_size = None
		self.type = None
	
def process_har(readfile, ua_id):
	log = json.load(open(readfile, 'rb'))['log']
	entries = log['entries']
	objects = []
	for har_ent in entries:
		rr = RRPair()
		# Parsing
		rr.sdt = parse_time(har_ent['startedDateTime'])
		rr.flowid = None
		rr.srcip = '219.228.106.207'
		rr.srcport = None
		rr.destip = parse_field(har_ent, 'serverIPAddress')
		rr.destport = parse_field(har_ent, 'connection')
		request = parse_field(har_ent, 'request')
		response = parse_field(har_ent, 'response')
		timings = parse_field(har_ent, 'timings')
		if request is not None:
			rr.url = parse_field(request, 'url')
			rr.method = parse_field(request, 'method')
			rr.request_version = parse_field(request, 'httpVersion')
			rr.request_header_size = parse_field(request, 'headersSize')
			rr.request_body_size = parse_field(request, 'bodySize')
			headers = parse_field(request, 'headers')
			if headers is not None:
				for field in headers:
					if field['name'] == 'Referer':
						rr.referrer = field['value']
					if field['name'] == 'Host':
						rr.host = field['value']
					if field['name'] == 'User-Agent':
						ua = field['value']
		if response is not None:
			rr.status = parse_field(response, 'status')
			rr.response_version = parse_field(response, 'httpVersion')
			rr.response_header_size = parse_field(response, 'headersSize')
			rr.response_body_size = parse_field(response, 'bodySize')
			rr.re_url = parse_field(response, 'redirectURL')
			content = parse_field(response, 'content')
			if content is not None:
				rr.type = parse_field(content, 'mimeType')
		if timings is not None:
			rr.dns = parse_field(timings, 'dns')
			rr.connect = parse_field(timings, 'connect')
			rr.send = parse_field(timings, 'send')
			rr.wait = parse_field(timings, 'wait')
			rr.receive = parse_field(timings, 'receive')
		# user agent id
		if ua not in ua_id:
			ua_id[ua] = uuid.uuid4().hex
			rr.uaid = ua_id[ua]
		else:
			rr.uaid = ua_id[ua]
		objects.append(rr)
	return objects
		
			
def main():
	parser = argparse.ArgumentParser(description='Dumping har files to web log format')
	parser.add_argument('-f', '--input', type=str, help= 'a single HAR file as input')
	parser.add_argument('-d', '--dir', type=str, help= 'file folder containing HAR file(s). All the HAR files under this folder will be processed.')
	args = parser.parse_args()
	input_file = args.input
	input_folder = args.dir
	if input_file is None and input_folder is None:
		parser.print_help()
		exit(1)
	else:
		all_objects = []
		ua_id_d = {}
		print 'processing hars...'
		if input_file is not None:
			all_objects += process_har(input_file, ua_id_d)
		elif input_folder is not None:
			# Processing all HAR file under the folder
			for root, dirs, files in os.walk(input_folder):
				for file in files:
					suffix = file.rsplit('.', 1)[1]
					if suffix != 'har':
						continue
					all_objects += process_har(os.path.join(root, file), ua_id_d)
		print 'sorting...'
		all_objects.sort(lambda x,y: cmp(x.sdt, y.sdt), None, False)
		
		if input_file is not None:
			output_prefix = input_file
		elif input_folder is not None:
			output_prefix = os.path.split(os.path.dirname(input_folder))[1]
		# Dumping useragents
		outfile = open(output_prefix+'.uaid', 'ab')
		for item in ua_id_d.items():
			outfile.write(item[1]+'\t\t'+item[0])
		outfile.close()
		# Dumping rrpair
		for rr in all_objects:
			# Write
			basic.write(output_prefix+'.log', 
				time = rr.sdt,
				dns = rr.dns,
				connect = rr.connect,
				send = rr.send,
				wait = rr.wait,
				receive = rr.receive,
				flow_id = rr.flowid,
				user_agent_id = rr.uaid,
				source_ip = rr.srcip,
				source_port = rr.srcport,
				dest_ip = rr.destip,
				dest_port = rr.destport,
				request_version = rr.request_version,
				response_version = rr.response_version,
				request_method = rr.method,
				response_status = rr.status,
				url = rr.url,
				referrer = rr.referrer,
				redirect_url = rr.re_url,
				request_header_size = rr.request_header_size,
				request_body_size = rr.request_body_size,
				response_header_size = rr.response_header_size,
				response_body_size = rr.response_body_size,
				response_content_type = rr.type)
		print 'writing useragent to file "%s"' % output_prefix+'.uaid'
		print 'writing log to file "%s"' % output_prefix+'.log'

			
if __name__ == '__main__':
	main()
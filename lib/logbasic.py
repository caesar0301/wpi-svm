#coding: utf-8
import codecs, re, datetime
import uuid

from myWeb import WebObject
import tree.node as mod_node

attribute_names = [
	'time', 
	'dns', 'connect', 'send', 'wait', 'receive',
	'flow_id',
	'user_agent_id',
	'source_ip',
	'source_port',
	'dest_ip',
	'dest_port',
	'request_version',
	'response_version',
	'request_method',
	'response_status',
	'request_header_size',
	'request_body_size',
	'response_header_size',
	'response_body_size',
	'response_content_type',
	'url',
	'referrer',
	'redirect_url',
]


def mylogger(str):
	#print 'warnning: %s' % str
	pass
	
def check_arg(arg):
	if arg is None:
		mylogger('%s is absent.' % arg)

def parse_field(dict, key):
	""" Simple dict wrapper
	dict: name of dict object
	key: name of key
	Return: dict[key] or None
	"""
	try:
		value = dict[key]
		if value == 'N/A':
			raise KeyError
	except KeyError:
		value = None
	return value

def time_str2dt(ts):
	""" Convert the time string (yyyy-mm-ddThh:mm:ss.mmm) 
		to value in python datatime format.
	"""
	time_re = re.compile(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d{3,6})')
	match = time_re.match(ts)
	if match:
		year = int(match.group(1))
		month = int(match.group(2))
		day = int(match.group(3))
		hour = int(match.group(4))
		minute = int(match.group(5))
		seconds = int(match.group(6))
		microseconds = int(match.group(7))*pow(10, 6-len(match.group(7)))
		dt = datetime.datetime(year, month, day, hour, minute, seconds, microseconds)
		return dt
	else:
		return None

def time_dt2str(dt):
	""" Convert the time value in python datatime format
		to string like (yyyy-mm-ddThh:mm:ss.mmm).
	"""
	return "%4d-%02d-%02dT%02d:%02d:%02d.%06d" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
		

class NodeFromLog(mod_node.Node, WebObject):
	def __init__(self, logline):		
		line = logline.strip(' \n\r\t')
		values = line.split('\t\t')
		if len(attribute_names) != len(values):
			print 'Data format error: line#%d' % index
			exit(-1)
		rr = dict(zip(attribute_names, values))

		nid = str(uuid.uuid1())
		mod_node.Node.__init__(self, 'nd_'+nid, nid)
		WebObject.__init__(self)

		self.user_ip = parse_field(rr, 'source_ip')
		sdt = parse_field(rr, 'time')
		if sdt is not None:
			self.start_time = time_str2dt(sdt)

		dns = parse_field(rr, 'dns')
		connect = parse_field(rr, 'connect')
		send = parse_field(rr, 'send')
		wait = parse_field(rr, 'wait')
		receive = parse_field(rr, 'receive')
		timings = [dns, connect, send, wait, receive]
		timings = [int(i) for i in timings if i != None]
		self.total_time = datetime.timedelta(milliseconds = sum(timings))

		rt = parse_field(rr, 'receive')
		self.receiving_time = rt!=None and int(rt) or 0
		self.url = parse_field(rr, 'url')
		self.status = int(parse_field(rr, 'response_status'))
		rbz = parse_field(rr, 'response_body_size')
		self.size = (rbz != None and int(rbz) or 0)
		self.type = parse_field(rr, 'response_content_type')
		self.re_url = parse_field(rr, 'redirect_url')
		self.user_agent = parse_field(rr, 'user_agent_id')
		self.referrer = parse_field(rr, 'referrer')

def read(filename):
	datafile = codecs.open(filename, 'rb', 'utf-8')
	lines = []
	for i in datafile.readlines():
		line = i.strip(' \n\r\t')
		if line != '' and line[0] != '#':
			# Valid line
			values = line.split('\t\t')
			if len(attribute_names) != len(values):
				print 'Data format error: %s' % line
				exit(-1)
			lines.append(line)
	return lines
	
def write(filename, **args):
	""" args: dict, keys of which are the same with 'args_names' below.
	The order is arbitrary.
	"""
	for key in attribute_names:
		value = parse_field(args, key)
		if value is None:
			mylogger('%s is absent.' % key)
			args[key] = 'N/A'	# lost signature = N/A
		else:
			if isinstance(value, int):
				args[key] = str(value)
	args_valus = [args[i] for i in attribute_names]
	content = '\t\t'.join(args_valus)	# seperator = \t\t
	if filename is not None:
		fo = codecs.open(filename, 'ab', 'utf-8')
		fo.write(content+'\n')
		fo.close()
	else:
		print content
	
def Test():
	import datetime
	timeval = datetime.datetime.now()
	print time_dt2str(timeval)
	print time_str2dt(time_dt2str(timeval))
	pass
	
if __name__ == '__main__':
	Test()
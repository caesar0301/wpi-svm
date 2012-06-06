#coding: utf-8
import codecs

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
	except KeyError:
		value = None
	return value

__attribute_names = [
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
		
def read(filename):
	datafile = open(filename, 'rb')
	all_lines = datafile.readlines()
	ret = []
	for i in all_lines:
		index = all_lines.index(i)
		line = i.strip(' \n\r\t')
		if line != '' and line[0] != '#':
			# Valid line
			values = line.split('\t\t')
			if len(__attribute_names) != len(values):
				print 'Data format error: line#%d' % index
				exit(-1)
			ret.append(dict(zip(__attribute_names, values)))
	return ret
	
def write(filename, **args):
	""" args: dict, keys of which are the same with 'args_names' below.
	The order is arbitrary.
	"""
	for key in __attribute_names:
		value = parse_field(args, key)
		if value is None:
			mylogger('%s is absent.' % key)
			args[key] = 'N/A'	# lost signature = N/A
		else:
			if isinstance(value, int):
				args[key] = str(value)
	args_valus = [args[i] for i in __attribute_names]
	content = '\t\t'.join(args_valus)	# seperator = \t\t
	if filename is not None:
		fo = codecs.open(filename, 'ab', 'utf-8')
		fo.write(content+'\n')
		fo.close()
	else:
		print content
	
def Test():
	#write('test', user_agent_id = 2)
	print read('test')[1:3]
	pass
	
if __name__ == '__main__':
	Test()
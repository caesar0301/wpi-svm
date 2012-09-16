# -*- coding: utf-8 -*-
import re

class Logger(object):
	def __init__(self, file_path):
		self.log_h = open(file_path, 'wb')

	def log(self, line):
		print line
		self.log_h.write(line+'\n')

	def close(self):
		self.log_h.close()

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
	
def search_url(turl, url_list):
	trul2 = remove_url_prefix(turl)
	for url in url_list:
		if trul2 == remove_url_prefix(url):
			return True
	return False


def cmp_url(u1, u2, mode = 'strict'):
	if mode == 'strict':
		if remove_url_prefix(u1) == remove_url_prefix(u2):
			return True
		return False
	elif mode == 'loose':
		urlre = re.compile(r'^(\w+://)?([^#\?]+)#?\??')
		match_u1 = urlre.match(u1)
		match_u2 = urlre.match(u2)
		if match_u1 and match_u2:
			if match_u1.group(2) == match_u2.group(2):
				return True
			return False
		else:
			return cmp_url(u1, u2, 'strict')

						
def main():
	pass
	
if __name__ == '__main__':
	main()
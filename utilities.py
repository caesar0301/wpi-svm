# -*- coding: utf-8 -*-
import re

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
							
def main():
	pass
	
if __name__ == '__main__':
	main()
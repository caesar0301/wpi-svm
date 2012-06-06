# coding: utf-8
# Check the url match
# Author: chenxm, 2012-05-31
import argparse, re

def remove_url_prefix(url):
	""" Remove the prefix of url
	url: input url string
	"""
	url_regex = re.compile(r"^(\w+:?//)?(.*)$", re.IGNORECASE)
	url_match = url_regex.match(url)
	if url_match:
		url = url_match.group(2)
	return url

def check_url(url, allurls):
	for i in allurls:
		if remove_url_prefix(url) == remove_url_prefix(i):
			return True
	return False
		
def main():
	parser = argparse.ArgumentParser(description='Check if the source urls exist.')
	parser.add_argument('sourceurls', type=str, help= 'source urls to be checked')
	parser.add_argument('allurls', type=str, help= 'all urls, the groudtruth')

	args = parser.parse_args()
	surls = open(args.sourceurls, 'rb').read().split('\n')
	aurls = open(args.allurls, 'rb').read().split('\n')
	
	hit_cnt = 0
	hit_urls = []
	for url in surls:
		if check_url(url, aurls):
			hit_urls.append(url)
			hit_cnt += 1
	print 'hit: %d' % hit_cnt
	print 'miss: %d' % (len(surls) - hit_cnt)
	print 'accuracy: %f' % (float(hit_cnt)/len(surls))
	ofile = open(args.sourceurls+'.hit', 'wb')
	ofile.write('\n'.join(hit_urls))
	ofile.close()

if __name__ == "__main__":
	main()
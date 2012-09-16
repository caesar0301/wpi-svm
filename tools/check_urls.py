# coding: utf-8
# Check the url match
# Author: chenxm, 2012-05-31
from __future__ import division
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
	parser.add_argument('input', type=str, help= 'source urls to be checked')
	parser.add_argument('groundtruth', type=str, help= 'all urls, the groudtruth')

	args = parser.parse_args()
	srcfile = args.input
	gtfile = args.groundtruth
	surls = set([i.strip('\n').split('\t')[0] for i in open(srcfile, 'rb').readlines()])
	aurls = set([i.strip('\n').split('\t')[0] for i in open(gtfile, 'rb').readlines()])
	
	hit_cnt = 0
	hit_urls = []
	tp = 0
	fp = 0
	tn = None
	fn = 0
	for url in aurls:
		if check_url(url, surls):
			hit_urls.append(url)
			tp += 1
		else:
			fn += 1
	fp = len(surls) - tp
	
	precision = tp/(tp + fp)
	recall = tp/(tp + fn)
	if precision + recall != 0:
		fscore = 2 * precision * recall/(precision + recall)
	else:
		fscore = -1
	sensitivity = tp / (tp + fn)
	print 'TP: %d, FP: %d, TN: None, FN: %d' % (tp, fp, fn)
	print 'Precision: %.3f' % precision
	print 'Recall: %.3f' % recall
	print 'F-Score: %.3f' % fscore
	print 'Sensitivity: %.3f' % sensitivity

if __name__ == "__main__":
	main()

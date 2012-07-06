# coding: utf-8
# Check the url match
# Author: chenxm, 2012-06-03
from __future__ import division
import argparse
		
def main():
	parser = argparse.ArgumentParser(description='Caculate the accuracy of prediction. The origin and predict files both record the label as the first character in each line.')
	parser.add_argument('origin', type=str, help= 'file containing right labels.')
	parser.add_argument('predict', type=str, help= 'file containing predict labels.')
	args = parser.parse_args()
	originfile = args.origin
	predictfile = args.predict
	origin_labels = [line.split()[0] for line in open(originfile, 'rb')]
	predict_labels = [line.split()[0] for line in open(predictfile, 'rb')]
	# Simple check
	if len(origin_labels) != len(predict_labels):
		print "Two set of instances don't match."
		exit(-1)
	pos = 0
	neg = 0
	for i in origin_labels:
		if i == '1':
			pos+=1
		else:
			neg+=1
	print 'Positive instances: %d' % pos
	print 'Negative instances: %d' % neg
	pairs = zip(origin_labels, predict_labels)
	tp = 0
	fp = 0
	tn = 0
	fn = 0
	for pair in pairs:
		if pair == ('1', '1'):
			tp += 1
		elif pair == ('1', '-1'):
			fn += 1
		elif pair == ('-1', '1'):
			fp += 1
		elif pair == ('-1', '-1'):
			tn += 1

	try:	
		precision = tp/(tp + fp)
	except ZeroDivisionError:
		precision = -1.0

	try:
		recall = tp/(tp + fn)
	except ZeroDivisionError:
		recall = -1.0

	try:
		if precision == -1.0: precision = 0
		if recall == -1.0: recall = 0
		fscore = 2 * precision * recall/(precision + recall)
	except ZeroDivisionError:
		fscore = -1.0

	try:
		sensitivity = tp / (tp + fn)
	except ZeroDivisionError:
		sensitivity = -1.0

	try:
		specificity = tn / (tn + fp)
	except ZeroDivisionError:
		specificity = -1.0

	if sensitivity == -1.0: sensitivity = 0
	if specificity == -1.0: specificity = 0
	bac = (sensitivity + specificity)/2	
		
	print 'TP: %d, FP: %d, TN: %d, FN: %d' % (tp, fp, tn, fn)
	print 'Precision: %.3f' % precision
	print 'Recall: %.3f' % recall
	print 'F-Score: %.3f' % fscore
	print 'Sensitivity: %.3f' % sensitivity
	print 'Specificity: %.3f' % specificity
	print 'BAC: %.3f' % bac


if __name__ == "__main__":
	main()

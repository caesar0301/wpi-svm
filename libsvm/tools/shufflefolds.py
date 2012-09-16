#!/usr/bin/env python
import argparse, sys, os
from subprocess import *
import random

parser = argparse.ArgumentParser(description='Shuffle data for cross validation.')
parser.add_argument('-v', '--vfold', default=5, type=int, help= 'folder count')
parser.add_argument('datafile', type=str, help= 'data file')

args = parser.parse_args()
vfold = args.vfold
datafile = args.datafile

###### chenck data format
checkdata_py = ''

is_win32 = (sys.platform == 'win32')
if not is_win32:
	checkdata_py = "./checkdata.py"
else:
	checkdata_py = r".\checkdata.py"
assert os.path.exists(checkdata_py), "checkdata.py not found"

cmd = 'python {0} {1}'.format(checkdata_py, datafile)
print 'checking data format...'
Popen(cmd, shell = True, stdout = PIPE).communicate()


class Label:
	def __init__(self, label, index):
		self.label = label
		self.index = index

# get labels
i = 0
labels = []
ld = {}
alllines = [line for line in open(datafile, 'r')]
for line in alllines:
	lv = float((line.split())[0])
	label = Label(lv, i)
	if lv not in ld:
		ld[lv] = [label]
	else:
		ld[lv].append(label)
	i = i + 1

# shuffle
for key in ld.keys():
	random.shuffle(ld[key])
	if len(ld[key]) < vfold:
		assert False, 'instance number not match fold count.'

fd = {}
for i in range(0, vfold):
	print i
	if i not in fd:
		fd[i] = []
	for key in ld.keys():
		l = len(ld[key])
		print l ,i*l/vfold, (i+1)*l/vfold
		for j in range(i*l/vfold, (i+1)*l/vfold):
			fd[i].append(ld[key][j])


for i in range(0, vfold):
	foldtrain = 'fold{0}-train.libsvm'.format(i+1)
	foldtest =  'fold{0}-test.libsvm'.format(i+1)
	filetrain = open(foldtrain, 'wb')
	filetest = open(foldtest, 'wb')
	print foldtrain, foldtest

	trainlist = []
	testlist = []
	for key in fd:
		if key == i:
			testlist += fd[key]
		else:
			trainlist += fd[key]
	print len(trainlist), len(testlist)

	# write
	random.shuffle(trainlist)
	random.shuffle(testlist)
	for i in trainlist:
		filetrain.write(alllines[i.index])
	for j in testlist:
		filetest.write(alllines[j.index])

	filetrain.close()
	filetest.close()




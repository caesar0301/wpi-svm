#!/usr/bin/env python

import argparse, sys, os
from subprocess import *

###### parse arguments
parser = argparse.ArgumentParser(description='Get the data with selected features.')
parser.add_argument('-flist', type=str, help= 'the seriel nubmers of features, e.g., "1,2,4-6" -> "1,2,4,5,6"')
parser.add_argument('allfeatures', type=str, help= 'original instance file')
parser.add_argument('subfeatures', type=str, help= 'instance file with selected features')
args = parser.parse_args()
fnum = args.flist
ori = args.allfeatures
sel = args.subfeatures
sn_arr = fnum.split(',')
sns = set()
for sn in sn_arr:
    if '-' in sn:
        [start, end] = sn.split('-')
        start = int(start)
        end = int(end)
        if start > end:
            raise ValueError
        else:
            for i in range(start, end+1):
                sns.add(i)
    else:
        sns.add(int(sn))
print 'features:',list(sns)

###### chenck data format
checkdata_py = ''

is_win32 = (sys.platform == 'win32')
if not is_win32:
	checkdata_py = "./checkdata.py"
else:
	checkdata_py = r".\checkdata.py"
assert os.path.exists(checkdata_py), "checkdata.py not found"

cmd = 'python {0} {1}'.format(checkdata_py, ori)
print 'checking data format...'
Popen(cmd, shell = True, stdout = PIPE).communicate()

###### process selected features
new_lines = []
for old_line in open(ori, 'rb'):
    nodes = old_line.split()
    for node in nodes[1:]:
        (index, value) = node.split(':')
        index = int(index)
        value = float(value)
        if index not in sns:
            nodes.remove(node)

    # format new line
    for i in range(len(nodes)):
        if i == 0:
            continue
        (index, value) = nodes[i].split(':')
        index = i
        nodes[i] = '{0}:{1}'.format(index, value)

    new_line = ' '.join(nodes)
    new_lines.append(new_line)

###### write to file as selected features
ofile = open(sel, 'wb')
content = '\n'.join(new_lines)
ofile.write(content)
ofile.flush()
ofile.close()

# finish

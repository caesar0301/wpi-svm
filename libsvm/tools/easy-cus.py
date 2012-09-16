#!/usr/bin/env python

import sys
import os
from subprocess import *

###### parse arguments
argv = sys.argv
usage = 'Usage: {0} [additional parameters for svm-train] training_file testing_file'.format(argv[0])

if len(argv) < 3:
        print usage
	raise SystemExit

# svm, grid, and gnuplot executable files

is_win32 = (sys.platform == 'win32')
if not is_win32:
	svmscale_exe = "../svm-scale"
	svmtrain_exe = "../svm-train"
	svmpredict_exe = "../svm-predict"
	grid_py = "./grid.py"
	gnuplot_exe = "/usr/local/bin/gnuplot"
	statistics_py = "./statistics.py"
else:
    # example for windows
	svmscale_exe = r"..\\windows\\svm-scale.exe"
	svmtrain_exe = r"..\\windows\\svm-train.exe"
	svmpredict_exe = r"..\\windows\\svm-predict.exe"
	gnuplot_exe = r"C:\Program Files (x86)\gnuplot\bin\pgnuplot.exe"
	grid_py = r".\\grid.py"
	statistics_py = r".\\statistics.py"

assert os.path.exists(svmscale_exe),"svm-scale executable not found"
assert os.path.exists(svmtrain_exe),"svm-train executable not found"
assert os.path.exists(svmpredict_exe),"svm-predict executable not found"
assert os.path.exists(gnuplot_exe),"gnuplot executable not found"
assert os.path.exists(grid_py),"grid.py not found"
assert os.path.exists(statistics_py),"statistics.py not found"

train_pathname = argv[-2]
assert os.path.exists(train_pathname),"training file not found"
train_file = os.path.split(train_pathname)[1]
scaled_file = train_file + ".scale"
model_file = train_file + ".model"
range_file = train_file + ".range"

test_pathname = argv[-1]
assert os.path.exists(test_pathname),"testing file not found"
test_file = os.path.split(test_pathname)[1]
scaled_test_file = test_file + ".scale"
predict_test_file = test_file + ".predict"
	
train_options = []
i = 1
while i < len(argv) - 2:
	train_options.append(argv[i])
	i = i+1
train_options_string = " ".join(train_options)
        
###### train
cmd = '{0} -s "{1}" "{2}" > "{3}"'.format(svmscale_exe, range_file, train_pathname, scaled_file)
print('Scaling training data...')
Popen(cmd, shell = True, stdout = PIPE).communicate()	

# cmd = 'python {0} -svmtrain "{1}" -gnuplot "{2}" {3} "{4}"'.format(grid_py, svmtrain_exe, gnuplot_exe, train_options_string, scaled_file)
# print('Cross validation...')
# f = Popen(cmd, shell = True, stdout = PIPE).stdout

# line = ''
# while True:
# 	last_line = line
# 	line = f.readline()
# 	if not line: break
# c,g,rate = map(float,last_line.split())

# print('Best c={0}, g={1} CV rate={2}'.format(c,g,rate))

c= 32
g= 0.125

cmd = '{0} -c {1} -g {2} {3} "{4}" "{5}"'.format(svmtrain_exe,c,g, train_options_string, scaled_file, model_file)
print('Training...')
Popen(cmd, shell = True, stdout = PIPE).communicate()

print('Output model: {0}'.format(model_file))

###### predict
cmd = '{0} -r "{1}" "{2}" > "{3}"'.format(svmscale_exe, range_file, test_pathname, scaled_test_file)
print('Scaling testing data...')
Popen(cmd, shell = True, stdout = PIPE).communicate()	

cmd = '{0} "{1}" "{2}" "{3}"'.format(svmpredict_exe, scaled_test_file, model_file, predict_test_file)
print('Testing...')
Popen(cmd, shell = True).communicate()	

print('Output prediction: {0}'.format(predict_test_file))


cmd = 'python {0} {1} {2}'.format(statistics_py, scaled_test_file, predict_test_file)
f = Popen(cmd, shell = True, stdout = PIPE).stdout
for line in f:
	print line.strip('\r \n')

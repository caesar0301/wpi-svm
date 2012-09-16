# select-feature.py --> easy-cus.py --> logging
import os, uuid, sys, re, math
from subprocess import *
import shutil
import argparse

###### global params

train_options = '-t 2'  # RBF kernel
subset_count = 1402     # 20% of data set
test_counts = [6993, 6986, 6965, 6939, 6879, 6660, 6309, 5608, 3505]
dup_count = 20      # running ** times
FBFs = '73,49,32,55,118,19,16,44,26,121'

# parse auguments
parser = argparse.ArgumentParser(description='Do the batch work: \
1. select feature set;\
2. partition the data by 80:20 randomly;\
3. 80 as training, 20 as testing;\
4. repeat 2 and 3 by 20 times;\
5. Calculate mean accuracy;\
6. goto 1, continue when no more features.')
parser.add_argument('datafile', type=str, help= 'File containing all instances')
args = parser.parse_args()
datafile_path = args.datafile
assert os.path.exists(datafile_path),"data file not found"

datafile_name = os.path.split(datafile_path)[1]

# clear logfile
log_file = sys.argv[0].split('.')[0]+'.log'
log_h = open(log_file, 'wb')

def log(l):
    global log_h
    print l 
    log_h.write(l+'\n')

def mean(numbers):
    return sum(numbers)/len(numbers)

def median(numbers):
    n = len(numbers)
    copy = numbers[:]
    copy.sort()
    if n & 1:
        return copy[n/2]
    else:
        return (copy[n/2-1] + copy[n/2]) / 2

def variance(numbers):
    ave = mean(numbers)
    return len(numbers) > 1 and math.fsum([math.pow(i-ave, 2) for i in numbers]) / (len(numbers)-1) or 0.0


###### prepare feature sets
feature_sets = []
FBFs = FBFs.split(',')
for i in range(0, len(FBFs), 1):
    feature_sets.append(FBFs[0:i+1])
print "# Feature Set:", len(feature_sets)

###### start
for count in test_counts:
    for feature_set in feature_sets[-1:]:
        ###### select features
        subfeatures = '{0}.sub'.format(datafile_name)
        log('#features:%d' % len(feature_set))

        cmd = 'python subFeatureSet.py -flist {0} {1} {2}'.format(','.join(feature_set), datafile_path, subfeatures)
        #print(cmd)
        Popen(cmd, shell=True, stdout=PIPE).communicate()

        i = dup_count
        mul_accs = []
        mul_pre = []
        mul_rec = []
        mul_fscore = []
        while i > 0:
            i -= 1      # to count number
            ###### partition data
            train_file = '{0}.train'.format(subfeatures)
            test_file = '{0}.test'.format(subfeatures)

            cmd = 'python subset.py {0} {1} {2} {3}'.format(subfeatures, count, test_file, train_file)
            #print(cmd)
            Popen(cmd, shell=True, stdout=PIPE).communicate()

            ###### easy processing
            cmd = 'python easy-cus.py {0} {1} {2}'.format(train_options, train_file, test_file)
            #print(cmd)
            f = Popen(cmd, shell=True, stdout=PIPE).stdout
            accuracy = None
            precision = None
            recall = None
            fscore = None
            for line in f:
                acc_re = re.compile(r'Accuracy = (\d+(\.)?\d+)')
                acc_match = acc_re.match(line)
                if acc_match:
                    accuracy = float(acc_match.group(1))
                    continue
                pre_re = re.compile(r'^Precision: ?(\d+\.?\d+)')
                pre_match = pre_re.match(line)
                if pre_match:
                    precision = float(pre_match.group(1))
                    continue

                recall_re = re.compile(r'^Recall: ?(\d+\.?\d+)')
                recall_match = recall_re.match(line)
                if recall_match:
                    recall = float(recall_match.group(1))
                    continue

                fscore_re = re.compile(r'^F-Score: ?(\d+\.?\d+)')
                fscore_match = fscore_re.match(line)
                if fscore_match:
                    fscore = float(fscore_match.group(1))
                    continue
            if accuracy is not None:
                mul_accs.append(accuracy)
            else:
                assert -1

            if precision is not None:
                mul_pre.append(precision)
            if recall is not None:
                mul_rec.append(recall)
            if fscore is not None:
                mul_fscore.append(fscore)


        # record mean accuracy
        print("minimum, median, maximum, mean, variance")
        log("#"*10)
        log('{0} {1} {2} {3} {4}'.format(min(mul_accs), median(mul_accs),\
            max(mul_accs), mean(mul_accs), variance(mul_accs)))
        # log('{0} {1} {2} {3} {4}'.format(min(mul_pre), median(mul_pre),\
        #     max(mul_pre), mean(mul_pre), variance(mul_pre)))
        # log('{0} {1} {2} {3} {4}'.format(min(mul_rec), median(mul_rec),\
        #     max(mul_rec), mean(mul_rec), variance(mul_rec)))
        # log('{0} {1} {2} {3} {4}'.format(min(mul_fscore), median(mul_fscore),\
        #     max(mul_fscore), mean(mul_fscore), variance(mul_fscore)))

log_h.close()
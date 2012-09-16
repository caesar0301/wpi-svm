# select-feature.py --> easy-cus.py --> logging
import os, uuid, sys
from subprocess import *
import shutil
import argparse

###### global params

train_optioins = {
    # '-t 0': 'linear',
    # '-t 1 -d 2':'polynomial d2',
    # '-t 1 -d 3':'polynomial d3',
    '-t 2':     'Guassian',
    # '-t 3':     'sigmoid',
    }

# sys path
is_win32 = (sys.platform == 'win32')
if not is_win32:
    fscore_py = "./cal_fscore.py"
else:
    fscore_py = ".\\cal_fscore.py"

# parse auguments
parser = argparse.ArgumentParser(description='Do the batch work: select-feature.py --> easy.py --> statistics.py')
parser.add_argument('trainfile', type=str, help= 'File containing training instances')
parser.add_argument('testfile', type=str, help= 'File containing test instances')

args = parser.parse_args()
train_file_path = args.trainfile
train_file = os.path.split(train_file_path)[1]
#fscore_file = train_file+".fscore"
selected_train_file = train_file+'.tmp'
model_file = selected_train_file +'.model'
grid_image = selected_train_file+'.scale.png'

##### caculate fscore
# cmd = 'python {0} "{1}" '.format(fscore_py, train_file_path)
# print(cmd)
# Popen(cmd, shell=True, stdout=PIPE).communicate()

# make sure model file can be opened correctly.
#if not os.path.exists(model_file):
 #   open(model_file, 'wb').write('')

test_file_path = args.testfile
selected_test_file = os.path.split(test_file_path)[1]+'.tmp'
scaled_test_file = selected_test_file+'.scale'
predict_test_file = selected_test_file+'.predict'

assert os.path.exists(train_file_path),"train file not found"
assert os.path.exists(test_file_path),"test file not found"
#assert os.path.exists(fscore_file),"fscore file not found"

# clear logfile
log_file = sys.argv[0].split('.')[0]+'.log'
log_h = open(log_file, 'wb')

def testID():
    test_id = uuid.uuid4().hex
    return test_id

def log(line):
    global log_h
    print line 
    log_h.write(line+'\n')


def get_feature_order():
    global fscore_file
    features_by_fscore = []
    for line in open(fscore_file):
        features_by_fscore.append(line.split(":")[0])
    return features_by_fscore

###### prepare feature sets

feature_sets = []
#FBFs = get_feature_order()
FBFs = '49,73,32,25,118,44,112,67,72,43,50,17,69,55,68,56,71,86,19,20,97,70,92,61,38,63,62,93,45,66,51,22,33,96,57,26,54,116,27,91,42,39,121,60,114,18,1,87,58,120,24,111,113,4,34,117,59,48,90,95,104,115,3,105,119,65,108,46,109,98,102,36,37,85,107,47,99,79,31,103,94,23,21,110,82,80,35,83,89,84,101,81,30,2,74,10,16,75,78,77,88,52,53,106,40,64,76,29,41,100,28,14'
FBFs = FBFs.split(',')
for i in range(0, len(FBFs), 1):
    feature_sets.append(FBFs[0:i+1])

print len(feature_sets)

for feature_set in feature_sets:
    for option in train_optioins.keys():
        log('############################')
        test_id = testID()
        log(test_id)
        log('kernel:%s' % train_optioins[option])
        
        ###### select features
        feature_set_str = ','.join(feature_set)
        log('features:%s' % feature_set_str)
        cmd = 'python select-feature.py -flist {0} {1} {2}'.format(feature_set_str, train_file_path, selected_train_file)
        print(cmd)
        Popen(cmd, shell=True, stdout=PIPE).communicate()

        cmd = 'python select-feature.py -flist {0} {1} {2}'.format(feature_set_str, test_file_path, selected_test_file)
        print(cmd)
        Popen(cmd, shell=True, stdout=PIPE).communicate()

        ###### easy processing
        cmd = 'python easy-cus.py {0} {1} {2}'.format(option, selected_train_file, selected_test_file)
        print(cmd)
        f = Popen(cmd, shell=True, stdout=PIPE).stdout
        for line in f:
            log(line.strip(' \r\n'))
            
        ###### logging
        if os.path.exists(model_file):
            log('model:')
            model_h = open(model_file, 'rb')
            for line in model_h.readlines():
                line = line.strip(' \r\n')
                if line != 'SV':
                    log(line)
                else:
                    break
            model_h.close()
            log('\r\n')

        try:
            if os.path.exists(grid_image):
                shutil.copyfile(grid_image, "images/%s.png" % str(test_id))
        except:
            pass

log_h.close()
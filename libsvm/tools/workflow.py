# select-feature.py --> easy-cus.py --> logging
import os, uuid, sys
from subprocess import *
import shutil
import argparse

###### global params

train_optioins = [
    '-t 0 -v 5',         # linear
    '-t 1 -d 2 -v 5',    # quadratic polynomial
    '-t 1 -d 3 -v 5',    # cubic polynomial
    '-t 2 -v 5',         # Guassian
    '-t 3 -v 5',         # sigmoid
    ]

parser = argparse.ArgumentParser(description='Do the batch work: select-feature.py --> easy.py --> statistics.py')
parser.add_argument('trainfile', type=str, help= 'File containing training instances')
parser.add_argument('testfile', type=str, help= 'File containing test instances')

args = parser.parse_args()
train_file_path = args.trainfile
fscore_file = train_file_path+".fscore"
selected_train_file = os.path.split(train_file_path)[1]+'.tmp'
model_file = selected_train_file +'.model'
grid_image = selected_train_file+'.scale.png'

test_file_path = args.testfile
selected_test_file = os.path.split(test_file_path)[1]+'.tmp'
scaled_test_file = selected_test_file+'.scale'
predict_test_file = selected_test_file+'.predict'

assert os.path.exists(train_file_path),"train file not found"
assert os.path.exists(test_file_path),"test file not found"
assert os.path.exists(fscore_file),"fscore file not found"

log_file = sys.argv[0].split('.')[0]+'.log'
if os.path.exists(log_file):
    os.remove(log_file)

is_win32 = (sys.platform == 'win32')
if not is_win32:
	statistics_py = "../../statistics.py"
else:
	statistics_py = r"..\\..\\statistics.py"

def testID():
    test_id = uuid.uuid4().hex
    return test_id

def log(line):
    global log_file

    print line
    log_h = open(log_file, 'ab')
    log_h.write(line+'\n')
    log_h.flush()
    log_h.close()

def get_feature_order():
    global fscore_file
    features_by_fscore = []
    for line in open(fscore_file):
        features_by_fscore.append(line.split(":")[0])
    return features_by_fscore

###### prepare feature sets

features = []
FBFs = get_feature_order()
for i in range(len(FBFs)):
    features.append(FBFs[0:i+1])

#features = [['1-123']]

###### workflow

for feature_set in features[0:1]:
    for option in train_optioins[0:1]:
        log('############################')
        test_id = testID()
        log(test_id)
        
        ###### select features
        feature_set_str = ','.join(feature_set)
        cmd = 'select-feature.py -flist {0} "{1}" "{2}"'.format(feature_set_str, train_file_path, selected_train_file)
        log(cmd)
        Popen(cmd, shell=True, stdout=PIPE).communicate()

        cmd = 'select-feature.py -flist {0} "{1}" "{2}"'.format(feature_set_str, test_file_path, selected_test_file)
        log(cmd)
        Popen(cmd, shell=True, stdout=PIPE).communicate()

        ###### easy processing
        cmd = 'easy-cus.py {0} "{1}" "{2}"'.format(option, selected_train_file, selected_test_file)
        log(cmd)
        f = Popen(cmd, shell=True, stdout=PIPE).stdout
        for line in f:
            log(line.strip(' \r\n'))
            
        ###### statistics
        cmd = '{0} "{1}" "{2}"'.format(statistics_py,scaled_test_file,predict_test_file)
        log(cmd)
        f = Popen(cmd, shell = True, stdout = PIPE).stdout
        for line in f:
            log(line.strip(' \r\n'))

        ###### logging
        if os.path.exists(model_file):
            log('model:')
            for line in open(model_file, 'rb'):
                line = line.strip(' \r\n')
                if line != 'SV':
                    log(line)
                else:
                    break
            log('\r\n')

        try:
            if os.path.exists(grid_image):
                shutil.copyfile(grid_image, "images/%s.png" % str(test_id))
        except:
            pass
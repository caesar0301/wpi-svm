# select-feature.py --> easy-cus.py --> logging
import os, uuid, sys
from subprocess import *
import shutil

train_file_path = "E:\\Cloud\\SkyDrive\\data\\icnc2013\\auto.instance"
selected_train_file = os.path.split(train_file_path)[1]+'.tmp'
model_file = selected_train_file + ".model"
grid_image = selected_train_file+'.scale.png'

test_file_path = "E:\\Cloud\\SkyDrive\\data\\icnc2013\\manual.log.instance"
selected_test_file = os.path.split(test_file_path)[1]+'.tmp'
scaled_test_file = selected_test_file+'.scale'
predict_test_file = selected_test_file+'.predict'

fscore_file = "E:\\Cloud\\SkyDrive\\data\\icnc2013\\auto.instance.fscore"
features_by_fscore = []

is_win32 = (sys.platform == 'win32')
if not is_win32:
	statistics_py = "../../statistics.py"
else:
	statistics_py = r"..\\..\\statistics.py"

def testID():
    test_id = uuid.uuid4().hex
    return test_id

def log(line):
    print line
    log_file = open('workflowlog.txt', 'ab')
    log_file.write(line+'\n')
    log_file.flush()
    log_file.close()

def get_feature_order():
    global fscore_file, features_by_fscore
    for line in open(fscore_file):
        features_by_fscore.append(line.split(":")[0])

get_feature_order()

features = []
for i in range(len(features_by_fscore)):
    features.append(features_by_fscore[0:i+1])

train_optioins = [
    '-t 0',         # linear
    '-t 1 -d 2',    # quadratic polynomial
    '-t 1 -d 3',    # cubic polynomial
    '-t 2',         # Guassian
    '-t 3',         # sigmoid
    ]

def main():
    global features, train_optioins

    if os.path.exists('workflowlog.txt'):
        os.remove('workflowlog.txt')

    for feature_set in features:
        for option in train_optioins:
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
                os.remove(model_file)

            try:
                if os.path.exists(grid_image):
                    shutil.copyfile(grid_image, "images/%s.png" % str(test_id))
                    os.remove(grid_image)
            except:
                pass
            

if __name__ == '__main__':
    main()
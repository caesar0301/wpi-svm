#!/usr/bin/env python

import argparse, sys, os
from subprocess import *

###### parse arguments
parser = argparse.ArgumentParser(description='Convert libsvm data format to data-ResourceDescription format used by FCBF-java.')
parser.add_argument('origin', type=str, help= 'file in libsvm format')
args = parser.parse_args()
orifile = args.origin

class Instance(object):
    def __init__(self, libsvm_line):
        libsvm_line = libsvm_line.rstrip('\r \n')
        elems = libsvm_line.split(' ')
        self.class_label = elems[0]
        self.atts = []
        i = 0
        for elem in elems[1:]:
            i += 1
            [key, value] = elem.split(':')
            if int(key) == i:
                self.atts.append(value)
            else:
                while int(key) != i:
                    i += 1
                    self.atts.append(None)
                self.atts.append(value)
             
###### process libsvm data
all_inst = []
for line in open(orifile, 'rb').readlines()[:1]:
    inst = Instance(line)
    all_inst.append(inst)


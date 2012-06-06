# coding: utf-8
# Check the url match
# Author: chenxm, 2012-06-03
import argparse
		
def main():
	parser = argparse.ArgumentParser(description='Deviding all instances into the positie(1) and the negtive(-1) which are stored in different files.')
	parser.add_argument('infile', type=str, help= 'file containing instances.')
	args = parser.parse_args()
	infile = args.infile
	fo = open(infile, 'rb')
	all_ins = fo.readlines()
	pos_ins = []
	neg_ins = []
	for ins in all_ins:
		ins = ins.rstrip('\n')
		if ins[0] == '1':
			pos_ins.append(ins)
		else:
			neg_ins.append(ins)
	open(infile+'.pos', 'wb').write('\n'.join(pos_ins)+'\n')
	open(infile+'.neg', 'wb').write('\n'.join(neg_ins)+'\n')
	print 'writing positive instances into "%s"' % infile+'.pos'
	print 'writing negitive instances into "%s"' % infile+'.neg'

if __name__ == "__main__":
	main()
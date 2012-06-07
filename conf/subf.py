score_file = 'result.instance.fscore'
fnames = 'fnames-all'

cnt = 20
all_fields = [i.rstrip('\n') for i in open(fnames, 'rb')]

subset = []
for line in open(score_file, 'rb'):
	if cnt > 0:
		index = int(line.split(':')[0])
		subset.append(all_fields[index])
		cnt -= 1

open('fnames-subset', 'wb').write('\n'.join(subset))
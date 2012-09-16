import uuid

from myGraph import Graph
from myWeb import WebPage
import utilities as utilities

(_ROOT, _DEPTH, _WIDTH) = range(3)

def parse_pages_svm(all_nodes, valid_urls):

	print '#Total nodes:', len(all_nodes)
	print '#Validurl:', len(valid_urls)

	all_nodes.sort(lambda x,y: cmp(x,y), lambda x: x.start_time, False)

	###### construct link trees
	print 'Building referrer trees...'
	new_graph = Graph()
	for node in all_nodes:
		new_graph.add_node(node)
	trees = new_graph.all_trees()
	junk_nodes = new_graph.junk_nodes

	# little trick: treat a tree with one node 
	# as the invalid and add its nodes to 'junk_nodes'
	valid_trees = []
	for tree in trees:
		if len(tree.nodes) > 1:
			valid_trees.append(tree)
		else:
			junk_nodes += tree.nodes
	
	print('#Valid trees: {0}\n#Junk_nodes: {1}'.format(len(valid_trees), len(junk_nodes)))
	
	###### parse page cands
	print 'Constructing page-level objects...'
	all_pages = []
	for tree in valid_trees:
		###### Detect valid HTML element to be Main Object Candidates (MOCs)
		mocs = []
		for node in tree.expand_tree(mode=_WIDTH):	# must be _WIDTH
			if tree[node].is_root() and int(tree[node].status) == 200:
				mocs.append(node)

		tmp = []
		for moc in mocs[::-1]:
			bp = tree[moc].bpointer
			if bp is None:
				tmp.append(moc)
			else:
				valid_nodes = 0
				for i in tree.expand_tree(moc,filter=lambda x: x==moc or x not in tmp):
					valid_nodes += 1
				# little trick: do not cut the sub tree with only one node
				if valid_nodes>1:
					tmp.append(moc)
		mocs = tmp

		###### parse pages
		# for rootid in mocs[:]:
		# 	new_page = WebPage()
		# 	all_pages.append(new_page)
		# 	for nodeid in tree.expand_tree(rootid, filter = lambda x: x==rootid or x not in mocs):
		# 		if nodeid == rootid:
		# 			new_page.add_obj(tree[nodeid], root=True)
		# 		else:
		# 			new_page.add_obj(tree[nodeid])
		# 	if utilities.search_url(new_page.root.url, valid_urls) is True:
		# 		new_page.isvalid = True
		# 	if tree[rootid].bpointer is not None:
		# 		new_page.ref = tree[tree[rootid].bpointer]

		###### parse pages according to paper
		real = []
		for moc in mocs:
			vurl_arr = [i[0] for i in valid_urls]
			if utilities.search_url(tree[moc].url, vurl_arr) is True:
				real.append(moc)

		for rootid in mocs[:]:
			new_page = WebPage()
			all_pages.append(new_page)
			for nodeid in tree.expand_tree(rootid, filter = lambda x: x==rootid or x not in real):
				if nodeid == rootid:
					new_page.add_obj(tree[nodeid], root=True)
				else:
					new_page.add_obj(tree[nodeid])
			if new_page.root.identifier in real:
				new_page.isvalid = True
			if tree[rootid].bpointer is not None:
				new_page.ref = tree[tree[rootid].bpointer]

	all_pages.sort(lambda x,y: cmp(x,y), lambda x: x.root.start_time, False)
	print('#Pages-level objs:%d' % len(all_pages))

	return valid_trees, all_pages, junk_nodes
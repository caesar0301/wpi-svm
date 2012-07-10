import json, uuid, os

import tree.tree as mod_tree
import tree.node as mod_node

from myWeb import *
import logbasic, utilities

###### global variable
har_folder = 'E:\\Cloud\\SkyDrive\\data\\icnc2013\\manual2'


def parse_field(dict, key):
	try:
		value = dict[key]
	except KeyError:
		value = None
	return value

class MyNode(mod_node.Node, WebObject):
	"""docstring for WebNode"""
	def __init__(self):
		nid = str(uuid.uuid1())
		mod_node.Node.__init__(self, 'nd_'+nid, nid)
		WebObject.__init__(self)


class MyPage(WebPage):
	def __init__(self, id = None):
		WebPage.__init__(self)
		if id is None:
			id = uuid.uuid4().hex
		self.id = id


class NewTreeNeeded(Exception):
	pass


def process_har_file(input):
	# Open HAR file

	ifile = open(input, 'rb')
	uni_str = unicode(ifile.read(), 'utf-8', 'replace')
	har_log = json.loads(uni_str)['log']
	har_pages = har_log['pages']
	har_entries = har_log['entries']
	
	# extreact all web objects

	all_web_objects = []

	for har_ent in har_entries:
		webobject = MyNode()
		all_web_objects.append(webobject)

		webobject.pageid = har_ent['pageref']

		sdt = parse_field(har_ent, 'startedDateTime')
		if sdt is not None:
			webobject.start_time = logbasic.parse_time(sdt)

		timings = parse_field(har_ent, 'timings')

		if timings is not None:
			dns = parse_field(timings, 'dns')
			connect = parse_field(timings, 'connect')
			send = parse_field(timings, 'send')
			wait = parse_field(timings, 'wait')
			receive = parse_field(timings, 'receive')
			timings = [dns, connect, send, wait, receive]
			timings = [int(i) for i in timings if i != None]
			webobject.total_time = datetime.timedelta(milliseconds = sum(timings))

			if receive is not None:
				webobject.receiving_time = int(receive)

		request = parse_field(har_ent, 'request')
		response = parse_field(har_ent, 'response')

		if request is not None:
			webobject.url = parse_field(request, 'url')
			headers = parse_field(request, 'headers')
			if headers is not None:
				for field in headers:
					if field['name'] == 'Referer':
						webobject.referrer = field['value']

		if response is not None:
			webobject.status = parse_field(response, 'status')
			webobject.size = parse_field(response, 'bodySize')
			content = parse_field(response, 'content')
			if content is not None:
				webobject.type = parse_field(content, 'mimeType')
			headers = parse_field(response, 'headers')
			for field in headers:
				if field['name'] == 'Location':
					webobject.re_url = field['value']

	# finde trees

	trees = []

	for new_node in all_nodes:
		try:
			# Start linking
			linked_flag = False
			for tree in trees:

				pred_id = None
				if new_node.referrer:
					for item in tree.nodes[::-1]:
						node_url = utilities.remove_url_prefix(new_node.referrer)
						item_url = utilities.remove_url_prefix(item.url)
						if node_url == item_url:
							pred_id = item.identifier
							break

				if pred_id:
					# Predecessor found...
					tree.add_node(new_node, pred_id)
					linked_flag = True
					break

				# After all the trees are checked:	
			if not linked_flag:
				raise NewTreeNeeded

		except NewTreeNeeded:
			if new_node.is_root():
				print new_node.url
				new_tree = mod_tree.Tree()
				new_tree.add_node(new_node, None)
				linked_flag = True
				trees.append(new_tree)

	ifile.close()

	return trees

def link_trees(child_trees):

	child_trees.sort(lambda x,y: cmp(x, y), lambda x: x[x.root].start_time, False)	
	child_urls = [i[i.root].url for i in child_trees]

	for ct in child_trees:
		found_flag = False
		for url in child_urls[0:child_trees.index(ct)]:
			if ct[ct.root].referrer == url:
				found_flag = True
				break

		if found_flag:
			found_tree = child_trees[child_urls.index(url)]
			ct[ct.root].bpointer = found_tree[found_tree.root].identifier

	def find_root(all, one):
		for item in all:
			if one[one.root].bpointer == item[item.root].identifier:
				break
		if item[item.root].bpointer == None:
			return item[item.root].identifier
		else:
			find_root(all, item)

	res_trees = [i for i in child_trees if i[i.root].bpointer is None]

	for ct in child_trees:
		if ct[ct.root].bpointer is not None:
			rootid = find_root(child_trees, ct)

			found_flag = False
			for i in res_trees:
				if rootid == i[i.root].identifier:
					found_flag = True
					break
			if found_flag:
				i.nodes += ct.nodes
			else:
				print 'not found'

	return res_trees




def test():
	har_file = "E:\\Cloud\\SkyDrive\\data\\icnc2013\\manual\\1.har"

	trees = process_har_file(har_file)
	print trees

	for tree in trees:
		print tree[tree.root].url
		print tree[tree.root].bpointer
		tree.show()


def main():
	all_trees = []

	for root, dirs, files in os.walk(har_folder):
		for file in files[:]:
			suffix = file.rsplit('.', 1)[1]
			if suffix != 'har':
				continue
			
			all_trees += process_har_file(os.path.join(root, file))

	print len(all_trees)
	final_trees = link_trees(all_trees)
	print len(final_trees)

	print final_trees[10][final_trees[10].root].url


if __name__ == '__main__':
	main()
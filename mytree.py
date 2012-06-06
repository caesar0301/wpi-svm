# coding: utf-8
from tree import tree, node
from myweb import WebObject

class Node(node.Node, WebObject):
	"""docstring for WebNode"""
	def __init__(self, name):
		node.Node.__init__(self, name)
		WebObject.__init__(self)
	
class Tree(tree.Tree):
	"""docstring for WebTree"""
	def __init__(self):
		tree.Tree.__init__(self)
		self.ref_node_d = {}	# key is the referrer and value is the identifier of node
		self.url_node_d = {}	# key is the url and value is the identifier of node
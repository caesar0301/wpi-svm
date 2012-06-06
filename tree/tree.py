# Python 3 Tree Implementation
#
# Copyright (C) 2011, Brett Alistair Kromkamp - brettkromkamp@gmail.com
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this list
# of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# Neither the name of the copyright holder nor the names of the contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import unittest

from node import Node

# Module constants
(_ADD, _DELETE, _INSERT) = range(3)
(_ROOT, _DEPTH, _WIDTH) = range(3)

class MultipleRootError(Exception):
	pass

class Tree(object):
	def __init__(self):
		self.nodes = []		# Node object
		self.root = None	# identifier

	def get_index(self, position):
		for index, node in enumerate(self.nodes):
			if node.identifier == position:
				break
		return index

	def create_node(self, name, identifier=None, parent=None):
		"""Create a child node for the node indicated by the 'parent' parameter"""
		node = Node(name, identifier)
		self.add_node(node, parent)
		return node
		
	def add_node(self, node, parent=None):
		if parent is None:
			if self.root is not None:
				raise MultipleRootError
			else:
				self.root = node.identifier
		self.nodes.append(node)
		self.__update_fpointer(parent, node.identifier, _ADD)
		node.bpointer = parent

	def move_node(self, source, destination):
		"""
		Move a node indicated by the 'source' parameter to the parent node
		indicated by the 'dest' parameter
		"""
		pass

	def remove_node(self, identifier):
		pass

	def show(self, position = None, level=_ROOT):
		if position is None:
			position = self.root
		queue = self[position].fpointer
		if level == _ROOT:
			print("{0} [{1}]".format(self[position].name,
									 self[position].identifier))
		else:
			print("+"*level, "{0} [{1}]".format(self[position].name,
												 self[position].identifier))
		if self[position].expanded:
			level += 1
			for element in queue:
				self.show(element, level)  # recursive call

	def expand_tree(self, position = None, mode=_DEPTH, filter = None):
		# Python generator. Loosly based on an algorithm from 'Essential LISP' by
		# John R. Anderson, Albert T. Corbett, and Brian J. Reiser, page 239-241
		def real_true(pos):
			return True
		if position is None:
			position = self.root
		filterfunc = filter
		if filterfunc is None:
			filterfunc = real_true
			
		yield position
		queue = self[position].fpointer
		while queue:
			if filterfunc(queue[0]):
				yield queue[0]
				expansion = self[queue[0]].fpointer
				if mode is _DEPTH:
					queue = expansion + queue[1:]  # depth-first
				elif mode is _WIDTH:
					queue = queue[1:] + expansion  # width-first
			else:
				queue = queue[1:]
				
	def sub_tree(self, position):
		st = Tree()
		for node_n in self.expand_tree(position):
			st.root = position
			st.nodes.append(self[node_n])
		return st

	def is_branch(self, position):
		""" Return the following nodes of [position]
		"""
		return self[position].fpointer

	def __update_fpointer(self, position, identifier, mode):
		if position is None:
			return
		else:
			self[position].update_fpointer(identifier, mode)

	def __update_bpointer(self, position, identifier):
		self[position].bpointer = identifier

	def __getitem__(self, key):
		return self.nodes[self.get_index(key)]

	def __setitem__(self, key, item):
		self.nodes[self.get_index(key)] = item

	def __len__(self):
		return len(self.nodes)

	def __contains__(self, identifier):
		return [node.identifier for node in self.nodes
				if node.identifier is identifier]

#--------------------------------------------------------------------------------

# Test suite

class TestTree(unittest.TestCase):
	def setUp(self):
		pass

	def test_initialization(self):
		pass

	def tearDown(self):
		pass

#--------------------------------------------------------------------------------

# Module testing

if __name__ == "__main__":

	# Example usage
	tree = Tree()
	tree.create_node("Harry", "harry")  # root node
	tree.create_node("Jane", "jane", parent = "harry")
	tree.create_node("Bill", "bill", parent = "harry")
	tree.create_node("Joe", "joe", parent = "jane")
	tree.create_node("Diane", "diane", parent = "jane")
	tree.create_node("George", "george", parent = "diane")
	tree.create_node("Mary", "mary", parent = "diane")
	tree.create_node("Jill", "jill", parent = "george")
	tree.create_node("Carol", "carol", parent = "jill")
	tree.create_node("Grace", "grace", parent = "bill")
	tree.create_node("Mark", "mark", parent = "jane")

	print("="*80)
	tree.show('harry')
	print("="*80)
	for node in tree.expand_tree(mode=_DEPTH):
		print tree[node].name
	print("="*80)
	for node in tree.expand_tree(filter = lambda x: x != 'george', mode=_DEPTH):
		print tree[node].name
	print("="*80)
	sub_t = tree.sub_tree('diane')
	sub_t.show('diane')
	print("="*80)
	print tree.is_branch('diane')
	# Run unit tests
	unittest.main()
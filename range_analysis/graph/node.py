# encoding: UTF-8

from intervals import IntInterval, FloatInterval

class Node(object):
	"""docstring for Node"""
	def __init__(self, _type):
		super(Node, self).__init__()
		self._type = _type
		self.prev_list = [] #前驱
		self.next_list = [] #后继
		self.prev_dashed_list = [] #虚线前驱
		self.next_dashed_list = [] #虚线后继
		self.Belong = None #所属的强连通分量

class Rangenode(Node):
	"""docstring for Rangenode"""
	def __init__(self, _type, I):
		super(Rangenode, self).__init__(_type)
		self.I = I

class Ftrangenode(Node):
	"""docstring for Ftrangenode"""
	def __init__(self, _type, lval=None, rval=None, l='(', r=')'):
		super(Ftrangenode, self).__init__(_type)
		self.lval = lval
		self.rval = rval
		self.l = l # ( for open and [ for close
		self.r = r
		self.I = None
	def __str__(self):
		ret = ''
		ret += self.l
		if self.lval != None:
			ret += self.lval
		ret += ','
		if self.rval != None:
			ret += self.rval
		ret += self.r
		return ret

class Opnode(Node):
	"""docstring for Opnode"""
	def __init__(self, _type, op, phi_block=None, phi_from_block=None):
		super(Opnode, self).__init__(_type)
		self.op = op
		self.phi_block = phi_block #记录这个符号属于哪个block，将来PHI可以判断死分支
		self.phi_from_block = phi_from_block #记录PHI的来源变量和来源变量属于的块

class Varnode(Node):
	"""docstring for Varnode"""
	def __init__(self, _type, var, var_I=None):#可能存在给定的初值！
		super(Varnode, self).__init__(_type)
		self.var = var
		self.I = var_I

class Constnode(Node):
	"""docstring for Constnode"""
	def __init__(self, _type, const):
		super(Constnode, self).__init__(_type)
		self.const = const
		val = float(const)
		if val == int(val) and not const.endswith('.0'):
			self.I = IntInterval([int(val), int(val)]) #TODO: float
		else:
			self.I = FloatInterval([val, val]) #TODO: float

class Callnode(Node):
	"""docstring for Callnode"""
	def __init__(self, _type, call):
		super(Callnode, self).__init__(_type)
		self.call = call
		
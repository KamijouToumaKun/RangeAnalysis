# encoding: UTF-8

import re

import context as Context
from stmt import Stmt

class Block(object):
	"""docstring for Block"""
	def __init__(self, block_body, next_block):
		super(Block, self).__init__()
		self.branch_var = [] # 用来记录这个块里的分支变量。一个块里可能有0个、1个或更多PHI符号（比如样例t5）
		self.divide_stmts(block_body, next_block)

	def __str__(self):
		return 'stmt_list: ' + str(self.stmt_list)\
		+ '\nto_block_list: ' + str(self.to_block_list)

	def divide_stmts(self, block_body, next_block):
		# 解析每一个语句、跳转语句。太麻烦了，这里就把每个换行（而不是每个分号）作为一个语句好了。
		self.stmt_list = []
		self.condition = 'True'
		self.to_block_list = []
		self.to_block_live = [] #标记该分支是否走得通
		for _stmt in block_body.split('\n'):
			stmt = _stmt.strip()
			if len(stmt) > 0:
				if stmt.startswith('if '):
					# greedy: (D) may be inside
					self.condition = re.findall(Context.PARENTHESE_GREEDY_PATTERN, stmt)[0].strip('()')
					if self.condition.endswith('(D'): #(D))多删了一个)
						self.condition += ')'
				elif stmt.startswith('goto '):
					to_block = re.findall(Context.LABEL_PATTERN, stmt)[0]
					self.to_block_list.append(to_block)
					self.to_block_live.append(True) #标记该分支能走得通
					#if <bb 5>(<L2>), choose <bb 5>, not <L2>
				elif stmt.startswith('else'):
					pass
				elif stmt.startswith('return'):
					pass
				else: #normal assignment stmt
					self.stmt_list.append(Stmt(stmt))
		if len(self.to_block_list) == 0: # if no goto, default: to next block
			self.to_block_list.append(next_block)
			self.to_block_live.append(True) #标记该分支能走得通
		# check:
		# print self.condition, self.to_block_list
		
# encoding: UTF-8
import re

import context as Context
from var import Var
from block import Block

class Func(object):
	"""docstring for Func"""
	def __init__(self, func_decl, var_decl, func_body):
		super(Func, self).__init__()
		self.divide_params(func_decl)
		# self.var_list = {}
		self.divide_vars(var_decl)
		self.block_list = {}
		# 用于记录已经对哪些变量进行了变量名替换
		self.var_vis = []
		self.divide_blocks(func_body)

	def __str__(self):
		return 'param_list: ' + str(self.param_list)\
		+ '\nvar_list: ' + str(self.var_list)\
		+ '\nblock_list: ' + str(self.block_list)

	def divide_params(self, func_decl):
		self.param_name = [] #这个字段用来按顺序专门记录各个参数名
		self.param_list = {}
		para_decl = re.findall(Context.PARENTHESE_PATTERN, func_decl)[0].strip('()')
		for _stmt in para_decl.split(','):
			stmt = _stmt.strip()
			if len(stmt) > 0:
				tmp = stmt.split(' ')
				var_type = tmp[0]
				name = tmp[-1]
				self.param_list[name] = Var(var_type)
				self.param_name.append(name)
		# check:
		# print self.param_list

	def divide_vars(self, var_decl):
		self.var_list = {}
		for _stmt in var_decl.split('\n'):
			stmt = _stmt.strip()
			if len(stmt) > 0:
				tmp = stmt.split(' ')
				var_type = tmp[0]
				name = tmp[-1][:-1] #skip ';'
				self.var_list[name] = Var(var_type)
		# check:
		# print self.var_list

	def divide_blocks(self, func_body):
		reg = re.compile(Context.LABEL_DECL_PATTERN)
		labels = reg.findall(func_body)
		block_bodies = re.split(Context.LABEL_DECL_PATTERN, func_body)[1:]

		self.block_list['ENTRY'] = Block('', r'<bb 2>') #TODO: what if there's no bb2?
		for i in range(len(labels)):
			label = labels[i]
			block_body = block_bodies[i]
			if i < len(labels)-1:
				next_block = labels[i+1][:-1] #skip ':'
			else:
				self.return_var = block_body.split(' ')[-1]
				index = self.return_var.rindex(';')
				self.return_var = self.return_var[:index]
				# self.return_var = self.return_var.strip(';\n')
				# 但是奇怪了，光删除\n还不够，还有些其他的奇怪符号
				if len(self.return_var) == 0: #直接return，没有返回值
					self.return_var = None
				next_block = 'EXIT'
			self.block_list[label] = Block(block_body, next_block)

	def get_var_type(self, _var_name): #e.g. k_1, k_1_t, _8, _8_t
		var_name = _var_name
		index = var_name.rfind('_t')
		if index != -1:
			var_name = _var_name[:index]
		index = var_name.rfind('_f')
		if index != -1:
			var_name = _var_name[:index] #e.g. get k_1, _8
		tmp = var_name.split('_')
		if len(tmp[0]) != 0:
			var_name = tmp[0]
		for name in self.param_list:
			if var_name == name:
				return self.param_list[name].var_type
		for name in self.var_list:
			if var_name == name:
				return self.var_list[name].var_type

	def blocks_right_replace(self, start, old):
		if old in self.var_vis: #不对一个变量进行重复替换处理
			return True, True #因为do-while的情况很少，所以默认是要进行变量替换的吧，但是可能有BUG
		self.var_vis.append(old)

		self.vis = [start] #标注有哪些块遍历过了
		# 从to_block开始遍历，到start（不含start）为止
		to_block = self.block_list[start.to_block_list[0] + ':']
		if to_block != start:
			new = old + '_t'
			self.block_right_replace(to_block, old, new)
			t_flag = True
		else: #next直接回到同一个块：可以判断出这是一个简单的do-while语句
			# 更复杂的do-while语句我也判断不出来……
			# 那么不应该做变量替换；或者说原变量k_1和变量k_1_t应该合一
			t_flag = False
		to_block = self.block_list[start.to_block_list[1] + ':']
		if to_block != start:
			new = old + '_f'
			self.block_right_replace(to_block, old, new)
			f_flag = True
		else: #next直接回到同一个块：可以判断出这是一个简单的do-while语句
			# 那么不应该做变量替换；或者说原变量k_1和变量k_1_f应该合一
			f_flag = False
		return t_flag, f_flag

	def block_right_replace(self, start, old, new):
		if start in self.vis: #因为块之间存在环，有可能已经遍历过了：结束
			return
		self.vis.append(start) #做上已经遍历的标志
		#开始具体操作
		for i in range(len(start.stmt_list)):
			flag, start.stmt_list[i].stmt = \
			right_replace(start.stmt_list[i].stmt, old, new)
			if flag == True:
				return#若发现了重新定义，则这个块不再做了；且之后的块都不用再替换了
		#如果只对下一个块进行修改，是不够的。一般来说需要继续深搜
		#否则还要继续遍历：
		if start.to_block_list[0] == 'EXIT': #next块是EXIT：叶节点
			return
		for i in range(len(start.to_block_list)): #对于所有的next块
			to_block = self.block_list[start.to_block_list[i] + ':']
			self.block_right_replace(to_block, old, new)

def right_replace(s, old, new): #只替换等号右边的内容
	if '=' not in s: #如果只是一个表达式，没有等号
		return False, s.replace(old, new)
	else:
		tmp = s.split('=')
		left = tmp[0]
		right = tmp[-1]
		if left.find(old) == -1:
			flag = False
		else: #如果发现对该变量进行了重定义，则这是最后一次变量替换了。
			flag = True
		return flag, left + '=' + tmp[-1].replace(old, new)

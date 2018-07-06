# encoding: UTF-8

import re
from intervals import IntInterval, FloatInterval
from graphviz import Digraph
from infinity import inf
import copy
import math

import range_analysis.symboltable.context as Context

from range_analysis.symboltable.func import Func
from range_analysis.symboltable.var import parse_var
from range_analysis.symboltable.stmt import parse_stmt, parse_call, parse_from_block
from range_analysis.graph.node import Rangenode, Ftrangenode, Opnode, Varnode, Constnode, Callnode

class Flowgraph(object):
	"""docstring for Flowgraph"""
	def __init__(self, func, init_val, last_Unreached):
		super(Flowgraph, self).__init__()
		self.index = 0
		self.node_list = {}
		self.func = func #记录这是在对哪个函数进行分析
		self.init_val = init_val #记录给定的参数初始值
		# 这两个变量是为了判断不可达分支
		self.last_Unreached = last_Unreached #沿用上一轮的不可达分支，标记dead_block
		self.Unreached = [] #默认不存在不可达分支

		self.deal_with_branch(func) 
		self.parse_stmts(func)
	# ----- 图的建立
	def get_var(self, func, var, var_I=None):
		# 如果已经有了这个变量，则直接返回
		for index in self.node_list:
			node = self.node_list[index]
			if type(node) == Varnode and node.var == var:
				return index
		# 否则，新建立这个变量对应的节点
		return self.add_node(Varnode(func.get_var_type(var), var, var_I))

	def add_node(self, node):
		index = self.index
		self.node_list[self.index] = node
		self.index += 1
		return index

	def add_edge(self, from_node_index, to_node_index): #连边，要处理fromlist和tolist
		self.node_list[from_node_index].next_list.append(to_node_index)
		self.node_list[to_node_index].prev_list.append(from_node_index)

	def add_dashed_edge(self, from_node_index, to_node_index): #future变量的虚线边
		self.node_list[from_node_index].next_dashed_list.append(to_node_index)
		self.node_list[to_node_index].prev_dashed_list.append(from_node_index)

	def deal_with_branch(self, func):
		ops = ['<=', '>=', '==', '!=', '<', '>'] #first <=, then <
		for _block in func.block_list:
			block = func.block_list[_block]
			if block.condition == 'True':
				continue
			for _op in ops:
				if _op in block.condition:
					tmp = block.condition.split(_op)
					op = _op
					to_var, to_var_I = parse_var(tmp[0], self.init_val)
					from_var, from_var_I = parse_var(tmp[-1], self.init_val)
					break
			if is_var(from_var) == False: #虽然名为from_var，其实往往是const
				# 有没有可能to_var是常量而from_var是变量？不管了！
				if func.get_var_type(to_var) == 'int':
					_type = 'int'
					const = int(from_var)
					TheInterval = IntInterval #这是一个类指针
				else:
					_type = 'float'
					const = float(from_var)
					TheInterval = FloatInterval
				if op == '<=':
					range_t_index = self.add_node(Rangenode(_type, TheInterval.at_most(const))) #<=const
					range_f_index = self.add_node(Rangenode(_type, TheInterval.greater_than(const))) #>const
				elif op == '>=':
					range_t_index = self.add_node(Rangenode(_type, TheInterval.at_least(const))) #>=const
					range_f_index = self.add_node(Rangenode(_type, TheInterval.less_than(const))) #<const
				elif op == '==': #TODO：只能这样了吗？？？
					range_t_index = self.add_node(Rangenode(_type, TheInterval([const, const]))) #==const
					range_f_index = self.add_node(Rangenode(_type, TheInterval.all())) #!=const
				elif op == '!=': #只能这样了
					range_t_index = self.add_node(Rangenode(_type, TheInterval.all())) #!=const
					range_f_index = self.add_node(Rangenode(_type, TheInterval([const, const]))) #==const
				elif op == '<':
					range_t_index = self.add_node(Rangenode(_type, TheInterval.less_than(const))) #<const
					range_f_index = self.add_node(Rangenode(_type, TheInterval.at_least(const))) #>=const
				else:#elif op == '>':
					range_t_index = self.add_node(Rangenode(_type, TheInterval.greater_than(const))) #>const
					range_f_index = self.add_node(Rangenode(_type, TheInterval.at_most(const))) #<=const
			else: #var
				ft_var = from_var
				if func.get_var_type(to_var) == 'int':
					_type = 'int'
				else:
					_type = 'float'
				if op == '<=':
					range_t_index = self.add_node(Ftrangenode(_type=_type, rval=ft_var, l='(', r=']')) #<=ft_var
					range_f_index = self.add_node(Ftrangenode(_type=_type, lval=ft_var, l='(', r=')')) #>ft_var
					rev_range_t_index = self.add_node(Ftrangenode(_type=_type, lval=to_var, l='[', r=')')) #>=to_var
					rev_range_f_index = self.add_node(Ftrangenode(_type=_type, rval=to_var, l='(', r=')')) #<to_var
				elif op == '>=':
					range_t_index = self.add_node(Ftrangenode(_type=_type, lval=ft_var, l='[', r=')')) #>=ft_var
					range_f_index = self.add_node(Ftrangenode(_type=_type, rval=ft_var, l='(', r=')')) #<ft_var
					rev_range_t_index = self.add_node(Ftrangenode(_type=_type, rval=to_var, l='(', r=']')) #<=to_var
					rev_range_f_index = self.add_node(Ftrangenode(_type=_type, lval=to_var, l='(', r=')')) #>to_var
				elif op == '==': #TODO：只能这样了吗
					range_t_index = self.add_node(Ftrangenode(_type=_type, lval=ft_var, rval=ft_var, l='[', r=']')) #==ft_var
					range_f_index = self.add_node(Ftrangenode(_type=_type)) #!=ft_var
					rev_range_t_index = self.add_node(Ftrangenode(_type=_type, lval=to_var, rval=ft_var, l='[', r=']')) #==to_var
					rev_range_f_index = self.add_node(Ftrangenode(_type=_type))
				elif op == '!=': #TODO:
					range_t_index = self.add_node(Ftrangenode(_type=_type)) #!=ft_var
					range_f_index = self.add_node(Ftrangenode(_type=_type, lval=ft_var, rval=ft_var, l='[', r=']')) #==ft_var
					rev_range_t_index = self.add_node(Ftrangenode(_type=_type))
					rev_range_f_index = self.add_node(Ftrangenode(_type=_type, lval=to_var, rval=ft_var, l='[', r=']')) #==to_var
				elif op == '<':
					range_t_index = self.add_node(Ftrangenode(_type=_type, rval=ft_var, l='(', r=')')) #<ft_var
					range_f_index = self.add_node(Ftrangenode(_type=_type, lval=ft_var, l='[', r=')')) #>=ft_var
					rev_range_t_index = self.add_node(Ftrangenode(_type=_type, lval=to_var, l='(', r=')')) #>to_var
					rev_range_f_index = self.add_node(Ftrangenode(_type=_type, rval=to_var, l='(', r=']')) #<=to_var
				else:#elif op == '>':
					range_t_index = self.add_node(Ftrangenode(_type=_type, lval=ft_var, l='(', r=')')) #>ft_var
					range_f_index = self.add_node(Ftrangenode(_type=_type, rval=ft_var, l='(', r=']')) #<=ft_var
					rev_range_t_index = self.add_node(Ftrangenode(_type=_type, rval=to_var, l='(', r=')')) #<to_var
					rev_range_f_index = self.add_node(Ftrangenode(_type=_type, lval=to_var, l='[', r=')')) #>=to_var
				# 反向的modify：e.g 把接下来的block中的所有k_1换成k_1_t
				from_var_t_flag, from_var_f_flag = func.blocks_right_replace(block, from_var)
				# 这种情况，还要把反方向的边连上，注意有可能需要加上初值！
				from_var_index = self.get_var(func, from_var, from_var_I)
				from_var_t_index = self.get_var(func, from_var+'_t' if from_var_t_flag else from_var)
				from_var_f_index = self.get_var(func, from_var+'_f' if from_var_f_flag else from_var)
				self.add_edge(from_var_index, rev_range_t_index)
				self.add_edge(rev_range_t_index, from_var_t_index)
				self.add_edge(from_var_index, rev_range_f_index)
				self.add_edge(rev_range_f_index, from_var_f_index)
			# 在block中把to_var添加为branch_var
			block.branch_var.append(to_var)
			# modify e.g 把to_block_t中的所有k_1换成k_1_t
			#本来按说SSA中有版本号，不存在对该变量进行重新定义的问题
			#但是当我看到_8这样的变量的存在的时候，我觉得还是这样做一下比较保险
			#注意，对于简单的do-while语句，可以判断得出来不需要变量替换
			to_var_t_flag, to_var_f_flag = func.blocks_right_replace(block, to_var)
			# 正向连边，注意有可能需要加上初值！
			to_var_index = self.get_var(func, to_var, to_var_I)
			to_var_t_index = self.get_var(func, to_var+'_t' if to_var_t_flag else to_var)
			to_var_f_index = self.get_var(func, to_var+'_f' if to_var_f_flag else to_var)
			# e.g. 连边k_1->[-inf~100)->k_1_t
			self.add_edge(to_var_index, range_t_index)
			self.add_edge(range_t_index, to_var_t_index)
			self.add_edge(to_var_index, range_f_index)
			self.add_edge(range_f_index, to_var_f_index)
			if is_var(from_var) == True: #var
			# future还要连虚线边
				self.add_dashed_edge(from_var_index, range_t_index)
				self.add_dashed_edge(from_var_index, range_f_index)
				self.add_dashed_edge(to_var_index, rev_range_t_index)
				self.add_dashed_edge(to_var_index, rev_range_f_index)

	def parse_stmts(self, func):
		for _block in func.block_list:
			block = func.block_list[_block]
			for stmt in block.stmt_list:
				to_var,op,from_var_1,from_var_I1,from_var_2,from_var_I2 = parse_stmt(stmt.stmt, self.init_val)
				if to_var == None: #需要不是一个单独的表达式
					continue
				to_var_index = self.get_var(func, to_var)				
				if from_var_1 != None: #普通的表达式
					if op == 'PHI':
						from_block_list = parse_from_block(stmt.stmt)
						tmp = {}
						tmp[from_var_1] = from_block_list[0]
						tmp[from_var_2] = from_block_list[1]
						op_index = self.add_node(Opnode('op', op, _block, tmp))
					else:
						op_index = self.add_node(Opnode('op', op))
					#op；如果是PHI的话，同时记下它属于哪个块、和它来自的变量所在的块
					#生成新的图顶点	
					if is_var(from_var_1): #var
						from_var_1_index = self.get_var(func, from_var_1, from_var_I1)
					else: #const
						from_var_1_index = self.add_node(Constnode('const', from_var_1))
					if from_var_2 != None:
						if is_var(from_var_2): #var
							from_var_2_index = self.get_var(func, from_var_2, from_var_I2)
						else: #const
							from_var_2_index = self.add_node(Constnode('const', from_var_2))
					#连边
					self.add_edge(from_var_1_index, op_index)
					if from_var_2 != None:
						self.add_edge(from_var_2_index, op_index)
					self.add_edge(op_index, to_var_index)
				else: #函数。我想函数运算不会是是表达式的一部分，因为这是SSA
					#新的顶点
					from_var_2_index = self.add_node(Callnode('call', from_var_2.split(' ')[0]))
					params, params_I = parse_call(from_var_2, self.init_val)
					# 各个参数对Call节点连边、Call对目标连边
					for i in range(len(params)):
						param_index = self.get_var(func, params[i], params_I[i])
						self.add_edge(param_index, from_var_2_index)
					self.add_edge(from_var_2_index, to_var_index)
	# -----图的显示
	def show(self):
		dot = Digraph('CFG', comment='')
		for _node in self.node_list:
			node = self.node_list[_node]
			label = node._type + '\n'
			if type(node) == Rangenode:
				label += str(node.I)
			elif type(node) == Ftrangenode:
				label += str(node)
			elif type(node) == Opnode:
				label += str(node.op)
			elif type(node) == Varnode:
				label += str(node.var)
			elif type(node) == Constnode:
				label += str(node.const)
			elif type(node) == Callnode:
				label += str(node.call)
			l = str(label) #节点类型
			l += '\nSSC:'+str(node.Belong) #节点所属的分量
			if type(node) not in [Opnode, Callnode]:
				l += '\n'+str(node.I) #节点的范围
			dot.node(str(_node), label=l)
		for _node in self.node_list:
			node = self.node_list[_node]
			for _next in node.next_list: #实线边
				dot.edge(str(_node), str(_next), label='')
			for _next in node.next_dashed_list: #虚线边
				dot.edge(str(_node), str(_next), label='', style='dotted')
		dot.view()
	# -----划分强连通分量
	def get_SSC(self):
		self.Bcnt = -1 #+1，分量的编号从0开始计
		self.Dindex = 0
		self.DFN = [None for i in range(len(self.node_list))]
		self.LOW = [None for i in range(len(self.node_list))]
		self.Stap = [] #stack
		self.Belong = [None for i in range(len(self.node_list))] #标注每个点属于哪个分量
		for i in range(len(self.node_list)):
			if self.DFN[i] == None:
				self.tarjan(i); #标注出所有的SSC
		# 发现，从编号最大的往下走，就是强连通分量之间的一个拓扑排序！！！
		# 一个强连通分量可能有多个入口
		# 一般来说一个是PHI，另一个是二元运算
		# 它们都是二元的，但是一般有一个前驱属于本分量，另一个不属于
		# 如果是二元运算的话，一般来说它的另一个前驱是常数（应该是吧……），于是不用把它作为入口
		# 但是如果一个是PHI，那么它的另一个前驱是变量
		# 那么，应该把PHI作为入口，并且先处理另一个前驱所在的分量
		# 但是，一定要从入口开始吗？？？我觉得既然是强连通的，那么随便从一个地方开始都可以

	def tarjan(self, i):
		self.Dindex += 1
		self.DFN[i] = self.LOW[i] = self.Dindex;
		self.Stap.append(i); #push
		for j in self.node_list[i].next_list: #foreach i->j，不考虑虚线边
			if self.DFN[j] == None:
				self.tarjan(j)
				if (self.LOW[j]<self.LOW[i]):
					self.LOW[i]=self.LOW[j] 
			elif j in self.Stap and self.DFN[j]<self.LOW[i]:
				self.LOW[i]=self.DFN[j]
		if self.DFN[i]==self.LOW[i]:
			self.Bcnt += 1
			while True:
				j=self.Stap.pop();  
				self.Belong[j]=self.Bcnt;
				self.node_list[j].Belong = self.Bcnt;
				if j==i:
					break #do-while
	# -----三阶段处理
	def analyze(self):
		for i in range(len(self.node_list)):
			self.future(i) #预先做一个future，因为有些变量作为参数一开始就有了初值（比如样例t5）！
		for tt in range(2): #TODO：整体要做2（或更多）遍吧？因为第一遍时有些future定值以后可能还没传给其他节点！
			for i in range(self.Bcnt, -1, -1): #倒着遍历每个强连通分量i：这是符合拓扑排序的
				for item in self.node_list:				
					if self.Belong[item] == i: #随便从该分量一个点开始遍历
						for t in range(3): #对这个块的item开始widen，3次之后必定收敛
							self.widen(i, item)
						break
			for i in range(len(self.node_list)):
				self.future(i)
			for i in range(self.Bcnt, -1, -1): #倒着遍历每个强连通分量i：这是符合拓扑排序的
				for item in self.node_list:
					if self.Belong[item] == i: #随便从该分量一个点开始遍历
						self.narrow(i, item) #narrow只需要1次就收敛了吧
						break

	def widen(self, SSC_index, start): #从start开始对分量中的每个节点做widen
		self.vis = [] #标注有哪些块遍历过了
		node = self.node_list[start]
		self.widen_single(SSC_index, node)

	def widen_single(self, SSC_index, node):
		if node in self.vis: #因为块之间存在环，有可能已经遍历过了：结束
			return
		self.vis.append(node) #做上已经遍历的标志
		#开始具体操作
		dead_branch_check = False #除非取交集得到了空集，才改为True
		if type(node) in [Rangenode, Ftrangenode, Opnode, Callnode]:
			if type(node) in [Rangenode, Ftrangenode, Opnode]:
				arg1 = self.node_list[node.prev_list[0]] #从prev节点拿到操作数（不一定要属于本分量）
				if len(node.prev_list) == 2:
					arg2 = self.node_list[node.prev_list[1]]
				else:
					arg2 = None
				e = self.get_evaluate(node, arg1, arg2) #从prev节点算出e。它返回一个deepcopy
				# 同时如果结果是死分支，则widen的处理要进行变化
				if e == 'Empty': #取交集得到了空集
					e = None
					dead_branch_check = True
			else:
				args = []
				for item in node.prev_list:
					args.append(self.node_list[item])
				e = get_call_evaluate(node, args) #从prev节点算出e。它返回一个deepcopy
			for item in node.next_list: #对于各个next节点
				res = self.node_list[item]
				if dead_branch_check == True:
					# 如果上面的运算是求交集、而结果是空集，则需要触发检查死分支的函数！
					res.I = None
					self.mark_dead_block(arg1.var, res.var)
				else:
					widen_update(res, e)
		# elif type(node) == Varnode or type(node) == Constnode
		# 	pass
		for item in node.next_list:
			if self.Belong[item] == SSC_index: #在本块内可能有多个next！见样例t8
				self.widen_single(SSC_index, self.node_list[item])

	def future(self, i): #到底需不需要考虑拓扑顺序呢？？？
		if type(self.node_list[i]) != Varnode or self.node_list[i].I == None:
			return #第一次future是提前做的，因此现在I还可能是空呢
		for item in self.node_list[i].next_dashed_list:
			if self.node_list[item].lval != None: #lval != -inf
				#e.g. 原来是[j_3, a)，现在有[, 99]
				#把lval换成-inf，变成[-inf, a)，然后把这个字符串代入Interval进行初始化
				tmp = copy.deepcopy(self.node_list[item])
				tmp.lval = str(self.node_list[i].I.lower)
				s = str(tmp).replace('-inf', '').replace('inf', '')
				if tmp._type == 'int':
					e = IntInterval.from_string(s)
				else:
					e = FloatInterval.from_string(s)
			else: #rval != inf
				#e.g. 原来是(a,j_3)，现在有[, 99]
				#把rval=j_3换成99，变成(a, 99)，然后把这个字符串代入Interval进行初始化
				tmp = copy.deepcopy(self.node_list[item])
				tmp.rval = str(self.node_list[i].I.upper)
				s = str(tmp).replace('-inf', '').replace('inf', '') #用字符串来初始化不能有inf，而要留空
				if tmp._type == 'int':
					e = IntInterval.from_string(s)
				else:
					e = FloatInterval.from_string(s)
			self.node_list[item].I = e

	def narrow(self, SSC_index, start): #从start开始对分量中的每个节点做narrow
		self.vis = [] #标注有哪些块遍历过了
		node = self.node_list[start]
		self.narrow_single(SSC_index, node)

	def narrow_single(self, SSC_index, node):
		if node in self.vis: #因为块之间存在环，有可能已经遍历过了：结束
			return
		self.vis.append(node) #做上已经遍历的标志
		#开始具体操作
		dead_branch_check = False
		if type(node) in [Rangenode, Ftrangenode, Opnode, Callnode]:
			if type(node) in [Rangenode, Ftrangenode, Opnode]:
				arg1 = self.node_list[node.prev_list[0]] #从prev节点拿到操作数（不一定要属于本分量）
				if len(node.prev_list) == 2:
					arg2 = self.node_list[node.prev_list[1]]
				else:
					arg2 = None
				e = self.get_evaluate(node, arg1, arg2) #从prev节点算出e。它返回一个deepcopy
				if e == 'Empty':
					e = None
					dead_branch_check = True
			else:
				args = []
				for item in node.prev_list:
					args.append(self.node_list[item])
				e = get_call_evaluate(node, args) #从prev节点算出e。它返回一个deepcopy
			for item in node.next_list: #对于各个next节点
				res = self.node_list[item]
				if dead_branch_check == True:
					# 如果上面的运算是求交集、而结果是空集，则需要触发检查死分支的函数！
					res.I = None
					self.mark_dead_block(arg1.var, res.var)
				else:
					narrow_update(res, e)
		# elif type(node) == Varnode or type(node) == Constnode
		# 	pass
		for item in node.next_list:
			if self.Belong[item] == SSC_index: #在本块内可能有多个next！见样例t8
				self.narrow_single(SSC_index, self.node_list[item])

	def get_return_interval(self, callee):
		for _node in self.node_list:
			node = self.node_list[_node]
			if type(node) == Varnode and node.var == callee.return_var:
				return node.I #得到返回的范围

	def mark_dead_block(self, from_var, to_var): #标记出这一轮不可达的块
		for _block in self.func.block_list:
			block = self.func.block_list[_block]
			if from_var in block.branch_var:
				if to_var.endswith('_t'): #将分支变量所在块到对应分支块的边标记成死边
					block.to_block_live[0] = False
				else:
					block.to_block_live[1] = False
		#然后对现在不可达的块进行标记-清扫算法。因为block只记录了出边而没有入边，不好做引用计数
		Scanned = []
		Unscanned = ['ENTRY']
		self.Unreached = [] #重新计算这一轮的Unreached
		for _block in self.func.block_list:
			if _block != 'ENTRY' and _block not in self.Unreached:
				self.Unreached.append(_block) #要保留最后的:
		while len(Unscanned) > 0:
			_o = Unscanned[0]
			Scanned.append(_o)
			Unscanned.pop(0)
			o = self.func.block_list[_o]
			for i in range(len(o.to_block_list)):
				_oo = o.to_block_list[i] + ':'
				if o.to_block_live[i] == True and _oo in self.Unreached:
					Unscanned.append(_oo)
					self.Unreached.remove(_oo)

	def get_evaluate(self, op, arg1, arg2): #需要判断死分支，所以必须是类内函数
		if type(op) in [Rangenode, Ftrangenode]:
			I1 = arg1.I
			I2 = op.I #Rangenode有I、且I一定不是None
			#而Ftrangenode一开始的I没有初始化，要等到做完Future Resolution以后才有
		elif type(op) == Opnode: #op，可能是一元或二元的
			I1 = arg1.I
			if arg2 != None:
				I2 = arg2.I
			else:
				I2 = None
			if type(arg1) == Varnode\
			and (arg1.var.endswith('_t') or arg1.var.endswith('_f'))\
			and arg1.Belong != op.Belong:
			# 如果arg1要参与其他分量节点的区间运算（即出循环）、且它是_t/_f，则要让它的区间收敛
				# print arg1.var, I1
				if I1 != None: #有可能它是空集；这说明这是一个不可能分支
					pass # TODO：应该在这里让区间收敛。但是要解决问题太多了
					# 问题1、怎么确定收敛结果？因为在分支语句中可能是跟变量比较，收敛的结果可能是一个区间而不是一个点！
				# 问题2、就算能让它正确收敛，因为区间变小了，它也无法再影响传递出去的e了。
				# 问题3、就算一路上的节点成功更新了，还有一个问题：无法区分PHI语句的from是循环初值还是if分支
				# 把循环初值误判成了if分支还造成了其他的问题：不可能分支的误判
			if arg2 != None and type(arg2) == Varnode\
			and (arg2.var.endswith('_t') or arg2.var.endswith('_f'))\
			and arg2.Belong != op.Belong:
			# 如果arg2要参与其他分量节点的区间运算（即出循环）、且它是_t/_f，则要让它的区间收敛
				if I2 != None: #有可能它是空集；这说明这是一个不可能分支
					pass # TODO：同上
		# else:
		# 	pass
		if type(op) in [Rangenode, Ftrangenode]: #求交集
			if I1 == None:
				e = None #这里I1为None代表它是空集，而不是未初始化
			elif I2 == None:
				e = copy.deepcopy(I1)
			else:
				try:
					e = I1 & I2
				except Exception as ex:
					e = 'Empty' #没有交集，则取空集
				else:
					pass
				finally:
					pass
		# 以下都是opnode。先是一元运算
		elif op.op == '(float)':
			e = FloatInterval([I1.lower, I1.upper])
			e.upper_inc = I1.upper_inc
			e.lower_inc = I1.lower_inc
		elif op.op == '(int)':
			if math.isinf(I1.lower):
				lower = -inf
			else:
				val = round(I1.lower)
				if abs(val-int(val)) <= 1e-6:
					lower = int(val) #浮点误差
				else:
					lower = int(I1.lower)
			if math.isinf(I1.upper):
				upper = inf
			else:
				val = round(I1.upper)
				if abs(val-int(val)) <= 1e-6:
					upper = int(val) #浮点误差
				else:
					upper = int(I1.upper)
			e = IntInterval([lower, upper])
			e.upper_inc = I1.upper_inc
			e.lower_inc = I1.lower_inc # TODO:整数化以后开闭可能变化！
		elif op.op == '=':
			e = copy.deepcopy(I1)
		# 再是二元运算
		elif op.op == 'PHI':
			# 如果一个arg是同一个分量的，而另一个不是：这是在一个循环内部
			if (arg1.Belong == op.Belong and arg2.Belong != op.Belong)\
			or (arg2.Belong == op.Belong and arg1.Belong != op.Belong):
			# if arg1.Belong == op.Belong or arg2.Belong == op.Belong:
				if arg1.Belong == op.Belong:
					inner = arg1
					outer = arg2
				else:
					inner = arg2
					outer = arg1
				# 第一次进循环，内部还是None，直接取外部；以后内部不是None了，就取内部
				if inner.I == None:
					e = copy.deepcopy(outer.I)
				else:
					e = copy.deepcopy(inner.I)
			else: #两个都不是另外一个分量的：这是一个if分支，应该取并集
				# 注意：还可能两者都是Inner的，见样例t9那个很复杂的分量。我认为这也算一个if分支？
				# 注意，只对if分支先排除不可能分支，因为对于循环存在误判的可能：
				# 循环一开始范围只有初值，此时因为交集为空而被误判为不可能分支
				# 但是循环几次以后范围扩大了，此时又变成可能分支了
				if op.phi_from_block[arg1.var] in self.last_Unreached:
					e = copy.deepcopy(arg2.I)
				elif op.phi_from_block[arg2.var] in self.last_Unreached:
					e = copy.deepcopy(arg1.I)
				# 然后取并集
				elif arg1.I == None:
					e = copy.deepcopy(arg2.I)
				elif arg2.I == None:
					e = copy.deepcopy(arg1.I)
				else:
					inner = arg1 #还是用inner和outer来标记吧
					outer = arg2
					e = copy.deepcopy(inner.I)
					if (outer.I.lower<e.lower) or\
					(outer.I.lower == e.lower and outer.I.lower_inc==False):
					#就算一个是(5一个是[6，或者一个是(6一个是[6，改一下也不会错
						e.lower = outer.I.lower
						e.lower_inc = outer.I.lower_inc# 开闭也要修改
					if (outer.I.upper>e.upper) or\
					(outer.I.upper == e.upper and outer.I.upper_inc==True):
					#就算一个是(5一个是[6，或者一个是(6一个是[6，改一下也不会错
						e.upper = outer.I.upper
						e.upper_inc = outer.I.upper_inc# 开闭也要修改
		else: #op：None参与时直接返回None
			if I1 == None or I2 == None:
				e = None
			elif op.op == '+':
				e = I1 + I2
				e.lower_inc = I1.lower_inc and I2.lower_inc #只要有一个开，结果就是开
				e.upper_inc = I1.upper_inc and I2.upper_inc #只要有一个开，结果就是开
				#TODO，对于整数，(1,3)+(3,5)=(4,8)是错的！不过允许有一点误差
			elif op.op == '-':
				# e = I1 - I2 这样写可能会出错
				e = copy.deepcopy(I1)
				e.lower += -I2.upper
				e.upper += -I2.lower #- -inf不等于+ inf，所以必须这么写……
				e.lower_inc = I1.lower_inc and I2.upper_inc #只要有一个开，结果就是开
				e.upper_inc = I1.upper_inc and I2.lower_inc #只要有一个开，结果就是开				
				#TODO，对于整数，(1,3)+(3,5)=(4,8)是错的！不过允许有一点误差
			elif op.op == '*': #TODO: 开闭的问题！！！现在默认是闭！
				L = [mul(I1.lower,I2.lower), mul(I1.lower,I2.upper), mul(I1.upper,I2.lower), mul(I1.upper,I2.upper)]
				if arg1._type == 'int':
					e = IntInterval([min(L), max(L)])
				else:
					e = FloatInterval([min(L), max(L)])
			elif op.op == '/': # TODO 开闭的问题
				L = [div(I1.lower,I2.lower), div(I1.lower,I2.upper),\
				div(I1.upper,I2.lower), div(I1.upper,I2.upper)]
				if arg1._type == 'int':
					e = IntInterval([min(L), max(L)])
				else:
					e = FloatInterval([min(L), max(L)])
		return e

def get_call_evaluate(node, args): #计算出函数调用的返回值，它不涉及PHI，不需要成为类内函数
	init_val = {}
	callee = Context.func_list[node.call]
	param_name = callee.param_name
	for i in range(len(param_name)):
		init_val[param_name[i]] = args[i].I #建立（形参->实参初始值）映射表
	# 分析过程利用上一轮的不可能分支来做
	last_Unreached = []
	for t in range(5): #还是要防止一下死循环；我想最多五次也就收敛了
		graph = Flowgraph(callee, init_val, last_Unreached) #沿用上一轮的不可能分支，内部会进行deepcopy
		graph.get_SSC()
		graph.analyze()
		if cmp(last_Unreached, graph.Unreached) == 0:
			break #如果不可能分支没有变化，则结束
		else:
			last_Unreached = graph.Unreached #记录下这一轮得到的新的不可能分支
		# last_Unreached = [] #因为判断不可能分支的部分可能有bug
		# 可以加上这一句来关闭对不可能分支的判断。这样本来会进入死循环，不过5次以后会跳出
	# graph.show()
	return graph.get_return_interval(callee)

def is_var(var_name): #从名字是否为字母开头来判断是常量还是变量
	pattern = r'^[A-Za-z_]'
	if re.search(pattern, var_name):
		return True
	else:
		return False

def mul(a, b): #要处理无穷的问题，例如[10,inf]*[5,inf] = [50,inf]
	if math.isinf(a) or math.isinf(b):
		if (a<0 and b<0) or (a>0 and b>0):
			return inf
		elif (a<0 and b>0) or (a>0 and b<0):
			return -inf
		else: #a和b一个是0，一个是inf
			return 0 #TODO：就按照0处理了？
	else:
		return a*b

def div(a, b): #要处理无穷的问题，例如[10,inf]/[5,inf] = [2,inf]
	if math.isinf(a) or math.isinf(b):
		if (a<0 and b<0) or (a>0 and b>0):
			return inf
		elif (a<0 and b>0) or (a>0 and b<0):
			return -inf
		else: #a和b一个是0，一个是inf
			return inf #TODO: 按照inf处理？
	else:
		return a/b

def widen_update(res, e): #用e更新res.I
	if e == None: #对于二元运算，比如None+[1,1]，得到的e就是None
		res.I = None
	elif res.I == None:
		res.I = copy.deepcopy(e) #不同的next节点各自拷贝一份，免得冲突
	else: # 如果e的范围更宽，则让res.I往inf的方向修改
		if (e.lower<res.I.lower) or\
		(e.lower == res.I.lower and e.lower_inc==False and res.I.lower_inc==True):
			res.I.lower = -inf
		#就算一个是(5一个是[6，改一下也不会错；或者一个是(6一个是[6，需要改
		if (e.upper>res.I.upper) or\
		(e.upper == res.I.upper and e.upper_inc==True and res.I.upper_inc==False):
			res.I.upper = inf

def narrow_update(res, e): #用e更新res.I
	if e == None or res.I == None: #比如取交集的结果是空，则把res.I又变回None
		res.I = None #这里也可能有e == None
	else: #如果res.I范围有inf，则往e的方向修改（变窄）
		if math.isinf(res.I.lower) and not math.isinf(e.lower): #-inf <= e.lower
			res.I.lower = e.lower
			res.I.lower_inc = e.lower_inc # 开闭也要修改
		if math.isinf(res.I.upper) and not math.isinf(e.upper): #inf <= e.upper
			res.I.upper = e.upper
			res.I.upper_inc = e.upper_inc # 开闭也要修改
		# 如果e的范围更宽，则让res.I往e的方向修改（变宽）
		if (e.lower<res.I.lower) or\
		(e.lower == res.I.lower and e.lower_inc==False):
		#就算一个是(5一个是[6，改一下也不会错；或者一个是(6一个是[6
			res.I.lower = e.lower
			res.I.lower_inc = e.lower_inc # 开闭也要修改
		if (e.upper>res.I.upper) or\
		(e.upper == res.I.upper and e.upper_inc==True):
			res.I.upper = e.upper
			res.I.upper_inc = e.upper_inc # 开闭也要修改

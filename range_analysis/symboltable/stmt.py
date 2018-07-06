# encoding: UTF-8

import re
import copy

from var import parse_var

class Stmt(object):
	"""docstring for Stmt"""
	def __init__(self, stmt):
		super(Stmt, self).__init__()
		self.stmt = stmt

	def __str__(self):
		return self.stmt

def parse_stmt(_stmt, init_val): #返回：to_var op from_var_1 from_var_2的四元式。这里var也可能是常量
	stmt = copy.deepcopy(_stmt)
	if '=' not in stmt: #因为不涉及指针，单独一个表达式（就算是函数）也不会有任何作用
		return None,None,None,None,None,None
	else:
		stmt = stmt.strip('# ') #删掉开头的'# '
		reg = re.compile(r'[^\s]*\s+')
		to_var, to_var_I = parse_var(reg.findall(stmt)[0], init_val)
		stmt = stmt.split('=')[-1].strip() #取等号右边的表达式
		if stmt.startswith('PHI'): #PHI
			op = 'PHI'
			reg = re.compile(r'\s*[^\s]*\(')
			tmp = reg.findall(stmt)
			from_var_1, from_var_I1 = parse_var(tmp[0].strip(' <('), init_val)
			from_var_2, from_var_I2 = parse_var(tmp[1].strip(' ('), init_val)
			return to_var, op, from_var_1, from_var_I1, from_var_2, from_var_I2
		elif stmt.startswith('(float)'): #float类型转换
			op = '(float)'
			reg = re.compile(r'\s+[^\s]*;')
			from_var_1, from_var_I1 = parse_var(reg.findall(stmt)[0].strip(' ;'), init_val)
			return to_var, op, from_var_1, from_var_I1, None, None
		elif stmt.startswith('(int)'): #int类型转换
			op = '(int)'
			reg = re.compile(r'\s+[^\s]*;')
			from_var_1, from_var_I1 = parse_var(reg.findall(stmt)[0].strip(' ;'), init_val)
			return to_var, op, from_var_1, from_var_I1, None, None
		else:
			ops = [' + ', ' - ', ' * ', ' / '] #avoid const, e.g. 1e+1
			for _op in ops:
				if _op in stmt:
					op = _op.strip()
					reg = re.compile(r'\s*[^\s]*\s+')
					from_var_1, from_var_I1 = parse_var(reg.findall(stmt)[0].strip(), init_val)
					reg = re.compile(r'\s+[^\s]*;')
					from_var_2, from_var_I2 = parse_var(reg.findall(stmt)[0].strip(' ;'), init_val)
					return to_var, op, from_var_1, from_var_I1, from_var_2, from_var_I2
			#没有算术运算
			if '(' in stmt: #函数调用，不在本方法中处理
				return to_var, '=', None, None, stmt, None
			else:
				# 只有一个量
				op = '='
				reg = re.compile(r'\s*[^\s]*;')
				from_var_1, from_var_I1 = parse_var(reg.findall(stmt)[0].strip(' ;'), init_val)
				return to_var, op, from_var_1, from_var_I1, None, None

def parse_call(_stmt, init_val):
	stmt = copy.deepcopy(_stmt)
	stmt = stmt.split(' ')[-1].strip(';') #bar (i_2(D));取后半段再去掉;
	stmt = stmt[1:-1] #去掉最外层的括号
	params = []
	params_I = []
	for _var in stmt.split(','):
		var, var_I = parse_var(_var.strip(), init_val) #获得每个参数，去掉空格，解析
		params.append(var)
		params_I.append(var_I)
	return params, params_I
	
def parse_from_block(_stmt):
	stmt = copy.deepcopy(_stmt)
	x = stmt.split(',')
	from_block = []
	for i in range(2):
		front, rear = x[i].rindex('(')+1, x[i].rindex(')') #跳过前面可能的(D)
		from_block.append('<bb '+x[i][front:rear]+'>:')
	return from_block
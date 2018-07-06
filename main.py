# encoding: UTF-8

import re
from infinity import inf
from intervals import IntInterval, FloatInterval

import range_analysis.symboltable.context as Context
from range_analysis.symboltable.func import Func
from range_analysis.graph.flowgraph import Flowgraph

def get_SSA(filename):
	file = open(filename, 'r')
	code = file.read()
	file.close()
	return code

def create_func_list(code):
	#;; Function name (...) name ()
	pattern = r';;\s*Function\s+.+\s*\([^()]*\)\s*.+\s*\([^()]*\)'
	reg = re.compile(pattern)
	funcs = reg.findall(code)
	#{body}
	reg = re.compile(Context.BRACE_PATTERN)
	func_bodies = reg.findall(code)
	for i in range(len(funcs)):
		# search func_decl & name
		func_decl = funcs[i].split('\n')[-1] #skip ';; Function name (...)'
		name = func_decl.split(' ')[0]
		# search var_decl & func_body
		index = func_bodies[i].index('<bb 2>:')
		var_decl = func_bodies[i][1:index-1] #skip '{'
		func_body = func_bodies[i][index:-1] #skip '}'
		Context.func_list[name] = Func(func_decl, var_decl, func_body)

if __name__=='__main__':
	code = get_SSA('benchmark/t1.ssa')
	init_val = {} #[100, 100]
	# code = get_SSA('benchmark/t2.ssa')
	# init_val = {'k':IntInterval.from_string('[200, 300]')} #[200, 300]
	# code = get_SSA('benchmark/t3.ssa')
	# init_val = {'k':IntInterval.from_string('[0, 10]'), 
	# 	'N':IntInterval.from_string('[20, 50]')} #[20, 50]
	# code = get_SSA('benchmark/t4.ssa')
	# init_val = {'argc':IntInterval.from_string('[, ]')} #[0, inf]
	# code = get_SSA('benchmark/t5.ssa')
	# init_val = {} #[210, 210] 一端错误
	# code = get_SSA('benchmark/t6.ssa')
	# init_val = {'argc':IntInterval.from_string('[, ]')} #[-9, 10]
	# code = get_SSA('benchmark/t7.ssa')
	# init_val = {'i':IntInterval.from_string('[-10,10]')} #[16, 30]
	# code = get_SSA('benchmark/t7_2.ssa') #函数层数太多，比较耗时
	# init_val = {'i':IntInterval.from_string('[-10,10]')} #[16, 30]
	# code = get_SSA('benchmark/t8.ssa')
	# init_val = {'a':IntInterval.from_string('[1,100]'),
	# 	'b':IntInterval.from_string('[-2,2]')} #[-3.22, 5.94]
	# code = get_SSA('benchmark/t9.ssa')
	# init_val = {} #[9791,9791]
	# code = get_SSA('benchmark/t10.ssa')
	# init_val = {'a':IntInterval.from_string('[30, 50]'),
	# 	'b':IntInterval.from_string('[90, 100]')} #[-10,40]
	# code = get_SSA('benchmark/t10_2.ssa') #如果改成i<b-j试试，还是错误。
	# init_val = {'a':IntInterval.from_string('[30, 50]'),
	# 	'b':IntInterval.from_string('[90, 100]')} #[-10,40]
	code = get_SSA('benchmark/t10_3.ssa') #如果改成j<b-i试试，一端错误。
	init_val = {'a':IntInterval.from_string('[30, 50]'),
		'b':IntInterval.from_string('[90, 100]')} #[-10,40]

	create_func_list(code)
	callee = Context.func_list['foo']
	# 分析过程利用上一轮的不可能分支来做
	last_Unreached = []
	for t in range(5): #还是要防止一下死循环；我想最多五次也就收敛了
		graph = Flowgraph(callee, init_val, last_Unreached)
		graph.get_SSC()
		graph.analyze()
		if cmp(last_Unreached, graph.Unreached) == 0:
			break #如果不可能分支没有变化，则结束
		else:
			last_Unreached = graph.Unreached #记录下这一轮得到的新的不可能分支
		# last_Unreached = [] #因为判断不可能分支的部分可能有bug，例如样例t9
		# 可以加上这一句来关闭对不可能分支的判断。这样本来会进入死循环，不过5次以后会跳出
		# 注意，同时要在call语句处也加上这句话
	graph.show()
	print graph.get_return_interval(callee)
	
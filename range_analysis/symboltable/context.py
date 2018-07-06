# encoding: UTF-8
# global vars
func_list = {}

# consts
LABEL_DECL_PATTERN = r'<bb\s*\d+>:|<L\s*\d+>:'
LABEL_PATTERN = r'<bb\s*\d+>|<L\s*\d+>'
BRACE_PATTERN = r'\{[^{}]*\}'
# BRACKET_PATTERN = 
PARENTHESE_GREEDY_PATTERN = r'\(.*\)' #outermost parentheses
PARENTHESE_PATTERN = r'\([^()]*\)'

# pip install git+https://github.com/taschini/pyinterval
# to get pyinterval
# pip install git+https://github.com/kvesteri/intervals
# to get intervals

# func_list = <name: class Func={param_list, var_list, block_list}>
# TODO: return_var_name
	# param_list = <name: class Var={type, interval}>
	# var_list = <name: class Var={type, interval}>
	# 真正在流图中操作的时候，需要建立一个带版本号的真·var_list，
	# 用param_list中的interval对真·var_list的interval做初始化
	# block_list = <label: class Block={stmt_list, condition, to_block_list}> 
	# 真正在流图中操作的时候，还需要记录from_block
	# stmt_list = [class Stmt={stmt}，同时提供方法进行对于stmt的解析]

#Flowgraph
#Node: 具体的各种node
	
#现在的问题是：
#控制边（虚线）到底要不要？
#三步法到底怎么做？

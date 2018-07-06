# encoding: UTF-8

from intervals import IntInterval, FloatInterval

class Var(object):
	"""docstring for Var"""
	def __init__(self, var_type, interval=None):
		super(Var, self).__init__()
		self.var_type = var_type
		self.interval = {}
		if var_type == 'int':
			if interval == None:
				self.interval['int'] = IntInterval.all()
			else:
				self.interval['int'] = IntInterval(interval)
		elif var_type == 'float':
			if interval == None:
				self.interval['float'] = FloatInterval.all()
			else:
				self.interval['float'] = FloatInterval(interval)

	def __str__(self):
		return 'var_type: ' + self.var_type\
		+ '\ninterval: ' + self.interval[self.var_type]

def parse_var(s, init_val): #解析变量名，同时返回其初始值
	var_name = s.strip()
	index = var_name.find('(D)')
	if index != -1:
		var_name = var_name[:index]
		if var_name.find('_') != -1:
			var_src_name = var_name.split('_')[0] #k_1取k
			var_I = init_val[var_src_name]
		else:
			var_I = None
	else:
		var_I = None
	return var_name, var_I

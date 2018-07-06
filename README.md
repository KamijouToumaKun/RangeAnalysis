# RangeAnalysis

首先用命令gcc -S -fdump-tree-ssa source.c 将source.c转换为.ssa文件
再使用本程序对样例进行测试。（还有不少问题正在修改中……）

本程序对变量做取值范围分析，使用的算法参见参考资料中的论文以及对应PPT。
运行环境为python 2.7（各个print都没有写成函数的形式）

用到的包：
1、graphviz：将数据流图可视化，方便调试
2、intervals：进行区间操作。GitHub地址：https://github.com/kvesteri/intervals
可以通过pip install git+https://github.com/kvesteri/intervals来安装

本程序的主文件是根目录下的main.py，采用文件输入和控制台输出。举例：
例如要测试benchmark/t2.ssa，其参数为int k，输入范围是[200, 300]
则在main.py中保留以下两个语句：
1、code = Context.get_SSA('benchmark/t2.ssa')
2、init_val = {'k':IntInterval.from_string('[200, 300]')} #[200, 300]
而把其他的对于code和init_val的赋值都注释掉
运行，得到控制台输出：[200, 300]

得到助教允许，在benchmark/t7.ssa中加了一个基本块标签<bb 5>
因此它跟原始提供的t7.ssa文件略有不同

对于新给的测试样例，请放在根目录下。例如：code = Context.get_SSA('t11.ssa')
并且给出相应的输入范围。提醒：
1、如果参数的类型是float，请把IntInterval.from_string改成FloatInterval.from_string
2、如果输入范围有一端是开区间，则把from_string参数字符串的'['或']'对应地改成'('或')'
3、如果输入范围有一端是无穷大，则把from_string参数字符串中的这一端空着不写
例如[-inf, 8]写成[,8]，[-inf, inf]写成[,]
类似的，如果输出为[,8]，它表示结果是[-inf,8]

如果样例文件涉及函数调用，尤其是多层的函数调用，计算结果用时可能长达几十秒，请耐心等待。

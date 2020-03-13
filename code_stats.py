#
# Example of how to analyze C code and push statistics to Graphite 

from pycparser import c_parser, c_ast, parse_file
import time
import socket

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003

def last_line(node):
    children = node.children()
    if not children:
        return node.coord.line
    else:
        last_child = last_line(children[-1][1])
        if type(node) == c_ast.Compound:
            return last_child + 1 #Closing curly
        else:
            return last_child 

def block_length(node):
    return last_line(node) - node.coord.line

def mean(x):
    return sum(x) / max(1, len(x))

class NestingDepthVisitor(c_ast.NodeVisitor):
    def __init__(self, fname):
        self.fname = fname
        self.depth = 0
        self.area = 0
        self.max_depth = 0
        self.max_depths = []
        self.total_flen = 0
    def visit_FuncDef(self, node):
        if node.coord.file != self.fname:
            #Do not count included functions
            return
        self.total_flen += block_length(node.body)
        self.max_depth = 0
        self.generic_visit(node.body)
        self.max_depths.append(self.max_depth)
    def visit_If(self, node):
        self.recursion(node)
    def visit_For(self, node):
        self.recursion(node)
    def visit_While(self, node):
        self.recursion(node)
    def visit_Do(self, node):
        self.recursion(node)
    def visit_Switch(self, node):
        self.recursion(node)
    def visit_Case(self, node):
        self.generic_visit(node)
    def visit_Default(self, node):
        self.generic_visit(node)
    def recursion(self, node):
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)
        self.generic_visit(node)
        self.depth -= 1
    def visit_Compound(self, node):
        block_len = block_length(node)
        self.generic_visit(node)
        self.area += block_len
    def stats(self):
        return {
            "max_nesting_depth": max(self.max_depths),
            "avg_max_nesting_depth": mean(self.max_depths),
            "average_nesting_depth": self.area / self.total_flen
        }

class FuncDefVisitor(c_ast.NodeVisitor):
    def __init__(self, fname):
        self.func_count = 0
        self.param_count = 0
        self.total_fun_len = 0
        self.fname = fname
    def report_func(self, fun_name, length, param_count):
        print("{} {} lines, {} params".format(fun_name, length, param_count))
        self.func_count += 1
        self.param_count += param_count
        self.total_fun_len += length
    def visit_FuncDef(self, node):
        if node.coord.file != self.fname:
            #Do not count included functions
            return
        name = node.decl.name
        param_count = len(node.decl.type.args.params)
        self.report_func(name, max(1, block_length(node.body) - 1), param_count)
    def stats(self):
        return {
            'function_count': self.func_count,
            'average_function_length': self.total_fun_len / self.func_count,
            'average_function_params': self.param_count / self.func_count
        }

def send_to_carbon(prefix, stats):
    timestamp = int(time.time())
    lines = [ '{}.{} {} {}'.format(prefix, k, v, timestamp) for k,v in stats.items()]
    lines.append('')
    message = '\n'.join(lines)
    sock = socket.socket()
    sock.connect((CARBON_SERVER, CARBON_PORT))
    sock.sendall(message.encode('utf-8'))
    sock.close()

def show_func_lens(filename):
    ast = parse_file(filename, use_cpp=True, cpp_path='clang', cpp_args=['-E', '-Iutils/fake_libc_include', '--std=c11'])
    fdv = FuncDefVisitor(filename)
    fdv.visit(ast)
    ndv = NestingDepthVisitor(filename)
    ndv.visit(ast)
    stats = {**fdv.stats(), **ndv.stats()}
    print(stats)
    send_to_carbon('vector', stats)

show_func_lens("data/vector.c")



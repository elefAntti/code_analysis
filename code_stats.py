#
# Example of how to analyze C code and push statistics to Graphite 

from pycparser import c_parser, c_ast, parse_file
import time
import socket
import os

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
    return max(1, last_line(node) - node.coord.line - 1)

def count_params(node):
    basic_count = len(node.decl.type.args.params)
    if basic_count == 1:
        itype = node.decl.type.args.params[0].type.type
        if type(itype) == c_ast.IdentifierType and itype.names[0] == 'void':
            return 0
    return basic_count

def mean(x):
    return sum(x) / max(1, len(x))

def count_decls(node):
    children = node.children()
    consts = 0
    statics = 0
    regular = 0
    if not children:
        return (0, 0, 0)
    else:
        for _, child in children:
            if type(child) == c_ast.Decl and type(child.type) == c_ast.TypeDecl:
                if 'const' in child.quals:
                    consts += 1
                elif 'static' in child.storage:
                    statics += 1
                else:
                    regular += 1
        return (consts, statics, regular)

class StatsVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.fname = ""
        self.depth = 0
        self.area = 0
        self.max_depth = 0
        self.max_depths = []
        self.total_flen = 0
        self.statics = 0 
        self.regular_vars = 0 
        self.has_statics = False
        self.funcs_with_statics = 0
        self.func_count = 0
        self.param_count = 0
        self.total_fun_len = 0
        self.global_vars = 0
        self.static_global_vars = 0
        self.file_count = 0
        self.funcs_with_no_params = 0
        self.funcs_with_many_params = 0
        self.long_functions = 0
        self.huge_functions = 0

    def process_file(self, filename, ast):
        self.fname = filename
        self.file_count += 1
        decls = count_decls(ast)
        self.static_global_vars += decls[1]
        self.global_vars += decls[2]
        self.visit(ast)
    def visit_FuncDef(self, node):
        if node.coord.file != self.fname:
            #Do not count included functions
            return
        func_len = block_length(node.body)
        self.total_flen += func_len
        if func_len > 50:
            self.long_functions += 1
        if func_len > 300:
            self.huge_functions += 1
        self.max_depth = 0
        self.has_statics = False
        self.recursion(node)
        if self.has_statics:
            self.funcs_with_statics += 1
        self.max_depths.append(self.max_depth)
        self.func_count += 1
        param_count = count_params(node)
        if param_count == 0:
            self.funcs_with_no_params += 1
        if param_count > 4:
            self.funcs_with_many_params += 1
        self.param_count += param_count

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
        decls = count_decls(node)
        self.statics += decls[1]
        self.regular_vars += decls[2]
        if decls[1] > 0:
            self.has_statics = True
        block_len = block_length(node)
        self.generic_visit(node)
        self.area += block_len
    def stats(self):
        return {
            "max_nesting_depth": max(self.max_depths),
            "avg_max_nesting_depth": mean(self.max_depths),
            "average_nesting_depth": self.area / self.total_flen,
            "funcs_with_statics": self.funcs_with_statics,
            'function_count': self.func_count,
            'average_function_length': self.total_flen / self.func_count,
            'average_function_params': self.param_count / self.func_count,
            'average_variable_count': (self.regular_vars + self.statics) / self.func_count,
            'global_vars': self.global_vars + self.static_global_vars,
            'extern_vars': self.global_vars,
            'file_count': self.file_count,
            'functions_without_params': self.funcs_with_no_params, 
            'functions_with_many_params': self.funcs_with_many_params,
            'long_functions': self.long_functions,
            'really_long_functions': self.huge_functions
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

def compute_stats(path):
    ndv = StatsVisitor()
    for filename in os.listdir(path):
        filename = "/".join([path, filename])
        print(filename)
        ast = parse_file(filename, use_cpp=True, cpp_path='clang', cpp_args=['-E', '-Iutils/fake_libc_include', '--std=c11'])
        ndv.process_file(filename, ast)
    stats = ndv.stats()
    print(stats)
    send_to_carbon('vector', stats)

compute_stats("data")



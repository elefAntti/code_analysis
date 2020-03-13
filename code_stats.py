#
# Example of how to analyze C code and push statistics to Graphite 

from pycparser import c_parser, c_ast, parse_file
import time
import socket

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003

class FuncDefVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.func_count = 0
        self.param_count = 0
        self.total_fun_len = 0
    def report_func(self, fun_name, length, param_count):
        print("{} {} lines, {} params".format(fun_name, length, param_count))
        self.func_count += 1
        self.param_count += param_count
        self.total_fun_len += length
    def visit_FuncDef(self, node):
        name = node.decl.name
        param_count = len(node.decl.type.args.params)
        if node.body.block_items:
            first_line = node.body.block_items[0].coord.line
            last_line = node.body.block_items[-1].coord.line
            self.report_func(name, last_line - first_line + 1, param_count)
        else:
            self.report_func(name, 0, param_count)
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
    v = FuncDefVisitor()
    v.visit(ast)
    send_to_carbon('vector', v.stats())

show_func_lens("data/vector.c")



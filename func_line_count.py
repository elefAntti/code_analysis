from pycparser import c_parser, c_ast, parse_file

class FuncDefVisitor(c_ast.NodeVisitor):
    def visit_FuncDef(self, node):
        name = node.decl.name
        if node.body.block_items:
            first_line = node.body.block_items[0].coord.line
            last_line = node.body.block_items[-1].coord.line
            print("'{}' is {} lines long".format(name, last_line - first_line + 1))
        else:
            print("'{}' is {} lines long".format(name, 0))
        print("'{}'' has {} params".format(name, len(node.decl.type.args.params)))

def show_func_lens(filename):
    ast = parse_file(filename, use_cpp=True, cpp_args=r'-Iutils/fake_libc_include')
    v = FuncDefVisitor()
    v.visit(ast)

show_func_lens("data/test.c")




from typing import Union

T_sn = tuple[Union[int, str, "T_sn"], ...]

CONST = {
    'output': 'output',
    'seq': 'Seq',
    'roll': 'roll',
    'range': 'myrange',
}

class PythonResolver:
    def __init__(self, root):
        self.root: T_sn = root

    def resolve(self):
        print(f'INPUT TREE:\n{self.root}\n\n')
        result = '\n'.join(map(self.resolve_node, self.root))
        print(f'RESULT:{result}\n\n')
        return result

    def resolve_node(self, node, cur_indent=0):
        if node[0] == 'number':
            return node[1]
        elif node[0] == 'var':  # variable inside an expression
            return node[1]
        elif node[0] == 'var_name':  # variable name inside a string, utilize f-string
            return node[1].replace('{', '').replace('}', '')

        # OUTPUT
        if node[0] == 'output':
            params = self.resolve_node(node[1])
            return f'{CONST["output"]}({params})'
        elif node[0] == 'output_named':
            params = self.resolve_node(node[1])
            name = self.resolve_node(node[2])
            return f'{CONST["output"]}({params}, named=f"{name}")'
        elif node[0] == 'string':
            return cleanup_string(node[1])
        elif node[0] == 'strvar':
            return '{' + node[1] + '}'
        elif node[0] == 'concat_string':
            l = node[1] if isinstance(node[1], str) else self.resolve_node(node[1])
            r = node[2] if isinstance(node[2], str) else self.resolve_node(node[2])
            res = l + r
            return cleanup_string(res)

        # CONDITIONALS
        elif node[0] == 'if':
            cond, code = node[1], node[2]
            res = f'if {self.resolve_node(cond)}:\n'
            res += '\n'.join([indent_str(self.resolve_node(x, cur_indent+2), cur_indent+2) for x in code])
            rest = node[3:]
            for i in range(0, len(rest), 2):
                if rest[i] == 'else':
                    res += f'\nelse:\n'
                    res += '\n'.join([indent_str(self.resolve_node(x, cur_indent+2), cur_indent+2) for x in rest[i+1]])
                elif rest[i] == 'elseif':
                    res += f'\nelif {self.resolve_node(rest[i+1])}:\n'
                    res += '\n'.join([indent_str(self.resolve_node(x, cur_indent+2), cur_indent+2) for x in rest[i+2]])
            return res
        elif node[0] == 'loop':
            var, over, code = node[1], node[2], node[3]
            res = f'for {var} in {self.resolve_node(over)}:\n'
            res += '\n'.join([indent_str(self.resolve_node(x, cur_indent+2), cur_indent+2) for x in code])
            return res

        # VARIABLE ASSIGNMENT
        elif node[0] == 'var_assign':
            var = node[1]
            value = self.resolve_node(node[2])
            return f'{var} = {value}'

        # EXPRESSIONS
        elif node[0] == 'expr_op':
            op, left, right = node[1:]
            op = {
                '=': '==', '^': '**', '/': '//'
            }.get(op, op)
            if op == 'dm':
                return f'{CONST["roll"]}({self.resolve_node(left)})'
            elif op == 'ndm':
                return f'{CONST["roll"]}({self.resolve_node(left)}, {self.resolve_node(right)})'
            # elif op == '@':  # TODO only problem if both sides are ints. fix later
            else:  # all other operators
                return f'{self.resolve_node(left)} {op} {self.resolve_node(right)}'
        elif node[0] == 'unary':
            op, expr = node[1:]
            return f'{op}{self.resolve_node(expr)}'
        elif node[0] == 'hash':  # len
            return f'len({self.resolve_node(node[1])})'
        elif node[0] == 'seq':
            elems = list(map(str, map(self.resolve_node, node[1])))
            return f'{CONST["seq"]}([{", ".join(elems)}])' if elems else f'{CONST["seq"]}()'
        elif node[0] == 'range':
            l, r = node[1:]
            l, r = self.resolve_node(l), self.resolve_node(r)
            return f'{CONST["range"]}({l}, {r})'
        elif node[0] == 'call':
            func = node[1]
            args = ', '.join(map(self.resolve_node, node[2]))
            return f'{func}({args})'

# function
# result
# set
        else:
            assert False, f'Unknown node: {node}'

def cleanup_string(s):
    return s.replace('{', '').replace('}', '')

def indent_str(s, indent):
    return '\n'.join(' ' * indent + x for x in s.split('\n'))
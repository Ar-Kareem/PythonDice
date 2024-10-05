
from typing import Union

T_sn = tuple[Union[int, str, "T_sn"], ...]

CONST = {
    'output': 'output',
    'seq': 'Seq',
    'roll': 'roll',
    'range': 'myrange',
    'cast_decorator': '@anydice_casting()',
    'setter': lambda name, value: f'settings_set("{name}", "{value}")',
    'function library': ('absolute_X', 'X_contains_X', 'count_X_in_X', 'explode_X', 'highest_X_of_X', 'lowest_X_of_X', 'middle_X_of_X', 'highest_of_X_and_X', 'lowest_of_X_and_X', 'maximum_of_X', 'reverse_X', 'sort_X'),
}

class PythonResolver:
    def __init__(self, root):
        self.root: T_sn = root
        self.defined_functions: set[str] = set(CONST['function library'])
        self.user_defined_functions: list[str] = []

    def resolve(self):
        result = '\n'.join(map(self.resolve_node, self.root))
        return result

    def resolve_node(self, node, cur_indent=0):

        # Handle str_obj  |  str_obj which is str or concat_string(str_obj, str_obj) or strvar(str)
        if isinstance(node, str):
            return node
        elif node[0] == 'strvar':
            return '{' + node[1] + '}'
        elif node[0] == 'concat_string':
            res = self.resolve_node(node[1]) + self.resolve_node(node[2])
            return cleanup_string(res)

        elif node[0] == 'number':
            return node[1]
        elif node[0] == 'var':  # variable inside an expression
            return node[1]

        # OUTPUT:
        elif node[0] == 'output':
            params = self.resolve_node(node[1])
            return f'{CONST["output"]}({params})'
        elif node[0] == 'output_named':
            params = self.resolve_node(node[1])
            name = self.resolve_node(node[2])  # node[2] is str_obj
            return f'{CONST["output"]}({params}, named=f"{name}")'

        elif node[0] == 'set':
            name, value = node[1], node[2]
            name, value = self.resolve_node(name), self.resolve_node(value)
            return CONST['setter'](name, value)


        # FUNCTION:
        elif node[0] == 'function':
            nameargs, code = node[1][1:], node[2]
            name, args = [], []
            for x in nameargs:
                if isinstance(x, str):
                    name.append(x)
                else:
                    DATATYPES = {'s': 'Seq', 'n': 'int', 'd': 'RV'}
                    args.append(f'{x[1]}: {DATATYPES[x[2]]}')
                    name.append('X')
            name = '_'.join(name)
            self.defined_functions.add(name)
            self.user_defined_functions.append(name)
            res = CONST['cast_decorator'] + '\n'
            res += f'def {name}({", ".join(args)}):\n'
            res += '\n'.join([indent_str(self.resolve_node(x, cur_indent+2), cur_indent+2) for x in code])
            return res + '\n'
        elif node[0] == 'result':
            return f'return {self.resolve_node(node[1])}'

        # CONDITIONALS (IF / LOOP)
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
            nameargs = node[1]
            name, args = [], []
            for x in nameargs:
                if isinstance(x, str):
                    name.append(x)
                else:  # expression
                    args.append(str(self.resolve_node(x)))
                    name.append('X')
            name = '_'.join(name)
            assert name in self.defined_functions, f'Unknown function {name} not defined. Currently callable functions: ' + str(self.user_defined_functions)
            return f'{name}({", ".join(args)})' if args else f'{name}()'


        else:
            assert False, f'Unknown node: {node}'

def cleanup_string(s):
    return s.replace('{', '').replace('}', '')

def indent_str(s, indent):
    return '\n'.join(' ' * indent + x for x in s.split('\n'))
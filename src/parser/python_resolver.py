import logging
from typing import Union, Sequence


logger = logging.getLogger(__name__)


T_elem = Union[str, int, None, Sequence["T_elem"]]

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
        assert self._check_nested_str(root), f'Expected nested strings/numbers from yacc, got {root}'
        self.root: T_elem = root
        self.defined_functions: set[str] = set(CONST['function library'])
        self.user_defined_functions: list[str] = []

    def _check_nested_str(self, node):
        if node is None or isinstance(node, (int, str)):
            return True
        if isinstance(node, Sequence):
            return all(self._check_nested_str(x) for x in node)
        logging.error(f'Unexpected node: {node}')
        return False

    def resolve(self):
        result = '\n'.join(map(self.resolve_node, self.root))
        return result

    def resolve_node(self, node: T_elem, cur_indent=0) -> str:
        if node is None:
            return ''
        assert not isinstance(node, int), f'resovler error, not sure what to do with a number: {node}. All numbers should be a tuple ("number", int)'

        # Handle str_obj  |  str_obj which is str or concat_string(str_obj, str_obj) or strvar(str)
        if isinstance(node, str):
            return node
        elif node[0] == 'strvar':
            assert isinstance(node[1], str), f'Expected string, got {node[1]}'
            return '{' + node[1] + '}'
        elif node[0] == 'concat_string':
            res = self.resolve_node(node[1]) + self.resolve_node(node[2])
            return cleanup_string(res)

        elif node[0] == 'number':  # number in an expression
            assert isinstance(node[1], str), f'Expected str of a number, got {node[1]}  type: {type(node[1])}'
            return str(node[1])
        elif node[0] == 'var':  # variable inside an expression
            assert isinstance(node[1], str), f'Expected str of a variable, got {node[1]}'
            return node[1]
        elif node[0] == 'group':  # group inside an expression, node[1] is an expression
            return f'({self.resolve_node(node[1])})'

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
            nameargs, code = node[1], node[2]
            assert isinstance(nameargs, tuple) and nameargs[0] == 'funcname_def', f'Error in parsing fuction node: {node}'
            nameargs = nameargs[1:]
            name, args = [], []
            for x in nameargs:  # nameargs is a list of strings and expressions e.g. [attack 3d6 if crit 6d6 and double crit 12d6]
                if isinstance(x, str):
                    name.append(x)
                else:
                    assert isinstance(x, tuple) and x[0] == 'param', f'Error in parsing function node: {node}'
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
            assert isinstance(op, str), f'Unknown operator {op}'
            op = {'=': '==', '^': '**', '/': '//'}.get(op, op)
            if op == 'dm':
                return f'{CONST["roll"]}({self.resolve_node(left)})'
            elif op == 'ndm':
                return f'{CONST["roll"]}({self.resolve_node(left)}, {self.resolve_node(right)})'
            # elif op == '@':  # TODO only problem if both sides are ints. fix later
            else:  # all other operators
                return f'{self.resolve_node(left)} {op} {self.resolve_node(right)}'
        elif node[0] == 'unary':
            op, expr = node[1:]
            if op == '!':
                return f'~{self.resolve_node(expr)}'
            return f'{op}{self.resolve_node(expr)}'
        elif node[0] == 'hash':  # len
            return f'len({self.resolve_node(node[1])})'
        elif node[0] == 'seq':
            assert isinstance(node[1], list), f'Expected list of expressions, got {node[1]}'
            seq_class = CONST['seq']
            elems = ", ".join([self.resolve_node(x) for x in node[1]])
            return f'{seq_class}([{elems}])'
        elif node[0] == 'range':
            l, r = node[1:]
            l, r = self.resolve_node(l), self.resolve_node(r)
            return f'{CONST["range"]}({l}, {r})'
        elif node[0] == 'call':
            nameargs = node[1]
            assert isinstance(nameargs, list), f'Expected list of strings and expressions, got {nameargs}'
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

def cleanup_string(s: str):
    return s.replace('{', '').replace('}', '')

def indent_str(s: str, indent: int):
    return '\n'.join(' ' * indent + x for x in s.split('\n'))
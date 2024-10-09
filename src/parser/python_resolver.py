import logging

from .myparser import Node, NodeType


logger = logging.getLogger(__name__)


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
    def __init__(self, root: Node):
        assert self._check_nested_str(root), f'Expected nested strings/None/Node from yacc, got {root}'
        self.root = root
        self.defined_functions: set[str] = set(CONST['function library'])
        self.user_defined_functions: list[str] = []
        self.called_functions: set[str] = set()
        self.INDENT_LEVEL = 2

        self.NEWLINES_AFTER_IF = 1
        self.NEWLINES_AFTER_LOOP = 1
        self.NEWLINES_AFTER_FUNCTION = 1
        self.NEWLINES_AFTER_FILE = 1

    def _check_nested_str(self, node):
        if isinstance(node, Node):
            return all(x is None or isinstance(x, str) or self._check_nested_str(x) for x in node)
        logger.error(f'Unexpected node: {node} with children nodes {node.vals if node else ""}')
        return False

    def resolve(self):
        result = self.resolve_node(self.root) + '\n'*self.NEWLINES_AFTER_FILE
        # check if all functions are defined
        for f_name in self.called_functions:
            assert f_name in self.defined_functions, f'Unknown function {f_name} not defined. Currently callable functions: {self.user_defined_functions}'

        # remove multiple nearby newlines
        result = list(result.split('\n'))
        result = [x for i, x in enumerate(result) if i == 0 or x.strip() != '' or result[i-1].strip() != '']
        return '\n'.join(result)

    def _indent_resolve(self, node: 'Node|str') -> str:
        """Given a node, resolve it and indent it. node to indent: if/elif/else, loop, function"""
        return self._indent_str(self.resolve_node(node))

    def _indent_str(self, s: str):
        """Indent a string by self.indent_level spaces for each new line"""
        return '\n'.join(' '*self.INDENT_LEVEL + x for x in s.split('\n'))

    def resolve_node(self, node: 'Node|str') -> str:
        assert node is not None, 'Got None'
        assert not isinstance(node, str), f'resolver error, not sure what to do with a string: {node}. All strings should be a Node ("string", str|strvar...)'

        if node.type == NodeType.MULTILINE_CODE:
            return '\n'.join([self.resolve_node(x) for x in node]) if len(node) > 0 else 'pass'

        elif node.type == NodeType.STRING:  # Node of str or ("strvar", ...)
            return ''.join([x if isinstance(x, str) else self.resolve_node(x) for x in node])
        elif node.type == NodeType.STRVAR:
            assert isinstance(node.val, str), f'Expected string for strvar, got {node.val}'
            return '{' + node.val + '}'
        elif node.type == NodeType.NUMBER:  # number in an expression
            assert isinstance(node.val, str), f'Expected str of a number, got {node.val}  type: {type(node.val)}'
            return str(node.val)
        elif node.type == NodeType.VAR:  # variable inside an expression
            assert isinstance(node.val, str), f'Expected str of a variable, got {node.val}'
            return node.val
        elif node.type == NodeType.GROUP:  # group inside an expression, node.val is an expression
            return f'({self.resolve_node(node.val)})'

        # OUTPUT:
        elif node.type == NodeType.OUTPUT:
            params = self.resolve_node(node.val)
            return f'{CONST["output"]}({params})'
        elif node.type == NodeType.OUTPUT_NAMED:
            params, name = node
            params, name = self.resolve_node(params), self.resolve_node(name)
            return f'{CONST["output"]}({params}, named=f"{name}")'

        elif node.type == NodeType.SET:
            name, value = node
            name, value = self.resolve_node(name), self.resolve_node(value)
            return CONST['setter'](name, value)

        # FUNCTION:
        elif node.type == NodeType.FUNCTION:
            nameargs, code = node
            assert isinstance(nameargs, Node) and nameargs.type == NodeType.FUNCNAME_DEF, f'Error in parsing fuction node: {node}'
            func_name, func_args = [], []
            for x in nameargs:  # nameargs is a list of strings and expressions e.g. [attack 3d6 if crit 6d6 and double crit 12d6]
                assert isinstance(x, str) or (isinstance(x, Node) and x.type in (NodeType.PARAM, NodeType.PARAM_WITH_DTYPE)), f'Error in parsing function node: {node}'
                if isinstance(x, str):
                    func_name.append(x)
                elif x.type == NodeType.PARAM:
                    arg_name = x.val
                    func_args.append(f'{arg_name}')
                    func_name.append('X')
                else:
                    arg_name, arg_dtype = x
                    assert isinstance(arg_dtype, str), f'Expected string for arg_dtype, got {arg_dtype}'
                    arg_dtype = {'s': 'Seq', 'n': 'int', 'd': 'RV'}.get(arg_dtype, arg_dtype)
                    func_args.append(f'{arg_name}: {arg_dtype}')
                    func_name.append('X')
            func_name = '_'.join(func_name)
            self.defined_functions.add(func_name)
            self.user_defined_functions.append(func_name)
            func_decorator = CONST['cast_decorator']
            func_def = f'def {func_name}({", ".join(func_args)}):'
            func_code = self._indent_resolve(code)
            return f'{func_decorator}\n{func_def}\n{func_code}' + '\n'*self.NEWLINES_AFTER_FUNCTION
        elif node.type == NodeType.RESULT:
            return f'return {self.resolve_node(node.val)}'

        # CONDITIONALS IF
        elif node.type == NodeType.IF_ELIF_ELSE:
            res = []
            for block in node:  # list of Nodes ('if', cond, code)+, ('elif', cond, code)*, ('else', code)?  (+: 1+, *: 0+, ?: 0 or 1)
                assert isinstance(block, Node), f'Expected Node in conditionals, got {block}'
                if block.type == NodeType.IF:
                    expr, code = block
                    r = f'if {self.resolve_node(expr)}:\n{self._indent_resolve(code)}'
                elif block.type == NodeType.ELSEIF:
                    expr, code = block
                    r = f'elif {self.resolve_node(expr)}:\n{self._indent_resolve(code)}'
                elif block.type == NodeType.ELSE:
                    r = f'else:\n{self._indent_resolve(block.val)}'
                else:
                    assert False, f'Unknown block type: {block}'
                res.append(r)
            return '\n'.join(res) + '\n'*self.NEWLINES_AFTER_IF

        # LOOP
        elif node.type == NodeType.LOOP:
            var, over, code = node
            return f'for {var} in {self.resolve_node(over)}:\n{self._indent_resolve(code)}' + '\n'*self.NEWLINES_AFTER_LOOP

        # VARIABLE ASSIGNMENT
        elif node.type == NodeType.VAR_ASSIGN:
            var, val = node
            return f'{var} = {self.resolve_node(val)}'

        # EXPRESSIONS
        elif node.type == NodeType.EXPR_OP:
            op, left, right = node
            assert isinstance(op, str), f'Unknown operator {op}'
            op = {'=': '==', '^': '**', '/': '//'}.get(op, op)
            if op == 'dm':
                return f'{CONST["roll"]}({self.resolve_node(left)})'
            elif op == 'ndm':
                return f'{CONST["roll"]}({self.resolve_node(left)}, {self.resolve_node(right)})'
            # elif op == '@':  # TODO only problem if both sides are ints. fix later
            else:  # all other operators
                return f'{self.resolve_node(left)} {op} {self.resolve_node(right)}'
        elif node.type == NodeType.UNARY:
            op, expr = node
            if op == '!':
                return f'~{self.resolve_node(expr)}'
            return f'{op}{self.resolve_node(expr)}'
        elif node.type == NodeType.HASH:  # len
            return f'len({self.resolve_node(node.val)})'
        elif node.type == NodeType.SEQ:
            seq_class = CONST['seq']
            elems = ", ".join([self.resolve_node(x) for x in node])
            return f'{seq_class}([{elems}])'
        elif node.type == NodeType.RANGE:
            l, r = node
            l, r = self.resolve_node(l), self.resolve_node(r)
            return f'{CONST["range"]}({l}, {r})'
        elif node.type == NodeType.CALL:
            name, args = [], []
            for x in node:
                if isinstance(x, Node) and x.type == NodeType.CALL_EXPR:  # expression
                    args.append(self.resolve_node(x.val))
                    name.append('X')
                elif isinstance(x, str):
                    name.append(x)
                else:
                    assert False, f'Unknown node in call: {x}, parent: {node}'
            name = '_'.join(name)
            self.called_functions.add(name)
            return f'{name}({", ".join(args)})' if args else f'{name}()'

        else:
            assert False, f'Unknown node: {node}'

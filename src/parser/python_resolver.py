import logging
from typing import Union

from .myparser import Node, NodeType


logger = logging.getLogger(__name__)


CONST = {
  'output': 'output',
  'seq': 'get_seq',
  'roll': 'roll',
  'range': 'myrange',
  'func_decorator': '@anydice_casting()',  # with func depth limit
  'setter': lambda name, value: f'settings_set({name}, {value})',
  'function library': ('absolute_X', 'X_contains_X', 'count_X_in_X', 'explode_X', 'highest_X_of_X', 'lowest_X_of_X', 'middle_X_of_X', 'highest_of_X_and_X', 'lowest_of_X_and_X', 'maximum_of_X', 'reverse_X', 'sort_X', 'true_div_X_X'),
  'oplib': {'@': 'myMatmul', 'len': 'myLen', '~': 'myInvert', '&': 'myAnd', '|': 'myOr'},
}
_FUNCS_MAY_COLLIDE = set((CONST['output'], CONST['roll'], CONST['range'], 'max_func_depth', 'anydice_casting', 'settings_set'))


class PythonResolver:
    def __init__(self, root: Node, flags=None):
        assert self._check_nested_str(root), f'Expected nested strings/None/Node from yacc, got {root}'
        self.root = root
        self.reset_state()

        flags = flags or {}
        # this flag is for a very nasty behaviour in anydice where a functions variables are a temporary copy of the callers variables; see https://anydice.com/program/394f0 and https://anydice.com/program/394f1 for the ugly behaviour
        # handling this is very ugly, we pass around a dictionary of all the code's variables and copy it for each function call
        # this makes the output code look unpleasant as every variable is accessed as dict['VAR'] instead of just VAR.
        # If you plan on understanding this file then please ignore all compiler flags and assume they are all the default value as compiler flags are just edge-cases.
        self._COMPILER_FLAG_NON_LOCAL_SCOPE = flags.pop('COMPILER_FLAG_NON_LOCAL_SCOPE', False)
        # this flag is to support operators on ints: @, len, and ~.  These operators (on ints) are rarely used in actual code.
        self._COMPILER_FLAG_OPERATOR_ON_INT = flags.pop('COMPILER_FLAG_OPERATOR_ON_INT', False)
        # prepends all func defs and func calls with a string to prevent collisions with user-defined functions checked against _FUNCS_MAY_COLLIDE (resolving turns it on when _funclib_conflicted is True and resets resolving)
        self._COMPILER_FLAG_FUNC_LIB_CONFLICT = flags.pop('COMPILER_FLAG_FUNC_LIB_CONFLICT', False)
        # this flag is to check if functions are defined. otherwise [func] might crash at run time or [list] might call python's internal "list()" function
        self._COMPILER_FLAG_FUNC_EXIST_CHECK = flags.pop('COMPILER_FLAG_FUNC_EXIST_CHECK', True)

        assert not flags, f'Unknown flags: {flags}'

        self.INDENT_LEVEL = 2

        self.NEWLINES_AFTER_IF = 1
        self.NEWLINES_AFTER_LOOP = 1
        self.NEWLINES_AFTER_FUNCTION = 1
        self.NEWLINES_AFTER_FILE = 1

    def reset_state(self):
        self._defined_functions: set[str] = set(CONST['function library'])  # used for collision checking and error messages
        self._user__defined_functions: list[str] = []  # only used for error messages
        self._called_functions: set[str] = set()
        self._output_counter = 0
        self.result_text: Union[str, None] = None

    def _check_nested_str(self, node):
        if isinstance(node, Node):
            return all(x is None or isinstance(x, str) or self._check_nested_str(x) for x in node)
        logger.error(f'Unexpected node: {node} with children nodes {node.vals if node else ""}')
        return False

    def resolve(self):
        result = ''
        if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
            result += 'vars = {}\n\n'
        result += self.resolve_node(self.root) + '\n' * self.NEWLINES_AFTER_FILE
        # check if all functions are defined
        if self._COMPILER_FLAG_FUNC_EXIST_CHECK:
            for f_name in self._called_functions:
                assert f_name in self._defined_functions, f'Unknown function {f_name} not defined. Currently callable functions: {self._user__defined_functions}'
        assert self._output_counter > 0, 'No outputs made. Did you forget to call "output expr"?'

        if any(f in self._defined_functions for f in _FUNCS_MAY_COLLIDE):  # collision -> reset with flag (if another collision then crash)
            assert not self._COMPILER_FLAG_FUNC_LIB_CONFLICT, 'Function library conflict despite flag; this should not happen'
            self._COMPILER_FLAG_FUNC_LIB_CONFLICT = True
            self.reset_state()
            self.resolve()
            return

        # remove multiple nearby newlines
        result = list(result.split('\n'))
        result = [x for i, x in enumerate(result) if i == 0 or x.strip() != '' or result[i - 1].strip() != '']
        self.result_text = '\n'.join(result)

    def get_text(self):
        assert self.result_text is not None, 'No text generated. Call resolve() first'
        return self.result_text

    def _indent_resolve(self, node: Union['Node', 'str']) -> str:
        """Given a node, resolve it and indent it. node to indent: if/elif/else, loop, function"""
        return self._indent_str(self.resolve_node(node))

    def _indent_str(self, s: str):
        """Indent a string by self.indent_level spaces for each new line"""
        return '\n'.join(' ' * self.INDENT_LEVEL + x for x in s.split('\n'))

    def resolve_node(self, node: Union['Node', 'str']) -> str:  # noqa: C901
        assert node is not None, 'Got None'
        assert not isinstance(node, str), f'resolver error, not sure what to do with a string [{node}]. All strings should be a Node ("string", str|strvar...)'

        if node.type == NodeType.MULTILINE_CODE:
            return '\n'.join([self.resolve_node(x) for x in node]) if len(node) > 0 else 'pass'

        elif node.type == NodeType.STRING:  # Node of str or ("strvar", ...)
            str_list = []
            for x in node:
                if isinstance(x, str):
                    str_list.append(x.replace('{', '{{').replace('}', '}}'))  # escape curly braces
                else:
                    str_list.append(self.resolve_node(x))
            return 'f"' + ''.join(str_list) + '"'
        elif node.type == NodeType.STRVAR:
            assert isinstance(node.val, str), f'Expected string for strvar, got {node.val}'
            if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
                return "{vars['" + node.val + "']}"
            return '{' + node.val + '}'
        elif node.type == NodeType.NUMBER:  # number in an expression
            assert isinstance(node.val, str), f'Expected str of a number, got {node.val}  type: {type(node.val)}'
            return str(node.val)
        elif node.type == NodeType.NUMBER_DECIMAL:  # number in an expression
            val1, val2 = node
            assert isinstance(val1, str) and isinstance(val2, str), f'Expected str of a number, got {val1} and {val2}'
            return f'{val1}.{val2}'
        elif node.type == NodeType.VAR:  # variable inside an expression
            assert isinstance(node.val, str), f'Expected str of a variable, got {node.val}'
            if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
                return f"vars['{node.val}']"
            return node.val
        elif node.type == NodeType.GROUP:  # group inside an expression, node.val is an expression
            return f'({self.resolve_node(node.val)})'

        # OUTPUT:
        elif node.type == NodeType.OUTPUT:
            self._output_counter += 1
            params = self.resolve_node(node.val)
            return f'{CONST["output"]}({params})'
        elif node.type == NodeType.OUTPUT_NAMED:
            self._output_counter += 1
            params, name = node
            params, name = self.resolve_node(params), self.resolve_node(name)
            return f'{CONST["output"]}({params}, named={name})'

        elif node.type == NodeType.SET:
            name, value = node
            name, value = self.resolve_node(name), self.resolve_node(value)
            return CONST['setter'](name, value)

        # FUNCTION:
        elif node.type == NodeType.FUNCTION:
            nameargs, code = node
            assert isinstance(nameargs, Node) and nameargs.type == NodeType.FUNCNAME_DEF, f'Error in parsing fuction node: {node}'
            func_name, func_args, func_arg_names = [], [], []
            if self._COMPILER_FLAG_FUNC_LIB_CONFLICT:
                func_name.append('f')
            for x in nameargs:  # nameargs is a list of strings and expressions e.g. [attack 3d6 if crit 6d6 and double crit 12d6]
                assert isinstance(x, str) or (isinstance(x, Node) and x.type in (NodeType.PARAM, NodeType.PARAM_WITH_DTYPE)), f'Error in parsing function node: {node}'
                if isinstance(x, str):
                    func_name.append(x)
                elif x.type == NodeType.PARAM:
                    arg_name = x.val
                    func_args.append(arg_name)
                    func_arg_names.append(arg_name)
                    func_name.append('X')
                else:
                    arg_name, arg_dtype = x
                    assert isinstance(arg_dtype, str), f'Expected string for arg_dtype, got {arg_dtype}'
                    arg_dtype = {'s': 'T_S', 'n': 'T_N', 'd': 'T_D'}.get(arg_dtype, arg_dtype)
                    func_args.append(f'{arg_name}: {arg_dtype}')
                    func_arg_names.append(arg_name)
                    func_name.append('X')
            if has_dups(func_arg_names):
                fix_dups_in_args(func_args, func_arg_names)
            if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
                func_args.append('vars')
            func_name = '_'.join(func_name)
            self._defined_functions.add(func_name)
            self._user__defined_functions.append(func_name)
            func_decorator = CONST['func_decorator']
            func_def = f'def {func_name}({", ".join(func_args)}):'
            func_code = ''
            if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
                func_code += self._indent_str('vars = vars.copy(); ' + '; '.join([f'vars["{n}"] = {n}' for n in func_arg_names])) + '\n'
            func_code += self._indent_resolve(code)
            return f'{func_decorator}\n{func_def}\n{func_code}' + '\n' * self.NEWLINES_AFTER_FUNCTION
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
            return '\n'.join(res) + '\n' * self.NEWLINES_AFTER_IF

        # LOOP
        elif node.type == NodeType.LOOP:
            var, over, code = node
            res_header = f'for {var} in {self.resolve_node(over)}:'
            res_code = ''
            if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
                res_code += self._indent_str(f"vars['{var}'] = {var}") + '\n'  # I hate this but it must happen
            res_code += self._indent_resolve(code)
            return res_header + '\n' + res_code + '\n' * self.NEWLINES_AFTER_LOOP

        # VARIABLE ASSIGNMENT
        elif node.type == NodeType.VAR_ASSIGN:
            var, val = node
            if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
                return f"vars['{var}'] = {self.resolve_node(val)}"
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
            elif op == '@':
                if self._COMPILER_FLAG_OPERATOR_ON_INT:
                    return f'{CONST["oplib"]["@"]}({self.resolve_node(left)}, {self.resolve_node(right)})'
                return f'({self.resolve_node(left)} {op} {self.resolve_node(right)})'  # wrap in parentheses to take precedence over multiplication
            elif op == '&' or op == '|':
                if self._COMPILER_FLAG_OPERATOR_ON_INT:
                    return f'{CONST["oplib"][op]}({self.resolve_node(left)}, {self.resolve_node(right)})'
                return f'{self.resolve_node(left)} {op} {self.resolve_node(right)}'
            else:  # all other operators
                return f'{self.resolve_node(left)} {op} {self.resolve_node(right)}'
        elif node.type == NodeType.UNARY:
            op, expr = node
            if op == '!':
                if self._COMPILER_FLAG_OPERATOR_ON_INT:
                    return f'{CONST["oplib"]["~"]}({self.resolve_node(expr)})'
                return f'~{self.resolve_node(expr)}'
            return f'{op}{self.resolve_node(expr)}'
        elif node.type == NodeType.HASH:  # len
            if self._COMPILER_FLAG_OPERATOR_ON_INT:
                return f'{CONST["oplib"]["len"]}({self.resolve_node(node.val)})'
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
            if self._COMPILER_FLAG_FUNC_LIB_CONFLICT:
                name.append('f')
            for x in node:
                if isinstance(x, Node) and x.type == NodeType.CALL_EXPR:  # expression
                    args.append(self.resolve_node(x.val))
                    name.append('X')
                elif isinstance(x, str):
                    name.append(x)
                else:
                    assert False, f'Unknown node in call: {x}, parent: {node}'
            if self._COMPILER_FLAG_NON_LOCAL_SCOPE:
                args.append('vars')
            name = '_'.join(name)
            self._called_functions.add(name)
            return f'{name}({", ".join(args)})' if args else f'{name}()'

        else:
            assert False, f'Unknown node: {node}'


def has_dups(lst):
    return len(lst) != len(set(lst))


def fix_dups_in_args(func_args, func_arg_names):
    # rarely used, but if a function has duplicate arguments then we need to rename them
    N = len(func_args)
    for i in range(N - 1, -1, -1):  # only first is kept
        if func_arg_names.count(func_arg_names[i]) > 1:  # IS DUP
            func_args[i] = f'dummy{i}: ' + func_args[i].split(': ')[1]  # TODO remove colon so anydice_casting doesn't waste time looping over non-used args
            func_arg_names[i] = f'dummy{i}'

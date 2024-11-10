from enum import Enum
import logging
from typing import Union


from .ply.lex import lex
from .ply.yacc import yacc


logger = logging.getLogger(__name__)


# --- LEX Tokenizer

# states for the lexer
states = (
  ('instring', 'exclusive'),
)

# All tokens must be named in advance.
_reserved = ('output', 'function', 'loop', 'over', 'named', 'set', 'to', 'if', 'else', 'result')
reserved = {k: k.upper() for k in _reserved}

tokens = ['PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER',
          'COLON', 'LESS', 'GREATER', 'EQUALS', 'NOTEQUALS', 'AT',
          'HASH', 'OR', 'AND', 'EXCLAMATION',
          'DOT', 'DOUBLE_DOT', 'COMMA',
          'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
          'LOWERNAME', 'UPPERNAME', 'NUMBER',
          'D_OP',

          'INSTRING_ANY', 'INSTRING_VAR', 'INSTRING_NONVAR',
          ] + list(reserved.values())

# Ignored characters
t_ignore = ' \t'
t_instring_ignore = ''

# Token matching rules are written as regexs
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_POWER = r'\^'

t_COLON = r':'
t_LESS = r'<'
t_GREATER = r'>'
t_EQUALS = r'='
t_NOTEQUALS = r'!='
t_AT = r'\@'

t_HASH = r'\#'
t_OR = r'\|'
t_AND = r'&'
t_EXCLAMATION = r'!'

t_DOUBLE_DOT = r'\.\.'
t_DOT = r'\.'
t_COMMA = r','

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'

t_UPPERNAME = r'[A-Z_][A-Z_]*'


# A function can be used if there is an associated action.
# Write the matching regex in the docstring.
def t_ignore_COMMENT(t):
    r'\\(.|\n)*?\\'
    # comment is any number of chars (including new lines) begining with \ and ending with \
    pass


def t_NUMBER(t):
    r'\d+'
    # t.value = int(t.value)  # Convert the string to an integer
    return t


def t_LOWERNAME(t):
    r'[a-z][a-z]*'
    if t.value == 'd':  # Special case for 'd' operator
        t.type = 'D_OP'
    else:
        t.type = reserved.get(t.value, 'LOWERNAME')
    return t


def t_begin_instring(t):
    r'"'
    t.lexer.begin('instring')  # Starts 'instring' state


t_instring_INSTRING_VAR = r'\[[A-Z_]+\]'
strbody = r'[^\n"[]'
t_instring_INSTRING_NONVAR = rf'\[{strbody}*'
t_instring_INSTRING_ANY = rf'{strbody}+'


def t_instring_end(t):
    r'"'
    t.lexer.begin('INITIAL')        # Back to the initial state


# Ignored token with an action associated with it
def t_INITIAL_ignore_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')


# Error handler for illegal characters
def t_ANY_error(t):
    col_pos = find_column(t.lexer.lexdata, t.lexpos)
    t.lexer.LEX_ILLEGAL_CHARS.append((t.value[0], t.lexpos, t.lexer.lineno, col_pos))
    t.lexer.skip(1)


# EOF handling rule if "instring" state is active then illegal
def t_ANY_eof(t):
    if t.lexer.current_state() == 'instring':
        col_pos = find_column(t.lexer.lexdata, t.lexpos)
        t.lexer.LEX_ILLEGAL_CHARS.append(('Non-closed string', t.lexpos, t.lexer.lineno, col_pos))
    return None


def find_column(inp, lexpos):
    line_start = inp.rfind('\n', 0, lexpos) + 1
    return (lexpos - line_start) + 1


# --- Parser


# --- Parser


class NodeType(Enum):
    MULTILINE_CODE = 'multiline_code'
    SINGLE_CODE = 'single_code'
    OUTPUT = 'output'
    OUTPUT_NAMED = 'output_named'
    FUNCTION = 'function'
    LOOP = 'loop'
    SET = 'set'
    RESULT = 'result'
    IF_ELIF_ELSE = 'if_elif_else'
    IF = 'if'
    ELSE = 'else'
    ELSEIF = 'elseif'
    VAR_ASSIGN = 'var_assign'

    STRING = 'string'
    STRVAR = 'strvar'
    FUNCNAME_DEF = 'funcname_def'
    PARAM = 'param'
    PARAM_WITH_DTYPE = 'param_with_dtype'

    EXPR_OP = 'expr_op'
    UNARY = 'unary'
    HASH = 'hash'
    GROUP = 'group'
    NUMBER = 'number'
    NUMBER_DECIMAL = 'number_decimal'
    VAR = 'var'
    SEQ = 'seq'
    RANGE = 'range'
    CALL = 'call'
    CALL_EXPR = 'call_expr'


class Node:
    def __init__(self, nodetype: NodeType, *children: 'str|Node'):
        assert isinstance(nodetype, NodeType), f'Expected NodeType, got {nodetype}'
        self.type = nodetype
        self.vals = list(children)

    def with_child(self, child: 'str|Node'):  # for recursive parsing
        self.vals.append(child)
        return self

    def __len__(self):
        return len(self.vals)

    def __iter__(self):
        return iter(self.vals)

    @property
    def val(self) -> Union['str', 'Node']:
        assert len(self.vals) == 1, f'Expected 1 child, got {len(self.vals)}'
        return self.vals[0]

    def __repr__(self):
        return f'<Node {self.type}: {self.vals}>'


# YACC Parsing rules


start = 'multiline_code'


def p_multiline_code(p):
    '''
    multiline_code : single_code
            | multiline_code single_code
    '''
    if p[1].type == NodeType.MULTILINE_CODE:  # recursive case
        p[0] = p[1].with_child(p[2])
    else:  # base case
        p[0] = Node(NodeType.MULTILINE_CODE, p[1])


def p_multiline_code_empty(p):
    'multiline_code : empty'
    p[0] = Node(NodeType.MULTILINE_CODE)


def p_empty(p):
    'empty :'
    pass


def p_single_code(p):
    '''
    single_code : OUTPUT expression
                | OUTPUT expression NAMED string

                | FUNCTION COLON funcname_def LBRACE multiline_code RBRACE

                | LOOP var_name OVER expression LBRACE multiline_code RBRACE

                | RESULT COLON expression
                | SET string TO string
                | SET string TO expression
    '''
    if p[1] == 'output':
        if len(p) == 3:
            p[0] = Node(NodeType.OUTPUT, p[2])
        else:
            p[0] = Node(NodeType.OUTPUT_NAMED, p[2], p[4])
    elif p[1] == 'function':
        p[0] = Node(NodeType.FUNCTION, p[3], p[5])
    elif p[1] == 'loop':
        p[0] = Node(NodeType.LOOP, p[2], p[4], p[6])
    elif p[1] == 'set':
        p[0] = Node(NodeType.SET, p[2], p[4])
    elif p[1] == 'result':
        p[0] = Node(NodeType.RESULT, p[3])
    else:
        assert False, f'UNEXPECTED YACC PARSING single_code: {p}'


def p_single_code_if_elseif_else(p):
    '''
    single_code : if_expr
                | if_expr else_expr
                | if_expr elseif_expr
                | if_expr elseif_expr else_expr
    '''
    # each element of p is a list of Nodes, flatten to a single list
    nodes = [x for sublist in p[1:] for x in sublist]
    p[0] = Node(NodeType.IF_ELIF_ELSE, *nodes)


def p_if(p):
    '''
    if_expr : IF expression LBRACE multiline_code RBRACE
    '''
    p[0] = [Node(NodeType.IF, p[2], p[4])]


def p_else(p):
    '''
    else_expr : ELSE LBRACE multiline_code RBRACE
    '''
    p[0] = [Node(NodeType.ELSE, p[3])]


def p_elif(p):
    '''
    elseif_expr :  ELSE IF expression LBRACE multiline_code RBRACE
            | elseif_expr ELSE IF expression LBRACE multiline_code RBRACE
    '''
    # elseif_expr has N nodes, where N is the number of elseif blocks
    if isinstance(p[1], list):  # recursive case
        p[0] = [*p[1], Node(NodeType.ELSEIF, p[4], p[6])]
    else:  # base case
        p[0] = [Node(NodeType.ELSEIF, p[3], p[5])]


def p_var_assign(p):
    '''
    single_code : var_name COLON expression
    '''
    p[0] = Node(NodeType.VAR_ASSIGN, p[1], p[3])


def p_var_name(p):
    '''
    var_name : UPPERNAME
    '''
    p[0] = p[1]


def p_string_instring(p):
    '''
    string : INSTRING_ANY
           | INSTRING_NONVAR
           | string INSTRING_ANY
           | string INSTRING_NONVAR
    '''
    assert (len(p) in (2, 3)), f'UNEXPECTED YACC PARSING string: {len(p)}, {p}'
    if isinstance(p[1], Node):  # recursive case
        p[0] = p[1].with_child(p[2])
    else:  # base case
        p[0] = Node(NodeType.STRING, p[1])


def p_strvar_instring(p):
    '''
    string : INSTRING_VAR
            | string INSTRING_VAR
    '''
    assert (len(p) in (2, 3)), f'UNEXPECTED YACC PARSING strvar_instring: {len(p)}, {p}'
    if isinstance(p[1], Node):  # recursive case
        var = Node(NodeType.STRVAR, p[2][1:-1])
        p[0] = p[1].with_child(var)
    else:  # base case
        var = Node(NodeType.STRVAR, p[1][1:-1])
        p[0] = Node(NodeType.STRING, var)


def p_funcname_def(p):
    '''
    funcname_def : LOWERNAME
                | OUTPUT
                | FUNCTION
                | LOOP
                | OVER
                | NAMED
                | SET
                | TO
                | IF
                | ELSE
                | RESULT
                |  funcname_def LOWERNAME
                | funcname_def OUTPUT
                | funcname_def FUNCTION
                | funcname_def LOOP
                | funcname_def OVER
                | funcname_def NAMED
                | funcname_def SET
                | funcname_def TO
                | funcname_def IF
                | funcname_def ELSE
                | funcname_def RESULT
    '''
    if isinstance(p[1], Node):  # recursive case
        p[0] = p[1].with_child(p[2])
    else:  # base case
        p[0] = Node(NodeType.FUNCNAME_DEF, p[1])


def p_funcname_def_impossibletocall(p):
    '''
    funcname_def :
                | D_OP
                | funcname_def D_OP
    '''
    # Good luck calling a function with " d " in the name. It's impossible
    # If a function has this in the name then it's impossible to call because a d is evaluated into an expression
    # however, if a function with this name IS included BUT never called then the code should execute fine. Thus this rule is added
    # SAME AS ABOVE
    if isinstance(p[1], Node):  # recursive case
        p[0] = p[1].with_child(p[2])
    else:  # base case
        p[0] = Node(NodeType.FUNCNAME_DEF, p[1])


def p_funcname_def_param(p):
    '''
    funcname_def : var_name
                |  var_name COLON D_OP
                |  var_name COLON LOWERNAME
                |  funcname_def var_name
                |  funcname_def var_name COLON D_OP
                |  funcname_def var_name COLON LOWERNAME
    '''
    if isinstance(p[1], Node):  # recursive case
        if len(p) == 3:  # var_name
            param = Node(NodeType.PARAM, p[2])
        else:  # var_name COLON dtype
            param = Node(NodeType.PARAM_WITH_DTYPE, p[2], p[4])
        p[0] = p[1].with_child(param)
    else:  # base case
        if len(p) == 2:  # var_name
            param = Node(NodeType.PARAM, p[1])
        else:  # var_name COLON dtype
            param = Node(NodeType.PARAM_WITH_DTYPE, p[1], p[3])
        p[0] = Node(NodeType.FUNCNAME_DEF, param)


# Precedence rules to handle associativity and precedence of operators
precedence = (
  # from docs: "Boolean operations have a lower precedence than all conditions, except for Not, which is a unary operation. "
  ('left', 'OR'),            # OR operator (lowest precedence)
  ('left', 'AND'),           # AND operator (higher precedence than OR)
  ('left', 'LESS', 'GREATER', 'EQUALS', 'NOTEQUALS'),  # Comparison operators
  ('left', 'PLUS', 'MINUS'),
  ('left', 'TIMES', 'DIVIDE'),
  ('left', 'POWER'),
  ('left', 'AT'),  # Assuming @ is left-associative
  ('left', 'D_OP'),  # 'd' operator must come after other operators
  ('right', 'HASH_OP'),  # 'HASH' (unary #) operator precedence
  ('right', 'EXCLAMATION'),  # Unary NOT operator (!) precedence
  ('right', 'UMINUS', 'UPLUS'),  # Unary minus and plus have the highest precedence
  ('left', 'DOT'),  # Decimal point
)


# Parsing rules
def p_expression_binop(p):
    '''
    expression : expression PLUS expression
               | expression MINUS expression
               | expression TIMES expression
               | expression DIVIDE expression
               | expression POWER expression
               | expression AT expression
               | expression AND expression
               | expression OR expression
    '''
    p[0] = Node(NodeType.EXPR_OP, p[2], p[1], p[3])


def p_expression_dop(p):
    '''
    expression : term D_OP term %prec D_OP
               | D_OP term %prec D_OP
    '''
    if len(p) == 4:
        p[0] = Node(NodeType.EXPR_OP, 'ndm', p[1], p[3])  # case: n d m
    else:
        p[0] = Node(NodeType.EXPR_OP, 'dm', p[2], 'DUMMY VAL')  # case: d m


def p_expression_comparison(p):
    '''
    expression : expression LESS expression
               | expression GREATER expression
               | expression EQUALS expression
               | expression NOTEQUALS expression
               | expression LESS EQUALS expression
               | expression GREATER EQUALS expression
    '''
    if len(p) == 4:
        p[0] = Node(NodeType.EXPR_OP, p[2], p[1], p[3])
    elif len(p) == 5:  # <=, >=, !=
        p[0] = Node(NodeType.EXPR_OP, p[2] + p[3], p[1], p[4])


def p_expression_term(p):
    '''
    expression : term
    '''
    p[0] = p[1]


def p_term_unary(p):
    '''
    term : PLUS term %prec UPLUS
            | MINUS term %prec UMINUS
            | EXCLAMATION term %prec EXCLAMATION
    '''
    p[0] = Node(NodeType.UNARY, p[1], p[2])


def p_term_hash(p):
    '''
    term : HASH term %prec HASH_OP
    '''
    p[0] = Node(NodeType.HASH, p[2])


def p_term_grouped(p):
    '''
    term : LPAREN expression RPAREN
    '''
    p[0] = Node(NodeType.GROUP, p[2])


def p_term_number(p):
    '''
    term : NUMBER
    '''
    p[0] = Node(NodeType.NUMBER, p[1])


def p_term_number_decimal(p):
    '''
    term : NUMBER DOT NUMBER
    '''
    p[0] = Node(NodeType.NUMBER_DECIMAL, p[1], p[3])


def p_term_name(p):
    '''
    term : var_name
    '''
    p[0] = Node(NodeType.VAR, p[1])


# Rule for seqs  { ... }

def p_term_seq(p):
    '''
    term : LBRACE RBRACE
         | LBRACE elements RBRACE
    '''
    if isinstance(p[2], Node):  # p[2] is a SEQ node
        p[0] = p[2]
    else:
        p[0] = Node(NodeType.SEQ)  # Empty seq


def p_elements(p):
    '''
    elements : elements COMMA element
             | element
    '''
    if len(p) == 4:  # recursive case
        p[0] = p[1].with_child(p[3])
    else:
        p[0] = Node(NodeType.SEQ, p[1])


def p_element(p):
    '''
    element : expression
            | range
    '''
    p[0] = p[1]


def p_range(p):
    '''
    range : expression DOUBLE_DOT expression
    '''
    p[0] = Node(NodeType.RANGE, p[1], p[3])


def p_str_element(p):
    '''
    term : string
    '''
    p[0] = p[1]


# Rule for function calls [ ... ]
def p_term_call(p):
    '''
    term : LBRACKET call_elements RBRACKET
    '''
    p[0] = p[2]  # call_elements is a CALL node


def p_call_elements(p):
    '''
    call_elements : LOWERNAME
                | OUTPUT
                | FUNCTION
                | LOOP
                | OVER
                | NAMED
                | SET
                | TO
                | IF
                | ELSE
                | RESULT
                | call_elements LOWERNAME
                | call_elements OUTPUT
                | call_elements FUNCTION
                | call_elements LOOP
                | call_elements OVER
                | call_elements NAMED
                | call_elements SET
                | call_elements TO
                | call_elements IF
                | call_elements ELSE
                | call_elements RESULT
    '''
    if isinstance(p[1], Node):  # recursive case
        p[0] = p[1].with_child(p[2])
    else:
        p[0] = Node(NodeType.CALL, p[1])


def p_call_elements_expr(p):
    '''
    call_elements : expression
                | call_elements expression
    '''
    if p[1].type == NodeType.CALL:  # recursive case
        wrapped = Node(NodeType.CALL_EXPR, p[2])
        p[0] = p[1].with_child(wrapped)
    else:
        wrapped = Node(NodeType.CALL_EXPR, p[1])
        p[0] = Node(NodeType.CALL, wrapped)


def p_error(p):
    if not p:
        logger.error('Syntax error BUT NONE')
        return
    col = find_column(p.lexer.lexdata, p.lexpos)
    p.lexer.YACC_ILLEGALs.append((p.value, p.lexpos, p.lineno, col))


# BUILD

def build_lex_yacc(debug=False):
    lexer = lex(debug=debug)
    yaccer = yacc(debug=debug)
    return lexer, yaccer

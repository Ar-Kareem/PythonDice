from .ply.lex import lex
from .ply.yacc import yacc

# --- Tokenizer

# All tokens must be named in advance.

states = (
    ('instring','exclusive'),
)

reserved = ('output','function','loop','over','named','set','if','else','result')
reserved = {k: k.upper() for k in reserved}

tokens = [ 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER',
            'COLON', 'LESS', 'GREATER', 'EQUALS', 'NOTEQUALS', 'AT', 
            'HASH', 'OR', 'AND',
            'DOT', 'COMMA', 
            'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
            'LOWERNAME', 'UPPERNAME', 'NUMBER', 
            'D_OP',

            'INSTRING_ANY', 'INSTRING_VAR', 'INSTRING_NONVAR', 
            ] + list(reserved.values())

# Ignored characters
t_ignore = ' \t\n'
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
    t.value = int(t.value)
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
    t.lexer.begin('instring')             # Starts 'instring' state

t_instring_INSTRING_VAR = r'\[[A-Z]+\]'
t_instring_INSTRING_NONVAR = r'\[[^"]*+'
t_instring_INSTRING_ANY = r'[^"[]+'

def t_instring_end(t):
    r'"'
    t.lexer.begin('INITIAL')        # Back to the initial state



# Ignored token with an action associated with it
def t_ANY_ignore_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')

# Error handler for illegal characters
ILLEGAL_CHARS = []
def t_ANY_error(t):
    print(f'Illegal character {t.value[0]!r}')
    ILLEGAL_CHARS.append(t.value[0])
    t.lexer.skip(1)

# Build the lexer object
lexer = lex()








# --- Parser
# -----------------------------------------------------------------------------
#
#   base       : OUTPUT expression
#              | OUTPUT expression NAMED string
#
#   string     : string INSTRING_ANY
#              | string INSTRING_VAR
#              | string INSTRING_NONVAR
#              | INSTRING_ANY
#              | INSTRING_VAR
#              | INSTRING_NONVAR
#
#   expression : term PLUS term
#              | term MINUS term
#              | term
#
#   term       : factor TIMES factor
#              | factor DIVIDE factor
#              | factor
#
#   factor     : NUMBER
#              | NAME
#              | PLUS factor
#              | MINUS factor
#              | LPAREN expression RPAREN
#
# -----------------------------------------------------------------------------

def p_start(p):
    '''
    start : outercode
    '''
    p[0] = p[1]

def p_multi_outercode(p):
    '''
    outercode : outercode outercode
    '''
    if p[1][0] == 'multi':
        left = p[1][1:]
    else:
        left = [p[1]]
    if p[2][0] == 'multi':
        right = p[2][1:]
    else:
        right = [p[2]]
    p[0] = ('multi', *left, *right)

def p_outercode_ignore(p):
    '''
    outercode : outercode ignored_tokens
    '''
    p[0] = p[1]

def p_outercode(p):
    '''
    outercode : OUTPUT expression
        |  OUTPUT expression NAMED string

        |  FUNCTION COLON funcname_def LBRACE outercode RBRACE

        |  LOOP var_name OVER expression LBRACE outercode RBRACE

        |  IF expression LBRACE outercode RBRACE
        |  IF expression LBRACE outercode RBRACE ELSE LBRACE outercode RBRACE
        |  IF expression LBRACE outercode RBRACE ELSEIF
        |  IF expression LBRACE outercode RBRACE ELSEIF ELSE LBRACE outercode RBRACE

        |  RESULT COLON expression
    '''
    if p[1] == 'output':
        if len(p) == 3:
            p[0] = ('output', p[2])
        else:
            p[0] = ('output_named', p[2], p[4])
    elif p[1] == 'function':
        p[0] = ('function', p[3], p[5])
    elif p[1] == 'loop':
        code = None if len(p) == 7 else p[6]
        p[0] = ('loop', p[2], p[4], code)
    elif p[1] == 'if':
        if_expr_code = ('if', p[2], p[4])
        if len(p) == 6:
            p[0] = if_expr_code
        elif len(p) == 10:
            p[0] = (*if_expr_code, 'else', p[8])
        elif len(p) == 7:
            p[0] = (*if_expr_code, *p[6])
        elif len(p) == 11:
            p[0] = (*if_expr_code, *p[6], 'else', p[9])
        else:
            assert False, f'{len(p)}, {p}'
    elif len(p) == 4:
        assert p[1] == 'result', 'what does this mean? ' + str(p[1])
        p[0] = ('result', p[3])
    elif len(p) == 2:
        p[0] = p[1]
    else:
        assert False, f'{len(p)}, {p}'

def p_outercode_elif(p):
    '''
    ELSEIF :  ELSE IF expression LBRACE outercode RBRACE
            | ELSEIF ELSE IF expression LBRACE outercode RBRACE
    '''
    if p[1] == 'else':
        p[0] = ('elseif', p[3], p[5])
    else:
        p[0] = (*p[1], p[4], p[6])

def p_var_assign(p):
    '''
    outercode : var_name COLON expression
    '''
    p[0] = ('var_assign', p[1], p[3])



def p_var_name(p):
    '''
    var_name : UPPERNAME
    '''
    p[0] = p[1]

def p_string_instring(p):
    '''
    string : INSTRING_ANY
           | strvar
           | INSTRING_NONVAR
           | string INSTRING_ANY
           | string strvar
           | string INSTRING_NONVAR
    '''
    if len(p) == 3:
        p[0] = ('concat_string', p[1], p[2])
    else:
        p[0] = ('string', p[1])
def p_strvar_instring(p):
    '''
    strvar : INSTRING_VAR
    '''
    p[0] = ('strvar', p[1][1:-1])

def p_funcname_def(p):
    '''
    funcname_def : LOWERNAME
                |  funcname_def LOWERNAME
                | OUTPUT
                | FUNCTION
                | LOOP
                | OVER
                | NAMED
                | SET
                | IF
                | ELSE
                | RESULT
                | funcname_def OUTPUT
                | funcname_def FUNCTION
                | funcname_def LOOP
                | funcname_def OVER
                | funcname_def NAMED
                | funcname_def SET
                | funcname_def IF
                | funcname_def ELSE
                | funcname_def RESULT
    '''
    if len(p) == 2:
        p[0] = ('funcname_def', p[1])
    elif len(p) == 3:
        p[0] = (*p[1], p[2])
    else:
        # p[0] = (*p[1], ('param', p[2], p[4]))
        assert False, f'{len(p)}, {p}'
def p_funcname_def_param(p):
    '''
    funcname_def : var_name
                |  var_name COLON D_OP 
                |  var_name COLON LOWERNAME 
                |  funcname_def var_name
                |  funcname_def var_name COLON D_OP 
                |  funcname_def var_name COLON LOWERNAME 
    '''
    if isinstance(p[1], tuple):  # recursive case
        if len(p) == 3:
            param = ('param', p[2])
        else:
            param = ('param', p[2], p[4])
        p[0] = (*p[1], param)
    else:  # base case
        if len(p) == 2:
            p[0] = ('funcname_def', p[1])
        else:
            p[0] = ('funcname_def', p[1], p[3])

# Precedence rules to handle associativity and precedence of operators
precedence = (
    ('left', 'OR'),            # OR operator (lowest precedence)
    ('left', 'AND'),           # AND operator (higher precedence than OR)
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('left', 'POWER'),
    ('left', 'AT'),  # Assuming @ is left-associative
    ('left', 'D_OP'),  # 'd' operator must come after other operators
    ('right', 'HASH_OP'),  # 'HASH' (unary #) operator precedence
    ('right', 'UMINUS', 'UPLUS'),  # Unary minus and plus have the highest precedence
    ('left', 'LESS', 'GREATER', 'EQUALS', 'NOTEQUALS'),  # Comparison operators
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
    p[0] = ('expr_op', p[2], p[1], p[3])
def p_expression_dop(p):
    '''
    expression : term D_OP term %prec D_OP
               | D_OP term %prec D_OP
    '''
    if len(p) == 4:
        p[0] = ('expr_op', 'dm', p[1], p[3])  # case: n d m
    else:
        p[0] = ('expr_op', 'ndm', p[2])  # case: d m
def p_expression_comparison(p):
    '''
    expression : expression LESS expression
               | expression GREATER expression
               | expression EQUALS expression
               | expression NOTEQUALS expression
               | expression LESS EQUALS expression
               | expression GREATER EQUALS expression
    '''
    p[0] = ('expr_op', p[2], p[1], p[3])

def p_expression_term(p):
    '''
    expression : term
    '''
    p[0] = p[1]

def p_term_unary(p):
    '''
    term : PLUS term %prec UPLUS
         | MINUS term %prec UMINUS
    '''
    p[0] = ('unary', p[1], p[2])
def p_term_hash(p):
    '''
    term : HASH term %prec HASH_OP
    '''
    p[0] = ('hash', p[2])

def p_term_grouped(p):
    '''
    term : LPAREN expression RPAREN
    '''
    p[0] = p[2]

def p_term_number(p):
    '''
    term : NUMBER
    '''
    p[0] = ('number', p[1])
def p_term_name(p):
    '''
    term : var_name
    '''
    p[0] = ('var', p[1])


# Rule for seqs  { ... }
def p_term_seq(p):
    '''
    term : LBRACE RBRACE
         | LBRACE elements RBRACE
    '''
    if len(p) == 3:
        p[0] = ('seq', [])  # Empty seq
    else:
        p[0] = ('seq', p[2])  # Non-empty seq
def p_elements(p):
    '''
    elements : elements COMMA element
             | element
    '''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]  # Append the new element
    else:
        p[0] = [p[1]]  # Single element in the set
def p_element(p):
    '''
    element : expression
            | range
    '''
    p[0] = p[1]
def p_range(p):
    '''
    range : expression DOT DOT expression
    '''
    p[0] = ('range', p[1], p[4])  # p[1] is expression1, p[4] is expression2
# Rule for function calls [ ... ]
def p_term_call(p):
    '''
    term : LBRACKET call_elements RBRACKET
    '''
    p[0] = ('call', p[2])  # Represent the CALL operation

def p_call_elements(p):
    '''
    call_elements : LOWERNAME
                | expression
                | call_elements LOWERNAME
                | call_elements expression

                | D_OP
                | OUTPUT
                | FUNCTION
                | LOOP
                | OVER
                | NAMED
                | SET
                | IF
                | ELSE
                | RESULT
                | call_elements D_OP
                | call_elements OUTPUT
                | call_elements FUNCTION
                | call_elements LOOP
                | call_elements OVER
                | call_elements NAMED
                | call_elements SET
                | call_elements IF
                | call_elements ELSE
                | call_elements RESULT
    '''
    if len(p) == 3:  # Either LOWERNAME or expression
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]  # Single element



def p_error(p):
    print(f'Syntax error at {p.value!r}')

def p_ignored_tokens(p):
    '''ignored_tokens : SET'''

#     # No action is taken for ignored tokens; simply return nothing or None.
#     pass

# Build the parser
yacc_parser = yacc()
print('yacc_parser ready')

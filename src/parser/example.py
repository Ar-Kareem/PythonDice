from .ply.lex import lex
from .ply.yacc import yacc

# --- Tokenizer

# All tokens must be named in advance.

states = (
    ('instring','exclusive'),
)

reserved = ('output','function','loop','named','set','if','else','result')
reserved = {k: k.upper() for k in reserved}

tokens = [ 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER',
            'COLON', 'LESS', 'GREATER', 'EQUALS', 'NOTEQUALS', 'AT', 
            'COMMENT', 'HASH', 'OR', 'AND', 'EXCLAMATION',
            'PERIOD', 'COMMA', 'UNDERSCORE', 
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
t_EXCLAMATION = r'!'

t_PERIOD = r'\.'
t_COMMA = r','
t_UNDERSCORE = r'_'

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'

t_UPPERNAME = r'[A-Z][A-Z]*'

# A function can be used if there is an associated action.
# Write the matching regex in the docstring.
def t_COMMENT(t):
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
    start : main
        |  start main
        |  start ignored_tokens
    '''
    if len(p) == 2:
        p[0] = (p[1], )
    else:
        p[0] = (*p[1], p[2])

def p_main_expression(p):
    '''
    main : OUTPUT expression
        |  OUTPUT expression NAMED string

        |  FUNCTION COLON funcname_def LBRACE RBRACE
        |  FUNCTION COLON funcname_def LBRACE funccode RBRACE

        | code
    '''
    if p[1] == 'output':
        if len(p) == 3:
            p[0] = ('output', p[2])
        else:
            p[0] = ('output_named', p[2], p[4])
    elif p[1] == 'function':
        p[0] = ('function', p[3])
    elif len(p) == 2:
        p[0] = p[1]

def p_func_code(p):
    '''
    funccode : RESULT COLON expression
            |  code
            |  funccode RESULT COLON expression
            |  funccode code
    '''
    if len(p) == 2:
        p[0] = ('funccode', p[1])
    elif len(p) == 3:
        p[0] = ('funccode', *p[1], p[2])
    elif len(p) == 4:
        assert p[1] == 'result', 'what does this mean? ' + str(p[1])
        result = ('result', p[3])
        p[0] = ('funccode', *p[1], result)
    else:
        assert p[2] == 'result', 'what does this mean? ' + str(p[2])
        result = ('result', p[4])
        p[0] = ('funccode', *p[1], result)


def p_var_name(p):
    '''
    var_name : UPPERNAME
                    | UNDERSCORE
                    | var_name UNDERSCORE
                    | var_name UPPERNAME
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2]

def p_var_assign(p):
    '''
    code : var_name COLON expression
    '''
    p[0] = ('var_assign', p[1], p[3])

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
            |  funcname_def var_name COLON LOWERNAME 
    '''
    if len(p) == 2:
        p[0] = ('funcname_def', p[1])
    elif len(p) == 3:
        p[0] = (*p[1], p[2])
    else:
        p[0] = (*p[1], ('param', p[2], p[4]))


# Precedence rules to handle associativity and precedence of operators
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('left', 'POWER'),
    ('left', 'AT'),  # Assuming @ is left-associative
    ('left', 'D_OP'),  # 'd' operator must come after other operators
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
    '''
    p[0] = ('expr_op', p[2], p[1], p[3])
def p_expression_dop(p):
    '''
    expression : term D_OP term %prec D_OP
               | D_OP term %prec D_OP
    '''
    if len(p) == 4:
        p[0] = ('expr_op', p[1], p[3])  # case: n d m
    else:
        p[0] = ('expr_op', p[2])  # case: d m
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
    elements : elements COMMA expression
             | expression
    '''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]  # Append the new element
    else:
        p[0] = [p[1]]  # Single element in the seq
def p_term_call(p):
    '''
    term : LBRACKET call_elements RBRACKET
    '''
    p[0] = ('call', p[2])  # Represent the CALL operation

def p_call_elements(p):
    '''
    call_elements : call_elements LOWERNAME
                  | call_elements expression
                  | LOWERNAME
                  | expression
    '''
    if len(p) == 3:  # Either LOWERNAME or expression
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]  # Single element



def p_error(p):
    print(f'Syntax error at {p.value!r}')

def p_ignored_tokens(p):
    '''
    ignored_tokens : LOOP
            | SET
            | IF
            | ELSE

            | COMMENT
            | HASH
            | OR
            | AND
            | EXCLAMATION
            | PERIOD
'''

#     # No action is taken for ignored tokens; simply return nothing or None.
#     pass

# Build the parser
yacc_parser = yacc()
print('yacc_parser ready')
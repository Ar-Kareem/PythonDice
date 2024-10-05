from .ply.lex import lex
from .ply.yacc import yacc

# --- Tokenizer

# All tokens must be named in advance.

states = (
    ('instring','exclusive'),
)

reserved = ('output','function','loop','named','set','if','else')
reserved = {k: k.upper() for k in reserved}

tokens = [ 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER',
            'COLON', 'LESS', 'GREATER', 'EQUALS', 'NOTEQUALS', 'AT', 
            'COMMENT', 'HASH', 'OR', 'AND', 'EXCLAMATION',
            'PERIOD', 'COMMA', 'UNDERSCORE', 
            'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
            'LOWERNAME', 'UPPERNAME', 'NUMBER', 
            
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

def p_base_output_expr(p):
    '''
    base : main
        |  base main
        |  base ignored_tokens
    '''
    if len(p) == 2:
        p[0] = (p[1], )
    else:
        p[0] = (*p[1], p[2])

def p_main_expression(p):
    '''
    main : OUTPUT expression
        |  OUTPUT expression NAMED string
        |  FUNCTION LBRACE expression RBRACE
    '''
    if len(p) == 3:
        p[0] = ('output', p[2])
    elif len(p) == 3 and p[1] == 'function':
        p[0] = ('function', p[3])
    else:
        p[0] = ('output_named', p[2], p[4])

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

def p_expression_term_binop(p):
    '''
    expression : term PLUS term
               | term MINUS term
    '''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expression_term(p):
    '''
    expression : term
    '''
    p[0] = p[1]

def p_term_factor_binop(p):
    '''
    term : factor TIMES factor
         | factor DIVIDE factor
    '''
    p[0] = ('binop', p[2], p[1], p[3])

def p_term_factor(p):
    '''
    term : factor
    '''
    p[0] = p[1]

def p_factor_number(p):
    '''
    factor : NUMBER
    '''
    p[0] = ('number', p[1])

# def p_factor_name(p):
#     '''
#     factor : NAME
#     '''
#     p[0] = ('name', p[1])

def p_factor_unary(p):
    '''
    factor : PLUS factor
           | MINUS factor
    '''
    p[0] = ('unary', p[1], p[2])

def p_factor_grouped(p):
    '''
    factor : LPAREN expression RPAREN
    '''
    p[0] = ('grouped', p[2])

def p_error(p):
    print(f'Syntax error at {p.value!r}')

def p_ignored_tokens(p):
    '''
    ignored_tokens : FUNCTION
            | LOOP
            | NAMED
            | SET
            | IF
            | ELSE

            | POWER

            | COLON
            | LESS
            | GREATER
            | EQUALS
            | NOTEQUALS
            | AT

            | COMMENT
            | HASH
            | OR
            | AND
            | EXCLAMATION
            | PERIOD
            | COMMA
            | UNDERSCORE
            
            | LBRACE
            | RBRACE
            | LBRACKET
            | RBRACKET
            | LOWERNAME
            | UPPERNAME
'''

#     # No action is taken for ignored tokens; simply return nothing or None.
#     pass

# Build the parser
yacc_parser = yacc()
print('yacc_parser ready')
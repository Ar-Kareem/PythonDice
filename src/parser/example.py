# -----------------------------------------------------------------------------
# example.py
#
# Example of using PLY To parse the following simple grammar.
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

from .ply.lex import lex
from .ply.yacc import yacc

# --- Tokenizer

# All tokens must be named in advance.

states = (
    ('instring','exclusive'),
)

reserved = {
    'OUTPUT': 'output',
    'FUNCTION': 'function',
    'LOOP': 'loop',
    'NAMED': 'named',
    'SET': 'set',
    'IF': 'if',
    'ELSE': 'else',
}
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
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_LOWERNAME(t):
    r'[a-z][a-z]*'
    t.type = reserved.get(t.value, 'LOWERNAME')
    return t

def t_COMMENT(t):
    r'\\.*\\'
    pass



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
def t_ANY_error(t):
    print(f'Illegal character {t.value[0]!r}')
    t.lexer.skip(1)

# Build the lexer object
lexer = lex()
    
# --- Parser

# # Write functions for each grammar rule which is
# # specified in the docstring.
# def p_expression(p):
#     '''
#     expression : term PLUS term
#                | term MINUS term
#     '''
#     # p is a sequence that represents rule contents.
#     #
#     # expression : term PLUS term
#     #   p[0]     : p[1] p[2] p[3]
#     # 
#     p[0] = ('binop', p[2], p[1], p[3])

# def p_expression_term(p):
#     '''
#     expression : term
#     '''
#     p[0] = p[1]

# def p_term(p):
#     '''
#     term : factor TIMES factor
#          | factor DIVIDE factor
#     '''
#     p[0] = ('binop', p[2], p[1], p[3])

# def p_term_factor(p):
#     '''
#     term : factor
#     '''
#     p[0] = p[1]

# def p_factor_number(p):
#     '''
#     factor : NUMBER
#     '''
#     p[0] = ('number', p[1])

# def p_factor_name(p):
#     '''
#     factor : NAME
#     '''
#     p[0] = ('name', p[1])

# def p_factor_unary(p):
#     '''
#     factor : PLUS factor
#            | MINUS factor
#     '''
#     p[0] = ('unary', p[1], p[2])

# def p_factor_grouped(p):
#     '''
#     factor : LPAREN expression RPAREN
#     '''
#     p[0] = ('grouped', p[2])

# def p_error(p):
#     print(f'Syntax error at {p.value!r}')

# # Build the parser
# yacc_parser = yacc()
# print('yacc_parser ready')
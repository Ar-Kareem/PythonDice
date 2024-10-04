import importlib

def do_parse(s, reload_module=False):
    from . import example
    if reload_module:
        importlib.reload(example)
    from .example import yacc_parser
    return yacc_parser.parse(s)


def do_lexer(s, reload_module=False):
    from . import example
    if reload_module:
        importlib.reload(example)
    from .example import lexer
    lexer.input(s)
    return lexer


def do_parse_classic(s, reload_module=False):
    from . import example_classic
    if reload_module:
        importlib.reload(example_classic)
    from .example_classic import yacc_parser
    return yacc_parser.parse(s)


def do_lexer_classic(s, reload_module=False):
    from . import example_classic
    if reload_module:
        importlib.reload(example_classic)
    from .example_classic import lexer
    lexer.input(s)
    return lexer

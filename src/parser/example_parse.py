import logging

import src.parser.parse_and_exec as parse_and_exec  # from "anything else" breaks
from src.randvar import output


trials = [
r'''


loop P over {1..5} {
 output 1 named "INLOOP%[P]%"
}


'''
]

def setup_logger(filename):
    logging.basicConfig(filename=filename, level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler())
setup_logger('./log/example_parse.log')


logger = logging.getLogger(__name__)


def main(trials=trials):
  for to_parse in trials:
    try:
      # print('Parsing:', to_parse)
      if to_parse is None or to_parse.strip() == '':
        logger.debug('Empty string')
        continue
      lexer, yaccer = parse_and_exec.build_lex_yacc()
      parse_and_exec.do_lex(to_parse, lexer)
      if lexer.LEX_ILLEGAL_CHARS:
        logger.debug('Lex Illegal characters found: ' + str(lexer.LEX_ILLEGAL_CHARS))
        continue
      yacc_ret = parse_and_exec.do_yacc(to_parse, lexer, yaccer)
      if lexer.YACC_ILLEGALs:
        logger.debug('Yacc Illegal tokens found: ' + str(lexer.YACC_ILLEGALs))
        replaced = to_parse
        for x in lexer.YACC_ILLEGALs:
          replaced = replaced[:x[1]] + 'X' + replaced[x[1]+1:]
        logger.debug(f'Replaced illegal tokens with X: {replaced}')
        continue
      if yacc_ret is None:
        logger.debug('Parse failed')
        continue
      python_str = parse_and_exec.do_resolve(yacc_ret)
      logger.debug(python_str)
      r = parse_and_exec.safe_exec(python_str, global_vars={})
      for (args, kwargs) in r:
        output(*args, **kwargs, blocks_width=50)
    except Exception as e:
      logger.exception(e)
      return
  # logger.debug('done')

if __name__ == '__main__':
  main()

trials = [
r'''
output [absolute 1]
output [{1..5} contains 1]
output [count 1 in {1..5}]
output [explode d3]
output [highest 1 of 2d3]
output [lowest 1 of 2d3]
output [middle 1 of 2d3]
output [highest of 1 and 1]
output [lowest of 1 and 1]
output [maximum of 2d3]
output [reverse {1..4}]
output [sort {1..4}]
'''
]

import logging
from .parse_and_exec import pipeline

def main():
  for to_parse in trials:
    try:
      pipeline(to_parse, 
                    do_exec=True, 
                    verbose_input_str=False, 
                    verbose_lex=False, 
                    verbose_yacc=False, 
                    verbose_parseed_python=True,
                    global_vars={'output': lambda x, named=None: 1}
                    # global_vars={'output': lambda x, named=None: print('output called', named)}
                    )
    except Exception as e:
      logging.warning(f'Error in parsing: {to_parse}')
      logging.exception(e)
      # pipeline(to_parse, do_exec=False, verbose_input_str=True, verbose_lex=True, verbose_yacc=True, verbose_parseed_python=False)
      return
  print('done')

if __name__ == '__main__':
  main()
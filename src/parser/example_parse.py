
trials = [
r'''
function: test {
  result: 1
}
function: another test D:d {
  result: 1
}


\function: anotheranother test D {
  result: 1
}\

function: beast {result: [test]}
output [beast]
output 2*2
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
loop P over {1..3} {
  output P
}
A__A: 1
output 999
'''
]

import logging
from .parse_and_exec import pipeline
from randvar import output

def main():
  for to_parse in trials:
    try:
      r = pipeline(to_parse, 
                    do_exec=True,
                    _do_unsafe_exec=False,
                    verbose_input_str=False, 
                    verbose_lex=False, 
                    verbose_yacc=False, 
                    verbose_parseed_python=True,
                    # global_vars={'output': lambda x, named=None: 1}
                    # global_vars={'output': lambda x, named=None: print('output called', named)}
                    )
      for (args, kwargs) in r:
        output(*args, **kwargs)
    except Exception as e:
      logging.warning(f'Error in parsing: {to_parse}')
      logging.exception(e)
      # pipeline(to_parse, do_exec=False, verbose_input_str=True, verbose_lex=True, verbose_yacc=True, verbose_parseed_python=False)
      return
  print('done')

if __name__ == '__main__':
  main()
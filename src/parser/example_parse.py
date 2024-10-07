
trials = [
r'''
function: test {
  result: 1
}
function: another test D:d {
  result: 1
}

\
function: anotheranother test D {
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
B: 1
loop P over {1..3} {
  loop PP over {5..6} {
    output PP
    output PP+10
  }
  output 3
  output 4
  if (P-1)/2 {
    output 1003
  } else if P-1 {
    output 1002
  } else {
  if (P-1)/2 {
    output 1003
  } else if P-1 {
    output 1002
  } else {
    output 1001
  }
  }
}
function: another test D:d {
A: 1
function: another test D:d {
  result: 1
}
B: 2
}

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
      if r is None:
        continue
      for (args, kwargs) in r:
        output(*args, **kwargs)
    except Exception as e:
      # logging.warning(f'Error in parsing: {to_parse}')
      logging.exception(e)
      # pipeline(to_parse, do_exec=False, verbose_input_str=True, verbose_lex=True, verbose_yacc=True, verbose_parseed_python=False)
      return
  print('done')

if __name__ == '__main__':
  main()
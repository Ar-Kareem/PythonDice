code_library = [
'''
output 1
''',
'''
output 1d6
''',
'''
output 1 + 2 * 3 ^ 4 @ 5 d 6
''',
'''
output 1d6
output 1d2
output 1d4 named "1d4 now"
output 1d2 named "1d2 now"
output 1d3
''',
'''
output (! 2)>3
output ! (2>3)
output 2 > !3
output ! 2>3
''',
'''
output ! 5
output ! 0
output ! -5
output ! (1 > 2)
output ! (1 < 2)
''',
]

#!/usr/bin/env python

from setuptools import setup

setup(
    name='dice_calc',
    version='0.1.5',
    author='Ar-Kareem',
    description='Advanced Calculator for Dice',
    package_dir={
        # main package 'src'
        'dice_calc': 'src',
        # parser 'src/parser'
        'dice_calc.parser': 'src/parser',
        # ply 'src/parser/ply'
        'dice_calc.parser.ply': 'src/parser/ply',
    },
    packages=['dice_calc', 'dice_calc.parser', 'dice_calc.parser.ply'],

)
#build/public            rm dist/* && python3 setup.py sdist && python3 -m twine upload --repository pypi dist/*



# test locally                 pip uninstall -y dice_calc ; pip install ..\..\..\pythondice\dist\dice_calc-0.0.9.tar.gz ; python ./test.py

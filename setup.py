#!/usr/bin/env python

from setuptools import setup

setup(
    name='dice_calc',
    version='0.0.8',
    author='Ar-Kareem',
    description='Advanced Calculator for Dice',
    package_dir={
        # main package 'src'
        'dice_calc': 'src',
        # parser 'src/parser'
        'dice_calc.parser': 'src/parser',
    },
    packages=['dice_calc', 'dice_calc.parser'],

)
#            rm dist/* && python3 setup.py sdist && python3 -m twine upload --repository pypi dist/*
#!/usr/bin/env python

from setuptools import setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='dice_calc',
    version='0.2.0',
    author='Ar-Kareem',
    description='Advanced Calculator for Dice',
    long_description=long_description,
    long_description_content_type='text/markdown',
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

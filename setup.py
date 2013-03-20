#!/usr/bin/env python
 
from distutils.core import setup

packages = ['user_creation']

setup(
    name='user_creation',
    version='0.1',
    description='A Django application that enables you to create users and send them an activation link',
    author='Tino de Bruijn',
    author_email='tinodb@gmail.com',
    packages=packages,
    zip_safe=False,
)
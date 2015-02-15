#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup


try:
    README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
except IOError:
    README = ''


setup(name='zimsoap',
      version='0.3.3',
      description='A high-level library to access programaticaly Zimbra \
                   SOAP API features',
      long_description=README,
      author='Jocelyn Delalande',
      author_email='jdelalande@oasiswork.fr',
      url='https://github.com/oasiswork/zimsoap/',
      packages=['zimsoap'],
      install_requires=['python-zimbra>=1.0']
      )

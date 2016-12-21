#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

from zimsoap import __version__
from zimsoap.version import Version

requirements = [
    'python-zimbra>=2.0',
    'six',
]

try:
    README = open(
        os.path.join(os.path.dirname(__file__), 'README.md')).read().strip()
except IOError:
    README = ''


setup(
    name='zimsoap',
    version=Version(__version__).release,
    description='A high-level library to abstract Zimbra SOAP API requests',
    long_description=README,
    author='Oasiswork',
    author_email='dev@oasiswork.fr',
    url='https://github.com/oasiswork/zimsoap/',
    packages=find_packages(),
    install_requires=requirements,
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)

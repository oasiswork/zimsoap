#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

try:
    README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
except IOError:
    README = ''


def mk_version(base_version):
    try:
        try:
            GIT_HEAD = open('.git/HEAD').readline().split(':')[1].strip()
        except IndexError: # if we checkout a commit
            GIT_HEAD_REV = open('.git/HEAD').readline()
        else:
            GIT_HEAD_REV = open('.git/{0}'.format(GIT_HEAD)).readline().strip()

        return '{0}-git-{1:.7}'.format(base_version, GIT_HEAD_REV)
    except IOError:
        return base_version

setup(name='zimsoap',
      version=mk_version('0.2.3'),
      description='A high-level library to access programaticaly Zimbra \
                   SOAP API features',
      long_description=README,
      author='Jocelyn Delalande',
      author_email='jdelalande@oasiswork.fr',
      url='https://github.com/oasiswork/zimsoap/',
      packages=['zimsoap'],
      install_requires=['python-zimbra>=1.0']
      )

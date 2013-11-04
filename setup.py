#!/usr/bin/env python

from distutils.core import setup

def mk_version(base_version):
    try:
        GIT_HEAD = open('.git/HEAD').readline().split(':')[1].strip()
        GIT_HEAD_REV = open('.git/{}'.format(GIT_HEAD)).readline().strip()
        return '{}-git-{:.7}'.format(base_version, GIT_HEAD_REV)
    except IOError:
        return base_version

setup(name='zimsoap',
      version=mk_version('0.1'),
      description='A high-level library to access programaticaly Zimbra SOAP API features',
      author='Jocelyn Delalande',
      author_email='jdelalande@oasiswork.fr',
      url='https://dev.oasiswork.fr/projects/zimsoap/',
      packages=['zimsoap'],
      install_requires=['pysimplesoap >= 0.11']
      )

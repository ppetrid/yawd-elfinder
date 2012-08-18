#!/usr/bin/env python
from setuptools import setup, find_packages
import elfinder

setup(
      name='yawd-elfinder',
      version = elfinder.__version__,
      description='Elfinder-based file management solution for Django',
      author='Yawd',
      author_email='info@yawd.eu',
      packages=find_packages(),
      license='BSD',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries'
        ]
)
#!/usr/bin/env python
from setuptools import setup, find_packages
import elfinder

setup(
      name='yawd-elfinder',
      url='http://www.yawd.eu/content/articles/3/12/yawd-elfinder/',
      version = elfinder.__version__,
      description='Elfinder-based file management solution for Django',
      author='yawd',
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
        ],
      include_package_data = True,
      install_requires = [
        "Django >= 1.4",
        "PIL",
        "python-magic"
        ],
)
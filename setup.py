#!/usr/bin/env python
from setuptools import setup, find_packages
import elfinder

imaging_library = list()
try:
    import Image
except ImportError:
    try:
        from PIL import Image
    except ImportError:
        imaging_library.append('PIL')

print imaging_library
setup(
      name='yawd-elfinder',
      url='http://yawd.eu/open-source-projects/yawd-elfinder/',
      version = elfinder.__version__,
      description='Elfinder-based file management solution for Django',
      long_description=open('README.rst', 'rt').read(),
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
        "Django>=1.5",
        "python-magic"
        ] + imaging_library,
)

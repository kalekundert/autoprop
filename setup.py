#!/usr/bin/env python3
# encoding: utf-8

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='autoprop',
    version='0.0.2',
    author='Kale Kundert',
    author_email='kale@thekunderts.net',
    long_description=open('README.rst').read(),
    url='https://github.com/kalekundert/autoprop',
    license='MIT',
    py_modules=[
        'autoprop',
    ],
    keywords=[
        'property', 'properties',
        'accessor', 'accessors',
        'getter', 'setter'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries',
    ],
)

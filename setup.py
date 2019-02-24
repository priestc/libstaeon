# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import sys

extra_install = []
if sys.version_info <= (3,1):
    extra_install.append('futures')

setup(
    name="staeon",
    version='0.1.0',
    description='Core library for the Staeon cryptocurrency',
    long_description=open('README.md').read(),
    author='Chris Priest',
    author_email='nbvfour@gmail.com',
    url='https://github.com/priestc/staeon-core',
    packages=find_packages(),
    scripts=['bin/staeon'],
    include_package_data=True,
    license='LICENSE',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'requests',
        'arrow',
        'bitcoin==1.1.42',
    ] + extra_install
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='smart-check',
    version='0.3',
    description='A smart S.M.A.R.T. check',
    author='Johann Schmitz',
    author_email='johann@j-schmitz.net',
    url='https://ercpe.de/projects/smart-check',
    download_url='https://code.not-your-server.de/smart-check.git/tags/',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data = {'': ['*.yaml']},
    zip_safe=False,
    license='GPL-3',
)

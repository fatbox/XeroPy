#/usr/bin/env python
from setuptools import setup, find_packages
import os

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

setup(
        name="XeroPy",
        description="Pythonic ORM implementation of the Xero API",
        zip_safe= False,
        version="1.0",
        packages = ['xero',],
        install_requires=[
            'httplib2==0.6.0',
            'oauth2==1.2.0',
            'SocksiPy-branch==1.02',
            ],
        dependency_links=[
            'http://socksipy-branch.googlecode.com/issues/attachment?aid=30003000&name=SocksiPy-branch-1.02.tar.gz&token=61d76a1fa803a56bcfd1a93e34365158#egg=SocksiPy-branch-1.02',
            ],
        )

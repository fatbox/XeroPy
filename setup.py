#/usr/bin/env python
from setuptools import setup, find_packages
import os
import xero

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

setup(
        name = "xero",
        version = ".".join(str(part) for part in xero.__version__)
        packages = find_packages(),
        zip_safe = False,
        )

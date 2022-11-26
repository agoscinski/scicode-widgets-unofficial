#!/usr/bin/env python3
from setuptools import setup
import site, sys
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]
if __name__ == "__main__":
    setup()


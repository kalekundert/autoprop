#!/usr/bin/env python3

import sys

def pytest_ignore_collect(path, config):
    if sys.version_info[0] == 2:
        return 'python3' in str(path)
    if sys.version_info[0] == 3:
        return 'python2' in str(path)

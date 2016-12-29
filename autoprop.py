#!/usr/bin/env python

import sys, inspect, re
from pprint import pprint
from collections import defaultdict

def autoprop(cls):
    accessors = defaultdict(dict)
    expected_num_args = {'get': 1, 'set': 2, 'del': 1}

    for method_name, method in inspect.getmembers(cls, inspect.isfunction):
        accessor_match = re.match('(get|set|del)_(.+)', method_name)
        if not accessor_match:
            continue

        prefix, name = accessor_match.groups()
        arg_spec = inspect.getfullargspec(method)
        num_args = len(arg_spec.args) - len(arg_spec.defaults or ())

        if num_args != expected_num_args[prefix]:
            continue

        accessors[name][prefix] = method

    print(accessors)

    for name in accessors:
        if not hasattr(cls, name):
            setattr(cls, name, property(
                accessors[name].get('get'),
                accessors[name].get('set'),
                accessors[name].get('del'),
            ))

    return cls


# Abuse the import system so that the module itself can be used as a decorator.  
# This is a very simple intended only to cut-down on boilerplate, so I think 
# the trade-off between magicalness and ease-of-use is justified in this case.
sys.modules[__name__] = autoprop
autoprop.__version__ = '0.0.0'

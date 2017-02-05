#!/usr/bin/env python

def autoprop(cls):
    # These imports have to be inside autoprop(), otherwise the sys.modules 
    # hack below somehow makes them unavailable when the decorator is applied.
    import inspect, re
    from collections import defaultdict

    if not hasattr(cls, '__class__'):
        raise TypeError('@autoprop can only be used with new-style classes')

    accessors = defaultdict(dict)
    expected_num_args = {'get': 0, 'set': 1, 'del': 0}

    # The accessors we're searching for are considered methods in python2 and 
    # functions in python3.  Other than this, though, they behave the same.
    ismethod = lambda x: inspect.ismethod(x) or inspect.isfunction(x)

    for method_name, method in inspect.getmembers(cls, ismethod):
        accessor_match = re.match('(get|set|del)_(.+)', method_name)
        if not accessor_match:
            continue

        # Use getfullargspec() if it's available, otherwise use getargspec().
        try: from inspect import getfullargspec as getargspec
        except ImportError: from inspect import getargspec

        prefix, name = accessor_match.groups()
        arg_spec = getargspec(method)
        num_args = len(arg_spec.args) - len(arg_spec.defaults or ())
        num_args_minus_self = num_args - 1

        if num_args_minus_self != expected_num_args[prefix]:
            continue

        accessors[name][prefix] = method

    for name in accessors:
        attr_doesnt_exist = not hasattr(cls, name)
        attr_is_autoprop = isinstance(
                getattr(cls, name, None), autoprop.property)

        if attr_doesnt_exist or attr_is_autoprop:
            setattr(cls, name, autoprop.property(
                accessors[name].get('get'),
                accessors[name].get('set'),
                accessors[name].get('del'),
            ))

    return cls


autoprop.__version__ = '0.0.2'
autoprop.property = type('property', (property,), {})

# Abuse the import system so that the module itself can be used as a decorator.  
# This is a simple module intended only to cut-down on boilerplate, so I think 
# the trade-off between magicalness and ease-of-use is justified in this case.
import sys
sys.modules[__name__] = autoprop

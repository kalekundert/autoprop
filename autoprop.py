#!/usr/bin/env python

class autoprop(object):

    __version__ = '1.0.1'
    property = type('property', (property,), {})

    class _Cache:
        __slots__ = ('value', 'is_stale')

        def __init__(self):
            self.value = None
            self.is_stale = True

        def __repr__(self):
            import sys
            return '{}(value={!r}, is_stale={!r})'.format(
                    self.__class__.__qualname__ if sys.version_info[0] >= 3 else self.__class__.__name__,
                    self.value,
                    self.is_stale,
            )

    def __new__(autoprop, cls):
        # These imports have to be inside autoprop(), otherwise the sys.modules 
        # hack below somehow makes them unavailable when the decorator is 
        # applied.
        import inspect, re
        from collections import defaultdict
        from functools import wraps

        if not hasattr(cls, '__class__'):
            raise TypeError('@autoprop can only be used with new-style classes')

        accessors = defaultdict(dict)
        expected_num_args = {'get': 0, 'set': 1, 'del': 0}

        # The accessors we're searching for are considered methods in python2 
        # and functions in python3.  They behave the same either way.
        ismethod = lambda x: inspect.ismethod(x) or inspect.isfunction(x)

        for method_name, method in inspect.getmembers(cls, ismethod):
            accessor_match = re.match('(get|set|del)_(.+)', method_name)
            if not accessor_match:
                continue

            # Suppress a warning by using getfullargspec() if it's available 
            # and getargspec() if it's not.
            try: from inspect import getfullargspec as getargspec
            except ImportError: from inspect import getargspec

            prefix, name = accessor_match.groups()
            arg_spec = getargspec(method)
            num_args = len(arg_spec.args) - len(arg_spec.defaults or ())
            num_args_minus_self = num_args - 1

            if num_args_minus_self != expected_num_args[prefix]:
                continue

            accessors[name][prefix] = method

        def get_cache(self, getter):
            if not hasattr(self, '_autoprop_cache'):
                self._autoprop_cache = {}
            return self._autoprop_cache.setdefault(getter, autoprop._Cache())

        def use_cache(getter):

            @wraps(getter)
            def wrapper(self, *args, **kwargs):
                cache = get_cache(self, getter)

                if cache.is_stale:
                    cache.value = getter(self, *args, **kwargs)
                    cache.is_stale = False

                return cache.value

            return wrapper

        def clear_cache(f, getter):
            if f is None:
                return None

            @wraps(f)
            def wrapper(self, *args, **kwargs):
                get_cache(self, getter).is_stale = True
                return f(self, *args, **kwargs)

            return wrapper

        for name in accessors:
            try:
                attr = getattr(cls, name)
                ok_to_overwrite = isinstance(attr, autoprop.property)
            except AttributeError:
                ok_to_overwrite = True

            getter  = accessors[name].get('get')
            setter  = accessors[name].get('set')
            deleter = accessors[name].get('del')

            # Cache the return value of the getter, if requested.  For some 
            # reason setting attributes on method objects 
            if getter and getattr(getter, '_autoprop_mark_cache', False):
                setter  = clear_cache(setter,  getter)
                deleter = clear_cache(deleter, getter)
                getter  = use_cache(getter)

            if ok_to_overwrite:
                property = autoprop.property(getter, setter, deleter)
                setattr(cls, name, property)

        return cls

    @staticmethod
    def cache(f):
        if not f.__name__.startswith('get_'):
            import sys
            raise ValueError("{}() cannot be cached; it's not a getter".format(
                f.__qualname__ if sys.version_info[0] >= 3 else f.__name__
            ))

        f._autoprop_mark_cache = True
        return f

# Abuse the import system so that the module itself can be used as a decorator.  
# This is a simple module intended only to cut-down on boilerplate, so I think 
# the trade-off between magicalness and ease-of-use is justified in this case.
import sys
sys.modules[__name__] = autoprop

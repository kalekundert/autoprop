#!/usr/bin/env python3

"""
Infer properties from accessor methods.

The :mod:`autoprop` module can be directly used as a class decorator.  

- Method discovery
  - Private methods

- Argument signatures
  - optional argument allowed
  - required arguments must match
"""

from .decorators import (
        autoprop, cache, dynamic, immutable, policy,
)
from .cache import (
        get_cache, clear_cache,
        get_cached_attr, set_cached_attr, del_cached_attr,
)

__version__ = '4.0.1'

# Hack to make the module directly usable as a decorator.  Only works for 
# python 3.5 or higher.  See this Stack Overflow post:
# https://stackoverflow.com/questions/1060796/callable-modules

import sys

class _CallableModule(sys.modules[__name__].__class__):

    def __call__(self, *args, **kwargs):
        return autoprop(*args, **kwargs)

sys.modules[__name__].__class__ = _CallableModule
del sys, _CallableModule


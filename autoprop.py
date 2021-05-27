#!/usr/bin/env python

"""Infer properties from accessor methods."""

import sys
import inspect
import re
import functools
import signature_dispatch
from functools import partial
from collections import defaultdict

__version__ = '3.0.0'

_EXPECTED_NUM_ARGS = {'get': 0, 'set': 1, 'del': 0}
_CACHE_POLICIES = ['dynamic', 'class', 'object', 'property', 'immutable']
_CACHE_ATTR = '_autoprop_cache'
_CACHE_VERSION_ATTR = '_autoprop_cache_version'
_CACHE_POLICY_ATTR = '_autoprop_cache_policy'
_REFRESH_ATTR = '_autoprop_refresh'
_INITIAL_VERSION = 1
_DEFAULT_POLICY = 'property'

class Cache:

    def __init__(self, obj):
        self.obj = obj
        self.cls = obj.__class__

        self.values = {}
        self.cls_versions = {}
        self.obj_versions = {}
        self.attr_touched = {}

    def bind(self, attr):
        return BoundCache(self, attr)

class BoundCache:

    def __init__(self, cache, attr):
        self.cache = cache
        self.attr = attr

    def is_stale(self, policy):
        if policy == 'dynamic':
            return True

        cache = self.cache
        attr = self.attr

        if attr not in cache.values:
            return True

        if policy == 'immutable':
            return False

        if cache.attr_touched.get(attr, False):
            return True

        if policy == 'property':
            return False

        v0 = _INITIAL_VERSION - 1

        if cache.obj_versions.get(attr, v0) < get_cache_version(cache.obj):
            return True

        if policy == 'object':
            return False

        assert policy == 'class'

        for base in cache.cls.__mro__:
            my_version = cache.cls_versions.get(base, {}).get(attr, v0)
            base_version = get_cache_version(base)
            if my_version < base_version:
                return True

        return False

    def get(self):
        return self.cache.values[self.attr]

    def update(self, value):
        cache = self.cache
        attr = self.attr

        cache.values[attr] = value
        cache.attr_touched[attr] = False
        cache.obj_versions[attr] = get_cache_version(cache.obj)

        # Build this dictionary on the fly to be robust against the (remote) 
        # possibility that `__mro__` could change at runtime, e.g.:
        # https://stackoverflow.com/questions/20822850/change-python-mro-at-runtime 

        for base in cache.cls.__mro__:
            cache.cls_versions.setdefault(base, {})[attr] = \
                    get_cache_version(base)

    def touch(self):
        self.cache.attr_touched[self.attr] = True

class CachedProperty(property):

    def __init__(self, name, getter, setter, deleter, policy):
        super().__init__(getter, setter, deleter)
        self.name = name
        self.policy = policy

    def __get__(self, obj, owner=None):
        # Class attribute access (e.g. for docstrings): 
        if obj is None:
            return super().__get__(obj, owner)

        # Instance attribute access:
        cache = self.get_bound_cache(obj)

        if cache.is_stale(self.policy):
            value = super().__get__(obj, owner)
            cache.update(value)

        return cache.get()

    def __set__(self, obj, value):
        cache = self.get_bound_cache(obj)
        cache.touch()
        return super().__set__(obj, value)

    def __delete__(self, obj):
        cache = self.get_bound_cache(obj)
        cache.touch()
        return super().__delete__(obj)

    def get_bound_cache(self, obj):
        cache = get_cache(obj)
        return cache.bind(self.name)

    def getter_replacement(self):
        def getter(obj, *args, **kwargs):
            if not args and not kwargs:
                return self.__get__(obj, None)
            else:
                return self.fget(obj, *args, **kwargs)
        return getter

def autoprop(cls):
    return _make_autoprops(cls)

def cache(*args, **kwargs):

    def wrapper(x, policy):
        if inspect.isclass(x):
            return _make_autoprops(x, cache=True, default_policy=policy)
        else:
            return _assign_policy(x, policy=policy)

    dispatch = signature_dispatch()

    @dispatch
    def decorator(*, policy):
        _check_policy(policy)
        return partial(wrapper, policy=policy)

    @dispatch
    def decorator():
        return partial(wrapper, policy=_DEFAULT_POLICY)

    @dispatch
    def decorator(f):
        return wrapper(f, _DEFAULT_POLICY)

    return decorator(*args, **kwargs)

def dynamic(f):
    return cache(policy='dynamic')(f)

def immutable(f):
    return cache(policy='immutable')(f)

def policy(policy):
    _check_policy(policy)

    def wrapper(f):
        _assign_policy(f, policy)
        return f

    return wrapper

def refresh(f):
    setattr(f, _REFRESH_ATTR, True)
    return f

def get_cache(obj):
    try:
        cache = getattr(obj, _CACHE_ATTR)
    except AttributeError:
        cache = Cache(obj)
        setattr(obj, _CACHE_ATTR, cache)

    return cache

def get_cache_version(obj):
    return getattr(obj, _CACHE_VERSION_ATTR, _INITIAL_VERSION)

def clear_cache(obj):
    try:
        delattr(obj, _CACHE_ATTR)
    except AttributeError:
        pass


def _make_autoprops(cls, *, cache=False, default_policy=_DEFAULT_POLICY):
    accessors = defaultdict(dict)

    def get_accessor(name, prefix):
        # If we found the accessor in this class, return it.
        try:
            return accessors[name][prefix]

        # Otherwise, look for a suitable method in parent classes.
        except KeyError:

            try:
                full_name = '%s_%s' % (prefix, name)
                attr = getattr(cls, full_name)
            except AttributeError:
                return None
            else:
                return attr if _is_accessor(full_name, attr) else None

    def increment_cache_version(f, predicate=lambda *args, **kwargs: True):
        if f is None:
            return f

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if predicate(*args, **kwargs):
                if args and isinstance(args[0], cls):
                    obj = args[0]
                else:
                    obj = cls

                version = get_cache_version(obj)
                setattr(obj, _CACHE_VERSION_ATTR, version + 1)

            return f(*args, **kwargs)

        return wrapper

    for name, attr in cls.__dict__.items():
        # Because we are iterating through `__dict__`, class/static methods 
        # will not be bound and will not appear as functions, which is good 
        # because we cannot make class properties without metaclasses.

        key = _is_accessor(name, attr)
        if key:
            name, prefix = key
            accessors[name][prefix] = attr

            if hasattr(attr, _CACHE_POLICY_ATTR):
                if not cache:
                    raise ValueError("\n".join([
                        f"cache disabled: can't specify cache policies",
                        f"class: {cls.__qualname__}",
                        f"method: {attr.__qualname__}",
                        f"decorate the class with `@autoprop.cache` or `@autoprop.dynamic` to enable the cache.",
                    ]))


        if getattr(attr, _REFRESH_ATTR, False):
            if not cache:
                raise ValueError("\n".join([
                    f"cache disabled: can't use `@autoprop.refresh`",
                    f"class: {cls.__qualname__}",
                    f"method: {attr.__qualname__}",
                    f"decorate the class with `@autoprop.cache` or `@autoprop.dynamic` to enable the cache.",
                ]))
            setattr(cls, name, increment_cache_version(attr))

        # We have to dig inside static/class methods to see if the underlying 
        # function is supposed to get decorated.

        if isinstance(attr, (classmethod, staticmethod)):
            if getattr(attr.__func__, _REFRESH_ATTR, False):
                if not cache:
                    raise ValueError("\n".join([
                        f"cache disabled: can't use `@autoprop.refresh`",
                        f"class: {cls.__qualname__}",
                        f"method: {attr.__func__.__qualname__}",
                        f"decorate the class with `@autoprop.cache` or `@autoprop.dynamic` to enable the cache.",
                    ]))
                attr = type(attr)(increment_cache_version(attr.__func__))
                setattr(cls, name, attr)

    for name in accessors:

        # Don't overwrite any attributes defined in this class.  Attributes 
        # defined in superclasses may be shadowed.

        if name in cls.__dict__:
            continue

        getter  = get_accessor(name, 'get')
        setter  = get_accessor(name, 'set')
        deleter = get_accessor(name, 'del')

        if not cache:
            # Mark the getter as 'dynamic'.  This won't have any affect on this 
            # class, but if a subclass with caching enabled incorporates this 
            # getter into an autoprop, this policy will ensure that the getter 
            # remains un-cached (as its author presumably intended).
            if getter:
                dynamic(getter)

            prop = property(getter, setter, deleter)

        else:
            setter = increment_cache_version(setter)
            deleter = increment_cache_version(deleter)
            policy = getattr(getter, _CACHE_POLICY_ATTR, default_policy)

            if policy == 'immutable':
                if getter and setter:
                    raise ValueError("\n".join([
                        f"can't specify setter for immutable property",
                        f"property: {cls.__qualname__}.{name}",
                        f"immutable getter: {getter.__qualname__}",
                        f"setter: {setter.__qualname__}",
                    ]))
                if getter and deleter:
                    raise ValueError("\n".join([
                        f"can't specify deleter for immutable property",
                        f"property: {cls.__qualname__}.{name}",
                        f"immutable getter: {getter.__qualname__}",
                        f"deleter: {deleter.__qualname__}",
                    ]))

            prop = CachedProperty(name, getter, setter, deleter, policy)

            if getter:
                setattr(cls, f'get_{name}', prop.getter_replacement())

        setattr(cls, name, prop)

    if cache:

        # Automatically increment the cache on attribute assignment.  
        # 
        # Don't do the same for attribute deletion, because (i) classes are not 
        # supposed to implement `__delattr__()` unless they actually support it 
        # and (ii) it's easy to get this behavior by decorating `__delattr__()` 
        # with `@autoprop.refresh`.  Decorating `__setattr__()` is not so 
        # easy because steps must be taken to avoid infinite recursion.

        try:
            __setattr__ = cls.__dict__['__setattr__']
        except KeyError:
            def __setattr__(self, name, value):
                super(cls, self).__setattr__(name, value)

        def predicate(self, name, value):
            return not name.startswith('_autoprop')

        __setattr__ = increment_cache_version(__setattr__, predicate)
        setattr(cls, '__setattr__', __setattr__)

    return cls

def _check_policy(policy):
    if policy not in _CACHE_POLICIES:
        expected = ', '.join(repr(p) for p in _CACHE_POLICIES)
        raise ValueError(f"unknown policy {policy!r}, expected one of: {expected}")

def _assign_policy(f, policy):
    if not f.__name__.startswith('get_'):
        raise ValueError(f"can't cache {f.__qualname__}; it's not a getter")

    setattr(f, _CACHE_POLICY_ATTR, policy)
    return f

def _is_accessor(name, attr):
    if not inspect.isfunction(attr):
        return False

    accessor_match = re.match('(get|set|del)_(.+)', name)
    if not accessor_match:
        return False

    def is_required(p):
        positional = p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD
        return p.kind in positional and p.default is p.empty

    # The attributes passed to this function must be accessed via `getattr()` 
    # (e.g. as opposed to `cls.__dict__[]`) because static/class methods are 
    # not callable until bound to the class.

    prefix, name = accessor_match.groups()
    sig = inspect.signature(attr)
    params = sig.parameters.values()
    num_args = sum(map(is_required, params)) - 1

    if num_args != _EXPECTED_NUM_ARGS[prefix]:
        return False

    return name, prefix

# Hack to make the module directly usable as a decorator.  Only works for 
# python 3.5 or higher.  See this Stack Overflow post:
# https://stackoverflow.com/questions/1060796/callable-modules

class CallableModule(sys.modules[__name__].__class__):

    def __call__(self, *args, **kwargs):
        return autoprop(*args, **kwargs)

sys.modules[__name__].__class__ = CallableModule


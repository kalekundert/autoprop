#!/usr/bin/env python3

import functools
import sys

from .cache import (
        CachedProperty, ConditionalCachedProperty,
        set_cached_attr, del_cached_attr,
)
from operator import attrgetter

if sys.version_info >= (3, 8):
    from functools import cached_property
else:
    from backports.cached_property import cached_property

_KNOWN_POLICIES = {}
_MISSING = object()
_UNDEFINED = object()

class ProvideMutatorsMixin:

    def __init__(self, *, provide_mutators=None):
        super().__init__()
        self._provide_mutators = provide_mutators

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        subcls_make_prop = cls.make_prop

        @functools.wraps(subcls_make_prop)
        def make_prop(self, cls, name, getter, setter, deleter):
            if self.parent and self._provide_mutators is None:
                is_enabled = getattr(self.parent, '_provide_mutators', False)
            else:
                is_enabled = self._provide_mutators

            if is_enabled:
                if not setter:
                    def setter(self, value):
                        set_cached_attr(self, name, value)

                if not deleter:
                    def deleter(self):
                        del_cached_attr(self, name)

            return subcls_make_prop(self, cls, name, getter, setter, deleter)

        cls.make_prop = make_prop

class Policy:
    wrap_getter = True

    def __init__(self):
        self.parent = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _KNOWN_POLICIES[cls.name] = cls

    def make_prop(self, cls, name, getter, setter, deleter):
        raise NotImplementedError

class DynamicPolicy(Policy):
    name = 'dynamic'
    wrap_getter = False

    def make_prop(self, cls, name, getter, setter, deleter):
        # Mark the getter as 'dynamic'.  This won't have any affect on this 
        # class, but if a subclass with caching enabled incorporates this 
        # getter into an autoprop, this policy will ensure that the getter 
        # remains un-cached (as its author presumably intended).
        if getter:
            from .decorators import dynamic
            dynamic(getter)

        return property(getter, setter, deleter)

class OverwritePolicy(Policy):
    name = 'overwrite'

    def make_prop(self, cls, name, getter, setter, deleter):
        if setter:
            raise ValueError("\n".join([
                f"can't specify setter for property using the 'overwrite' cache policy",
                f"property: {cls.__qualname__}.{name}",
                f"getter: {getter.__qualname__}",
                f"setter: {setter.__qualname__}",
            ]))

        if deleter:
            raise ValueError("\n".join([
                f"can't specify deleter for property using the 'overwrite' cache policy",
                f"property: {cls.__qualname__}.{name}",
                f"getter: {getter.__qualname__}",
                f"deleter: {deleter.__qualname__}",
            ]))

        return cached_property(getter)

class ManualPolicy(ProvideMutatorsMixin, Policy):
    name = 'manual'

    def make_prop(self, cls, name, getter, setter, deleter):
        return CachedProperty(getter, setter, deleter)

class AutomaticPolicy(ProvideMutatorsMixin, Policy):
    name = 'automatic'

    class MemoManager:

        def __init__(self, watch):
            self._watchers = [
                    _undefined_ok(attrgetter(w) if isinstance(w, str) else w)
                    for w in watch
            ]

        def refresh(self, obj):
            return [id(f(obj)) for f in self._watchers]

        def is_fresh(self, prev_memo, curr_memo):
            return prev_memo == curr_memo

    def __init__(self, *, watch, **kwargs):
        super().__init__(**kwargs)
        self._manager = self.MemoManager(watch)

    def make_prop(self, cls, name, getter, setter, deleter):
        return ConditionalCachedProperty(getter, setter, deleter, self._manager)

class ImmutablePolicy(Policy):
    name = 'immutable'

    def make_prop(self, cls, name, getter, setter, deleter):
        if setter:
            raise ValueError("\n".join([
                f"can't specify setter for immutable property",
                f"property: {cls.__qualname__}.{name}",
                f"immutable getter: {getter.__qualname__}",
                f"setter: {setter.__qualname__}",
            ]))

        if deleter:
            raise ValueError("\n".join([
                f"can't specify deleter for immutable property",
                f"property: {cls.__qualname__}.{name}",
                f"immutable getter: {getter.__qualname__}",
                f"deleter: {deleter.__qualname__}",
            ]))

        return CachedProperty(getter, setter, deleter)

def _make_policy(policy, **kwargs):
    if isinstance(policy, Policy):
        if kwargs:
            args = ', '.join(repr(k) for k in kwargs)
            raise TypeError("got unexpected keyword arguments: {args}")
        return policy

    try:
        policy_cls = _KNOWN_POLICIES[policy]
    except KeyError:
        expected = ', '.join(repr(p) for p in _KNOWN_POLICIES)
        raise ValueError(f"unknown policy {policy!r}, expected one of: {expected}")
    else:
        return policy_cls(**kwargs)

def _undefined_ok(f):

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AttributeError:
            return _UNDEFINED

    return wrapper



#!/usr/bin/env python3

import inspect
import re
import functools
import signature_dispatch

from .policies import _make_policy
from functools import partial
from collections import defaultdict
from collections.abc import Callable

_CACHE_POLICY_ATTR = '__autoprop_cache_policy'
_EXPECTED_NUM_ARGS = {'get': 0, 'set': 1, 'del': 0}
_UNSPECIFIED = object()

def autoprop(cls):
    return _make_autoprops(cls)

def cache(*args, **kwargs):
    """
    Enable caching for a method or class.

    Keyword Arguments:
        policy (str):
            How the cache should be managed

        provide_mutators (bool):
            Only allowed for the ``manual`` and ``automatic`` policies.  If 
            true, 

        watch (List[str]):
            Only allowed for the ``automatic`` policy.  

    

    """

    def decorator(x, policy='overwrite', **kwargs):
        policy = _make_policy(policy, **kwargs)
        if inspect.isclass(x):
            return _make_autoprops(x, default_policy=policy)
        else:
            return _assign_policy(x, policy=policy)

    dispatch = signature_dispatch()

    @dispatch
    def decorator_factory(*, policy, **kwargs):
        return partial(decorator, policy=policy, **kwargs)

    @dispatch
    def decorator_factory():
        return decorator

    @dispatch
    def decorator_factory(f: Callable):
        return decorator(f)

    return decorator_factory(*args, **kwargs)

def dynamic(f):
    """
    Alias for: :deco:`@autoprop.cache(policy='dynamic') <autoprop.cache>`
    """
    return cache(policy='dynamic')(f)

def immutable(f):
    """
    Alias for: :deco:`@autoprop.cache(policy='immutable') <autoprop.cache>`
    """
    return cache(policy='immutable')(f)

def policy(policy: str, **kwargs):
    """
    Specify the caching policy for a method.

    Arguments:
        policy: See :deco:`autoprop.cache`
        kwargs: See :deco:`autoprop.cache`

    This decorator is very similar to :deco:`autoprop.cache`.  The only real 
    differences are that :deco:`autoprop.policy` does not have a default policy 
    and can only be used on methods (i.e. it can't be used on classes).  

    The reason why this decorator is provided is simply that some people might 
    find it more readable in certain circumstances.  For example, if a class is 
    decorated with :deco:`autoprop.cache`, it may feel redundant to use the 
    same decorator again on individual methods to change the cache policy.  Why 
    specify that those methods are cached when the class already specifies that 
    all methods are cached by default?  The :deco:`autoprop.policy` decorator 
    may make it more clear that everything is still cached and that only the 
    details of how that caching works are changing.
    """
    def wrapper(f):
        p = _make_policy(policy, **kwargs)
        _assign_policy(f, p)
        return f

    return wrapper


def _make_autoprops(cls, *, default_policy='dynamic'):
    accessors = defaultdict(dict)
    default_policy = _make_policy(default_policy)

    def get_accessor(prop_name, kind):
        # If we found the accessor in this class, return it.
        try:
            return accessors[prop_name][kind]

        # Otherwise, look for a suitable method in parent classes.
        except KeyError:

            try:
                accessor_name = prop_name.make_accessor_name(kind)
                attr = getattr(cls, accessor_name)
            except AttributeError:
                return None
            else:
                return attr if _is_accessor(cls, accessor_name, attr) else None

    for attr_name, attr in cls.__dict__.items():
        # Because we are iterating through `__dict__`, class/static methods 
        # will not be bound and will not appear as functions, which is good 
        # because we cannot make class properties without metaclasses.

        x = _is_accessor(cls, attr_name, attr)
        if x:
            prop_name, kind = x
            accessors[prop_name][kind] = attr

    for prop_name in accessors:
        prop_name_str = str(prop_name)

        # Don't overwrite any attributes defined in this class.  Attributes 
        # defined in superclasses may be shadowed.

        if prop_name_str in cls.__dict__:
            continue

        getter  = get_accessor(prop_name, 'get')
        setter  = get_accessor(prop_name, 'set')
        deleter = get_accessor(prop_name, 'del')

        policy = getattr(getter, _CACHE_POLICY_ATTR, None)
        if policy:
            policy.parent = default_policy
        else:
            policy = default_policy

        prop = policy.make_prop(cls, prop_name_str, getter, setter, deleter)
        try:
            prop.__set_name__(cls, prop_name_str)
        except AttributeError:
            pass

        setattr(cls, prop_name_str, prop)

        if getter and policy.wrap_getter:
            getter_name = prop_name.make_accessor_name('get')
            getter_wrapper = _wrap_getter(getter, prop_name_str)
            setattr(cls, getter_name, getter_wrapper)

    return cls

def _wrap_getter(getter, prop_name):
    prop_name_str = str(prop_name)

    if len(inspect.signature(getter).parameters) == 1:
        @functools.wraps(getter)
        def getter_wrapper(self): #
            # Delegate to the property, e.g. to handle caching.
            return getattr(self, prop_name_str)
    else:
        @functools.wraps(getter)
        def getter_wrapper(self, *args, **kwargs): #
            if not args and not kwargs:
                return getattr(self, prop_name_str)
            else:
                return getter(self, *args, **kwargs)

    return getter_wrapper

def _assign_policy(f, policy):
    if not f.__name__.lstrip('_').startswith('get_'):
        raise ValueError(f"can't cache {f.__qualname__}; it's not a getter")

    setattr(f, _CACHE_POLICY_ATTR, policy)
    return f

def _is_accessor(cls, name, attr):
    if not inspect.isfunction(attr):
        return False

    try:
        prop_name, kind = _PropertyName.from_accessor_name(cls, name)
    except ValueError:
        return False

    sig = inspect.signature(attr)
    fake_bind_args = [None] * (_EXPECTED_NUM_ARGS[kind] + 1)

    try:
        sig.bind(*fake_bind_args)
    except TypeError:
        return False

    return prop_name, kind

def _regex_in(*terms):
    return '|'.join(re.escape(x) for x in terms)

class _PropertyName:
    root: str
    prefix: str

    def __init__(self, root, prefix):
        self.root = root
        self.prefix = prefix

    def __str__(self):
        return f'{self.prefix}{self.root}'

    def __eq__(self, other):
        return self.root == other.root and self.prefix == other.prefix

    def __hash__(self):
        return hash((self.root, self.prefix))

    @classmethod
    def from_accessor_name(cls, owner, name):
        prefix_regex = _regex_in('', '_', f'_{owner.__name__}__')
        match = re.match(rf'({prefix_regex})(get|set|del)_(.+)', name)
        if not match:
            raise ValueError

        prefix, kind, root = match.groups()
        return cls(root, prefix), kind

    def make_accessor_name(self, kind):
        return f'{self.prefix}{kind}_{self.root}'


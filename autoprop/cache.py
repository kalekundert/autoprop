#!/usr/bin/env python3

_CACHE_ATTR = '__autoprop_cache'
_SET_BY_USER = object()
_UNSPECIFIED = object()

class Cache:

    def __init__(self, obj):
        self.values = {}
        self.memos = {}

class CachedProperty(property):

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, owner=None):
        # Class attribute access (e.g. for docstrings): 
        if obj is None:
            return super().__get__(obj, owner)

        # Instance attribute access:
        cache = get_cache(obj)
        attr = self.name

        try:
            return cache.values[attr]
        except KeyError:
            value = super().__get__(obj, owner)
            cache.values[attr] = value
            return value

class ConditionalCachedProperty(property):

    def __init__(self, getter, setter, deleter, memo_manager):
        super().__init__(getter, setter, deleter)
        self.memo_manager = memo_manager

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, owner=None):
        # Class attribute access (e.g. for docstrings): 
        if obj is None:
            return super().__get__(obj, owner)

        # Instance attribute access:
        cache = get_cache(obj)
        attr = self.name
        manager = self.memo_manager
        curr_memo = manager.refresh(obj)

        try:
            prev_memo = cache.memos[attr]
        except KeyError:
            is_fresh = False
        else:
            is_fresh = prev_memo is _SET_BY_USER or \
                    manager.is_fresh(prev_memo, curr_memo)

        if is_fresh:
            # Assume that a `memos` entry implies a `values` entry.
            return cache.values[attr]

        value = super().__get__(obj, owner)
        cache.values[attr] = value
        cache.memos[attr] = curr_memo
        return value

def get_cache(obj):
    try:
        return getattr(obj, _CACHE_ATTR)
    except AttributeError:
        cache = Cache(obj)
        setattr(obj, _CACHE_ATTR, cache)
        return cache

def get_cached_attr(obj, attr, default=_UNSPECIFIED):
    """
    Get the cached value of the given attribute.

    .. warning::

        This method should only be used on properties that are cached with the 

    Arguments:
        obj:
            Any object.

        attr (str):
            The name of the attribute to look up.

        default:
            The value to return if the given attribute is not found in the 
            cache.  If not specified, an :exc:`AttributeError` will be raised 
            in this circumstance.

    If the given object didn't have a cache, this will initialize and empty one.
    Only the 
    """
    cache = get_cache(obj)
    try:
        return cache.values[attr]
    except KeyError as err:
        if default is not _UNSPECIFIED:
            return default
        else:
            raise AttributeError(err) from None

def set_cached_attr(obj, attr, value):
    cache = get_cache(obj)
    cache.values[attr] = value
    cache.memos[attr] = _SET_BY_USER

def del_cached_attr(obj, attr):
    cache = get_cache(obj)

    try:
        del cache.values[attr]
    except KeyError as err:
        raise AttributeError(err) from None

    try:
        del cache.memos[attr]
    except KeyError:
        pass

def clear_cache(obj):
    """
    Delete the cache associated with the given object.

    .. warning::

        Only the ``manual``, ``automatic``, and ``immutable`` cache policies 
        will be affected by this operation.  The ``overwrite`` policy caches 
        values directly in the instance dictionary, and so will not be 
        affected.

    This will force any values stored in the cache to be recalculated the next 
    time they are needed.
    """
    try:
        delattr(obj, _CACHE_ATTR)
    except AttributeError:
        pass



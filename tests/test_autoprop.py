#!/usr/bin/env python

import pytest
import autoprop

def test_get():
    @autoprop
    class Example(object): #
        def get_attr(self): #
            return 'attr'

    ex = Example()
    assert ex.attr == 'attr'

def test_set():
    @autoprop
    class Example(object): #
        def set_attr(self, attr): #
            self._attr = 'new ' + attr

    ex = Example()
    ex.attr = 'attr'
    assert ex._attr == 'new attr'

def test_del():
    @autoprop
    class Example(object): #
        def del_attr(self): #
            self._attr = None

    ex = Example()
    del ex.attr
    assert ex._attr is None

def test_get_set():
    @autoprop
    class Example(object): #
        def get_attr(self): #
            return self._attr
        def set_attr(self, attr): #
            self._attr = 'new ' + attr

    ex = Example()
    ex.attr = 'attr'
    assert ex.attr == 'new attr'

def test_get_set_del():
    @autoprop
    class Example(object): #
        def get_attr(self): #
            return self._attr
        def set_attr(self, attr): #
            self._attr = 'new ' + attr
        def del_attr(self): #
            self._attr = None

    ex = Example()
    ex.attr = 'attr'
    assert ex.attr == 'new attr'
    del ex.attr
    assert ex.attr is None

def test_cache_get():
    @autoprop
    class Example(object): #
        def __init__(self): #
            self._attr = 0
        @autoprop.cache
        def get_attr(self): #
            self._attr += 1
            return self._attr

    ex = Example()

    # Calling the getter multiple times only call the underlying method once.
    assert ex.attr == 1
    assert ex.attr == 1

def test_cache_get_set_del():
    @autoprop
    class Example(object): #
        def __init__(self): #
            self._attr = 0
        @autoprop.cache
        def get_attr(self): #
            self._attr += 1
            return self._attr
        def set_attr(self, attr): #
            self._attr = attr
        def del_attr(self): #
            self._attr = 0

    ex = Example()

    # Calling the getter multiple times only call the underlying method once.
    assert ex.attr == 1
    assert ex.attr == 1

    # Calling the setter clears the cache.
    ex.attr = 2
    assert ex.attr == 3
    assert ex.attr == 3

    # Calling the deleter also clears the cache.
    del ex.attr
    assert ex.attr == 1
    assert ex.attr == 1

def test_ignore_similar_names():
    @autoprop #
    class Example(object):
        def getattr(self):
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_ignore_empty_names():
    @autoprop #
    class Example(object):
        def get_(self):
            return 'get'

    ex = Example()
    with pytest.raises(AttributeError):
        getattr(ex, '')

def test_ignore_non_methods():
    @autoprop #
    class Example(object):
        get_attr = 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_dont_overwrite_existing_attributes():
    @autoprop #
    class Example(object):
        attr = 'class var'
        def get_attr(self):
            return 'attr'

    ex = Example()
    assert ex.attr == 'class var'

def test_dont_overwrite_inherited_attributes():
    @autoprop #
    class Parent(object):
        attr = 'class var'
        def get_attr(self):
            return 'parent'

    @autoprop #
    class Child(Parent):
        def get_attr(self):
            return 'child'

    parent = Parent()
    child = Child()

    assert parent.attr == 'class var'
    assert child.attr == 'class var'

def test_overwrite_inherited_autoprops():
    @autoprop #
    class Parent(object):
        def get_attr(self):
            return 'parent'
        def get_overloaded_attr(self):
            return 'parent'

    @autoprop #
    class Child(Parent):
        def get_overloaded_attr(self):
            return 'child'

    parent = Parent()
    child = Child()

    assert parent.attr == 'parent'
    assert parent.overloaded_attr == 'parent'
    assert child.attr == 'parent'
    assert child.overloaded_attr == 'child'

def test_optional_arguments():
    @autoprop #
    class Example(object):
        def get_attr(self, pos=None, *args, **kwargs):
            return self._attr
        def set_attr(self, new_value, pos=None, *args, **kwargs):
            print('asdasd')
            self._attr = 'new ' + new_value
        def del_attr(self, pos=None, *args, **kwargs):
            self._attr = None

    ex = Example()
    ex.attr = 'attr'
    assert ex.attr == 'new attr'
    del ex.attr
    assert ex.attr == None

def test_getters_need_one_argument():
    @autoprop #
    class Example(object):
        def get_attr():
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

    @autoprop #
    class Example(object):
        def get_attr(self, more_info):
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_setters_need_two_arguments():
    @autoprop #
    class Example(object):
        def set_attr(self):
            self._attr = 'no args'

    ex = Example()
    ex.attr = 'attr'
    with pytest.raises(AttributeError):
        assert ex._attr != 'no args'

    @autoprop #
    class Example(object):
        def set_attr(self, new_value, more_info):
            self._attr = 'two args'

    ex = Example()
    ex.attr = 'attr'
    with pytest.raises(AttributeError):
        assert ex._attr != 'two args'

def test_deleters_need_one_argument():
    @autoprop #
    class Example(object):
        def del_attr():
            pass

    ex = Example()
    with pytest.raises(AttributeError):
        del ex.attr

    @autoprop #
    class Example(object):
        def del_attr(self, more_info):
            pass

    ex = Example()
    with pytest.raises(AttributeError):
        del ex.attr

def test_docstrings():

    @autoprop #
    class Example(object):
        def get_attr(self): #
            "get attr"
            return self._attr
        def set_attr(self, attr): #
            "set attr"
            self._attr = 'new ' + attr
        def del_attr(self): #
            "del attr"
            self._attr = None

    # The docstrings on the setter and deleter are ignored, as per the default 
    # behavior of the `property()` decorator.
    assert Example.attr.__doc__ == "get attr"

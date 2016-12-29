#!/usr/bin/env python3

import pytest
import autoprop

def test_accessors():
    @autoprop   # (no fold)
    class Example:
        def get_attr(self):
            return 'attr'

    ex = Example()
    assert ex.attr == 'attr'

    @autoprop   # (no fold)
    class Example:
        def set_attr(self, attr):
            self._attr = 'new ' + attr

    ex = Example()
    ex.attr = 'attr'
    assert ex._attr == 'new attr'

    @autoprop   # (no fold)
    class Example:
        def del_attr(self):
            self._attr = None

    ex = Example()
    del ex.attr
    assert ex._attr is None

    @autoprop   # (no fold)
    class Example:
        def get_attr(self):
            return self._attr
        def set_attr(self, attr):
            self._attr = 'new ' + attr

    ex = Example()
    ex.attr = 'attr'
    assert ex.attr == 'new attr'

    @autoprop   # (no fold)
    class Example:
        def get_attr(self):
            return self._attr
        def set_attr(self, attr):
            self._attr = 'new ' + attr
        def del_attr(self):
            self._attr = None

    ex = Example()
    ex.attr = 'attr'
    assert ex.attr == 'new attr'
    del ex.attr
    assert ex.attr is None

def test_ignore_similar_names():
    @autoprop   # (no fold)
    class Example:
        def getattr(self):
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_ignore_empty_names():
    @autoprop   # (no fold)
    class Example:
        def get_(self):
            return 'get'

    ex = Example()
    with pytest.raises(AttributeError):
        getattr(ex, '')

def test_ignore_non_methods():
    @autoprop   # (no fold)
    class Example:
        get_attr = 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_overwrite_superclass_properties():
    @autoprop   # (no fold)
    class Parent:
        def get_attr(self):
            return 'parent'

    @autoprop   # (no fold)
    class Child:
        def get_attr(self):
            return 'child'

    parent = Parent()
    child = Child()

    assert parent.attr == 'parent'
    assert child.attr == 'child'

def test_dont_overwrite_existing_attributes():
    @autoprop   # (no fold)
    class Example:
        attr = 'class var'
        def get_attr(self):
            return 'attr'

    ex = Example()
    assert ex.attr == 'class var'

def test_optional_arguments():
    @autoprop   # (no fold)
    class Example:
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
    @autoprop   # (no fold)
    class Example:
        def get_attr():
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

    @autoprop   # (no fold)
    class Example:
        def get_attr(self, more_info):
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_setters_need_two_arguments():
    @autoprop   # (no fold)
    class Example:
        def set_attr(self):
            self._attr = 'no args'

    ex = Example()
    ex.attr = 'attr'
    with pytest.raises(AttributeError):
        assert ex._attr != 'no args'

    @autoprop   # (no fold)
    class Example:
        def set_attr(self, new_value, more_info):
            self._attr = 'two args'

    ex = Example()
    ex.attr = 'attr'
    with pytest.raises(AttributeError):
        assert ex._attr != 'two args'

def test_deleters_need_one_argument():
    @autoprop   # (no fold)
    class Example:
        def del_attr():
            pass

    ex = Example()
    with pytest.raises(AttributeError):
        del ex.attr

    @autoprop   # (no fold)
    class Example:
        def del_attr(self, more_info):
            pass

    ex = Example()
    with pytest.raises(AttributeError):
        del ex.attr


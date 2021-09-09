#!/usr/bin/env python

import pytest
import autoprop

def test_metadata():
    assert hasattr(autoprop, '__doc__')
    assert hasattr(autoprop, '__version__')

def test_get():
    @autoprop
    class Example: #
        def get_attr(self): #
            return 'attr'

    ex = Example()
    assert ex.attr == 'attr'
    assert ex.attr == 'attr'

def test_set():
    @autoprop
    class Example: #
        def set_attr(self, attr): #
            self._attr = ['set', attr]

    ex = Example()
    ex.attr = 'x'
    assert ex._attr == ['set', 'x']
    ex.attr = 'y'
    assert ex._attr == ['set', 'y']

def test_del():
    @autoprop
    class Example: #
        def del_attr(self): #
            self._attr = 'del'

    ex = Example()
    del ex.attr
    assert ex._attr == 'del'
    del ex.attr
    assert ex._attr == 'del'

def test_get_set():
    @autoprop
    class Example: #
        def get_attr(self): #
            return ['get', *self._attr]
        def set_attr(self, attr): #
            self._attr = ['set', attr]

    ex = Example()
    ex.attr = 'x'
    assert ex.attr == ['get', 'set', 'x']
    ex.attr = 'y'
    assert ex.attr == ['get', 'set', 'y']

def test_get_del():
    @autoprop
    class Example: #
        def get_attr(self): #
            return ['get', *self._attr]
        def del_attr(self): #
            self._attr = ['del']

    ex = Example()
    del ex.attr
    assert ex.attr == ['get', 'del']
    del ex.attr
    assert ex.attr == ['get', 'del']

def test_get_set_del():
    @autoprop
    class Example: #
        def get_attr(self): #
            return ['get', *self._attr]
        def set_attr(self, attr): #
            self._attr = ['set', attr]
        def del_attr(self): #
            self._attr = ['del']

    ex = Example()

    ex.attr = 'x'
    assert ex.attr == ['get', 'set', 'x']
    del ex.attr
    assert ex.attr == ['get', 'del']

    ex.attr = 'y'
    assert ex.attr == ['get', 'set', 'y']
    del ex.attr
    assert ex.attr == ['get', 'del']

def test_protected():
    @autoprop
    class Example: #
        def _get_attr(self): #
            return ['get', *self._attr_helper]
        def _set_attr(self, attr): #
            self._attr_helper = ['set', attr]
        def _del_attr(self): #
            self._attr_helper = ['del']

    ex = Example()

    ex._attr = 'x'
    assert ex._attr == ['get', 'set', 'x']
    del ex._attr
    assert ex._attr == ['get', 'del']

    ex._attr = 'y'
    assert ex._attr == ['get', 'set', 'y']
    del ex._attr
    assert ex._attr == ['get', 'del']

def test_private():
    @autoprop
    class Example: #

        def __get_attr(self): #
            return ['get', *self.__attr_helper]
        def __set_attr(self, attr): #
            self.__attr_helper = ['set', attr]
        def __del_attr(self): #
            self.__attr_helper = ['del']

        def test(self): #
            # Implement the test within the class, so we have access to 
            # name-mangled attributes.

            ex.__attr = 'x'
            assert ex.__attr == ['get', 'set', 'x']
            del ex.__attr
            assert ex.__attr == ['get', 'del']

            ex.__attr = 'y'
            assert ex.__attr == ['get', 'set', 'y']
            del ex.__attr
            assert ex.__attr == ['get', 'del']

    ex = Example()
    ex.test()

def test_ignore_similar_names():
    @autoprop
    class Example: #
        def getattr(self): #
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_ignore_dunder():
    @autoprop
    class Example: #
        def __get_attr__(self): #
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_ignore_non_methods():
    @autoprop
    class Example: #
        get_attr = 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_ignore_wrong_args_get():
    @autoprop
    class Example: #
        def get_attr(): #
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

    @autoprop
    class Example: #
        def get_attr(self, more_info): #
            return 'attr'

    ex = Example()
    with pytest.raises(AttributeError):
        ex.attr

def test_ignore_wrong_args_set():
    @autoprop
    class Example: #
        def set_attr(self): #
            self._attr = 'no args'

    ex = Example()
    ex.attr = 'attr'
    with pytest.raises(AttributeError):
        assert ex._attr != 'no args'

    @autoprop
    class Example: #
        def set_attr(self, new_value, more_info): #
            self._attr = 'two args'

    ex = Example()
    ex.attr = 'attr'
    with pytest.raises(AttributeError):
        assert ex._attr != 'two args'

def test_ignore_wrong_args_del():
    @autoprop
    class Example: #
        def del_attr(): #
            pass

    ex = Example()
    with pytest.raises(AttributeError):
        del ex.attr

    @autoprop
    class Example: #
        def del_attr(self, more_info): #
            pass

    ex = Example()
    with pytest.raises(AttributeError):
        del ex.attr

def test_ignore_wrong_args_inherited():
    # Tricky case where the parent class has methods with the right names to be 
    # used in autoprops, but not the right arguments.  The child class should 
    # not use these parent class methods.

    @autoprop
    class Parent: #
        def get_attr(self, arg1):
            pass
        def set_attr(self, arg1, arg2): #
            pass

    @autoprop
    class GetChild(Parent): #
        def get_attr(self): #
            return 'attr-child'

    c = GetChild()
    assert c.attr == 'attr-child'
    with pytest.raises(AttributeError):
        c.attr = 'x'

    @autoprop
    class SetChild(Parent): #
        def set_attr(self, value): #
            self._attr = value

    c = SetChild()
    c.attr = 'x'
    assert c._attr == 'x'
    with pytest.raises(AttributeError):
        c.attr

def test_dont_overwrite_existing_attributes():
    @autoprop
    class Example: #
        attr = 'class var'
        def get_attr(self): #
            return 'attr'

    ex = Example()
    assert ex.attr == 'class var'

def test_overwrite_inherited_attributes():
    class Parent: #
        attr = 'parent'

    @autoprop
    class Child(Parent): #
        def get_attr(self): #
            return 'child'

    p = Parent()
    c = Child()

    assert p.attr == 'parent'
    assert c.attr == 'child'

def test_overwrite_inherited_autoprops_1():
    @autoprop
    class Parent: #
        def get_attr(self): #
            return 'parent'
        def get_overloaded_attr(self): #
            return 'parent'

    @autoprop
    class Child(Parent): #
        def get_overloaded_attr(self): #
            return 'child'

    p = Parent()
    c = Child()

    assert p.attr == 'parent'
    assert p.overloaded_attr == 'parent'
    assert c.attr == 'parent'
    assert c.overloaded_attr == 'child'

def test_overwrite_inherited_autoprops_2():

    @autoprop
    class Parent:
        def __init__(self): #
            self._attr = 'attr'
        def get_attr(self): #
            return self._attr
        def set_attr(self, attr): #
            self._attr = attr

    @autoprop
    class Child1(Parent):
        pass

    @autoprop
    class Child2(Parent):
        def get_attr(self): #
            return self._attr + '-get2'

    @autoprop
    class Child3(Parent):
        def get_attr(self): #
            return self._attr + '-get3'
        def set_attr(self, attr): #
            self._attr = attr + '-set3'

    assert 'attr' in Parent.__dict__
    assert 'attr' not in Child1.__dict__
    assert 'attr' in Child2.__dict__
    assert 'attr' in Child3.__dict__

    p = Parent()
    c1 = Child1()
    c2 = Child2()
    c3 = Child3()

    assert p.attr == 'attr'
    assert c1.attr == 'attr'
    assert c2.attr == 'attr-get2'
    assert c3.attr == 'attr-get3'

    c1.attr = 'xyz'
    c2.attr = 'xyz'
    c3.attr = 'xyz'

    assert c1.attr == 'xyz'
    assert c2.attr == 'xyz-get2'
    assert c3.attr == 'xyz-set3-get3'

def test_partially_inherited_autoprops():
    # If the child only implements one of the accessors, the others should be 
    # picked up from the parent class.

    @autoprop
    class Parent: #
        def get_attr(self): #
            return ['parent get', *self._attr]
        def set_attr(self, value): #
            self._attr = ['parent set', value]
        def del_attr(self): #
            self._attr = ['parent del']

    @autoprop
    class GetChild(Parent): #
        def get_attr(self): #
            return ['child get', *self._attr]

    c = GetChild()
    c.attr = 'x'
    assert c.attr == ['child get', 'parent set', 'x']
    del c.attr
    assert c.attr == ['child get', 'parent del']

    @autoprop
    class SetChild(Parent): #
        def set_attr(self, value): #
            self._attr = ['child set', value]

    c = SetChild()
    c.attr = 'x'
    assert c.attr == ['parent get', 'child set', 'x']
    del c.attr
    assert c.attr == ['parent get', 'parent del']

    @autoprop
    class DelChild(Parent): #
        def del_attr(self): #
            self._attr = ['child del']

    c = DelChild()
    c.attr = 'x'
    assert c.attr == ['parent get', 'parent set', 'x']
    del c.attr
    assert c.attr == ['parent get', 'child del']

def test_optional_arguments_1():
    @autoprop
    class Example: #
        def get_attr(self, pos=None, *args, **kwargs): #
            return ['get', *self._attr]
        def set_attr(self, new_value, pos=None, *args, **kwargs): #
            self._attr = ['set', new_value]
        def del_attr(self, pos=None, *args, **kwargs): #
            self._attr = ['del']

    ex = Example()
    ex.attr = 'x'
    assert ex.attr == ['get', 'set', 'x']
    del ex.attr
    assert ex.attr == ['get', 'del']

def test_optional_arguments_2():
    # Ok if a setter has one (or more) optional arguments in lieu of one 
    # required argument.

    @autoprop
    class Example: #
        def get_attr(self): #
            return ['get', *self._attr]
        def set_attr(self, new_value=None): #
            self._attr = ['set', new_value]

    ex = Example()
    ex.attr = 'x'
    assert ex.attr == ['get', 'set', 'x']

    @autoprop
    class Example: #
        def get_attr(self): #
            return ['get', *self._attr]
        def set_attr(self, new_value=None, other_arg=None): #
            self._attr = ['set', new_value, other_arg]

    ex = Example()
    ex.attr = 'x'
    assert ex.attr == ['get', 'set', 'x', None]

def test_keyword_only_arguments():
    # inspect.getargspec() chokes on methods with keyword-only arguments.

    @autoprop
    class Example: #
        def get_attr(self, *, pos=None): #
            return 'attr'
        def set_attr(self, *, new_value): #
            pass

    ex = Example()
    assert ex.attr == 'attr'

    # Even though the setter has one required argument, it's a named argument, 
    # so it shouldn't count and 'attr' should be defined without a setter.
    with pytest.raises(AttributeError):
        ex.attr = 'setter'

@pytest.mark.xfail
def test_classmethod():
    # I wrote this test when trying to address #1, before realizing that this 
    # probably isn't possible.  I'm leaving the test cases because the syntax 
    # is nice in principle, and maybe I'll find a way to implement it some day.

    @autoprop
    class Example: #

        @classmethod
        def get_attr(cls): #
            return ['get', self._attr]

        @classmethod
        def set_attr(cls, value): #
            cls._attr = ['set', value]

        @classmethod
        def del_attr(cls): #
            cls._attr = ['del']

    Example.attr = 'x'
    assert Example.attr == ['get', 'set', 'x']
    del Example.attr
    assert Example.attr == ['get', 'del']

@pytest.mark.xfail
def test_staticmethod():
    # I wrote this test when trying to address #1, before realizing that this 
    # probably isn't possible.  I'm leaving the test cases because the syntax 
    # is nice in principle, and maybe I'll find a way to implement it some day.

    @autoprop
    class Example: #

        @staticmethod
        def get_attr(): #
            return ['get', self._attr]

        @staticmethod
        def set_attr(value): #
            Example._attr = ['set', value]

        @staticmethod
        def del_attr(): #
            Example._attr = ['del']

    Example.attr = 'x'
    assert Example.attr == ['get', 'set', 'x']
    del Example.attr
    assert Example.attr == ['get', 'del']

@pytest.mark.parametrize(
    'decorator', [
        autoprop,
        autoprop.dynamic,
        autoprop.cache(policy='manual'),
        autoprop.cache(policy='automatic', watch=[]),
    ],
)
def test_docstrings(decorator):
    # This is a bit of a tricky case because getting the docstring requires 
    # accessing the `CachedProperty` descriptor as a class attribute, which 
    # changes how the arguments to `__get__()` need to be interpreted.

    @decorator
    class Example: #
        def get_attr(self): #
            "get attr"
            pass
        def set_attr(self, attr): #
            "set attr"
            pass
        def del_attr(self): #
            "del attr"
            pass

    ex = Example()

    # The docstrings on the setter and deleter are ignored, as per the default 
    # behavior of the `property()` decorator.
    assert Example.attr.__doc__ == "get attr"

@pytest.mark.parametrize(
    'decorator', [
        autoprop.immutable,
    ],
)
def test_docstrings_immutable(decorator):
    # See `test_docstrings()` for more info.

    @decorator
    class Example: #
        def get_attr(self): #
            "get attr"
            pass

    ex = Example()
    assert Example.attr.__doc__ == "get attr"


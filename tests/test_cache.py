#!/usr/bin/env python3

import pytest
import autoprop

def _test_policy(make_policy_test_cls, class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    MyObj = make_policy_test_cls(
            class_decorator,
            getter_decorator,
            inherit_perturbers,
    )

    o1 = MyObj(1)
    o2 = MyObj(2)

    assert o1.x == 1
    assert o2.x == 2

    # Indirectly modify the return value of `MyObj.get_x()` via a mutable 
    # dictionary.  This avoids triggering any of the conditions that would 
    # invalidate the cache.
    o1.d['x'] = 3

    perturb(o1)

    assert o1.x == (3 if recalculate else 1)
    assert o2.x == 2

def make_policy_test_cls(class_decorator, getter_decorator, inherit_perturbers):

    if inherit_perturbers:
        @autoprop
        class MyParent:

            def set_x(self, x):
                pass

            def del_x(self):
                pass

            def set_y(self, y):
                pass

            def del_y(self):
                pass

            @autoprop.refresh
            def refresh(self):
                pass

            @classmethod
            @autoprop.refresh
            def refresh_cls(cls):
                pass

            @staticmethod
            @autoprop.refresh
            def refresh_static():
                pass

        @class_decorator
        class MyObj(MyParent):

            def __init__(self, x):
                self.d = {'x': x}

            @getter_decorator
            def get_x(self):
                return self.d['x']

    else:
        @class_decorator
        class MyObj:

            def __init__(self, x):
                self.d = {'x': x}

            @getter_decorator
            def get_x(self):
                return self.d['x']

            def set_x(self, x):
                pass

            def del_x(self):
                pass

            def set_y(self, y):
                pass

            def del_y(self):
                pass

            @autoprop.refresh
            def refresh(self):
                pass

            @classmethod
            @autoprop.refresh
            def refresh_cls(cls):
                pass

            @staticmethod
            @autoprop.refresh
            def refresh_static():
                pass

    return MyObj

def make_policy_test_cls_read_only(class_decorator, getter_decorator, inherit_perturbers):

    if inherit_perturbers:
        @autoprop
        class MyParent:

            def set_y(self, y):
                pass

            def del_y(self):
                pass

            @autoprop.refresh
            def refresh(self):
                pass

            @classmethod
            @autoprop.refresh
            def refresh_cls(cls):
                pass

            @staticmethod
            @autoprop.refresh
            def refresh_static():
                pass

        @class_decorator
        class MyObj(MyParent):

            def __init__(self, x):
                self.d = {'x': x}

            @getter_decorator
            def get_x(self):
                return self.d['x']

    else:
        @class_decorator
        class MyObj:

            def __init__(self, x):
                self.d = {'x': x}

            @getter_decorator
            def get_x(self):
                return self.d['x']

            def set_y(self, y):
                pass

            def del_y(self):
                pass

            @autoprop.refresh
            def refresh(self):
                pass

            @classmethod
            @autoprop.refresh
            def refresh_cls(cls):
                pass

            @staticmethod
            @autoprop.refresh
            def refresh_static():
                pass

    return MyObj

def make_policy_decorators(policy):
    return [
            (
                autoprop(cache=True, policy=policy),
                noop,
            ), (
                autoprop,
                autoprop.cache(policy=policy),
            )
    ]

def set_x(obj):
    obj.x = 0

def del_x(obj):
    del obj.x

def set_y(obj):
    obj.y = 0

def del_y(obj):
    del obj.y

def set_z(obj):
    obj.z = 0

def refresh(obj):
    obj.refresh()

def refresh_cls(obj):
    obj.refresh_cls()

def refresh_static(obj):
    obj.refresh_static()

def noop(obj):
    return obj


@pytest.mark.parametrize(
        'class_decorator, getter_decorator', 
            make_policy_decorators('read-only'),
)
@pytest.mark.parametrize(
        'perturb, recalculate', [
            (autoprop.clear_cache, True),
            (set_y, False),
            (del_y, False),
            (set_z, False),
            (refresh, False),
            (refresh_cls, False),
            (refresh_static, False),
            (noop, False),
        ],
)
@pytest.mark.parametrize(
        'inherit_perturbers', [False, True],
)
def test_policy_read_only(class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    _test_policy(
            make_policy_test_cls_read_only,
            class_decorator,
            getter_decorator,
            perturb,
            recalculate,
            inherit_perturbers,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator',
            make_policy_decorators('property'),
)
@pytest.mark.parametrize(
        'perturb, recalculate', [
            (autoprop.clear_cache, True),
            (set_x, True),
            (del_x, True),
            (set_y, False),
            (del_y, False),
            (set_z, False),
            (refresh, False),
            (refresh_cls, False),
            (refresh_static, False),
            (noop, False),
        ],
)
@pytest.mark.parametrize(
        'inherit_perturbers', [False, True],
)
def test_policy_property(class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    _test_policy(
            make_policy_test_cls,
            class_decorator,
            getter_decorator,
            perturb,
            recalculate,
            inherit_perturbers,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator', [
            *make_policy_decorators('object'),
            (autoprop, autoprop.cache),
            (autoprop(cache=True), noop),
        ],
)
@pytest.mark.parametrize(
        'perturb, recalculate', [
            (autoprop.clear_cache, True),
            (set_x, True),
            (del_x, True),
            (set_y, True),
            (del_y, True),
            (set_z, True),
            (refresh, True),
            (refresh_cls, False),
            (refresh_static, False),
            (noop, False),
        ],
)
@pytest.mark.parametrize(
        'inherit_perturbers', [False, True],
)
def test_policy_object(class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    _test_policy(
            make_policy_test_cls,
            class_decorator,
            getter_decorator,
            perturb,
            recalculate,
            inherit_perturbers,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator', 
            make_policy_decorators('class'),
)
@pytest.mark.parametrize(
        'perturb, recalculate', [
            (autoprop.clear_cache, True),
            (set_x, True),
            (del_x, True),
            (set_y, True),
            (del_y, True),
            (set_z, True),
            (refresh, True),
            (refresh_cls, True),
            (refresh_static, True),
            (noop, False),
        ],
)
@pytest.mark.parametrize(
        'inherit_perturbers', [False, True],
)
def test_policy_class(class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    _test_policy(
            make_policy_test_cls,
            class_decorator,
            getter_decorator,
            perturb,
            recalculate,
            inherit_perturbers,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator', [
            (autoprop, noop),
            (autoprop, autoprop.cache(policy='dynamic')),
            (autoprop, autoprop.dynamic),
            (autoprop(cache=True), autoprop.cache(policy='dynamic')),
            (autoprop(cache=True), autoprop.dynamic),
        ],
)
@pytest.mark.parametrize(
        'perturb, recalculate', [
            (autoprop.clear_cache, True),
            (set_x, True),
            (del_x, True),
            (set_y, True),
            (del_y, True),
            (set_z, True),
            (refresh, True),
            (refresh_cls, True),
            (refresh_static, True),
            (noop, True),
        ],
)
@pytest.mark.parametrize(
        'inherit_perturbers', [False, True],
)
def test_policy_dynamic(class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    _test_policy(
            make_policy_test_cls,
            class_decorator,
            getter_decorator,
            perturb,
            recalculate,
            inherit_perturbers,
    )


def test_cache_inheritance():
    # The child class determines whether or not the attribute is cached.

    @autoprop
    class Parent:

        def __init__(self, v=0): #
            self._w = v
            self._x = v
            self._y = v
            self._z = v

        @autoprop.cache
        def get_super_cache(self): #
            self._w += 1
            return self._w

        @autoprop.cache
        def get_parent_cache(self): #
            self._x += 1
            return self._x

        def get_child_cache(self): #
            self._y += 1
            return self._y

        @autoprop.cache
        def get_both_cache(self): #
            self._z += 1
            return self._z

    @autoprop
    class Child(Parent):

        def get_parent_cache(self): #
            self._x += 1
            return self._x

        @autoprop.cache
        def get_child_cache(self): #
            self._y += 1
            return self._y

        @autoprop.cache
        def get_both_cache(self): #
            self._z += 1
            return self._z

    p = Parent()
    c = Child(10)

    assert p.parent_cache == 1
    assert p.parent_cache == 1
    assert c.parent_cache == 11
    assert c.parent_cache == 12

    assert p.child_cache == 1
    assert p.child_cache == 2
    assert c.child_cache == 11
    assert c.child_cache == 11

    assert p.both_cache == 1
    assert p.both_cache == 1
    assert c.both_cache == 11
    assert c.both_cache == 11

    assert p.super_cache == 1
    assert p.super_cache == 1
    assert c.super_cache == 11
    assert c.super_cache == 11

def test_read_only_setter_err():
    with pytest.raises(ValueError) as err:

        @autoprop
        class MyObj:

            @autoprop.cache(policy='read-only')
            def get_x(self):
                pass

            def set_x(self, x):
                pass

    assert err.match(r"can't specify setter for read-only property: .*MyObj\.x")
    assert err.match(r"read-only getter: .*MyObj\.get_x")
    assert err.match(r"setter: .*MyObj.set_x")

def test_read_only_deleter_err():
    with pytest.raises(ValueError) as err:

        @autoprop
        class MyObj:

            @autoprop.cache(policy='read-only')
            def get_x(self):
                pass

            def del_x(self):
                pass

    assert err.match(r"can't specify deleter for read-only property: .*MyObj\.x")
    assert err.match(r"read-only getter: .*MyObj\.get_x")
    assert err.match(r"deleter: .*MyObj.del_x")

def test_cache_non_getter_err():
    with pytest.raises(ValueError) as err:

        @autoprop
        class MyObj:

            @autoprop.cache
            def non_getter(self):
                pass

    assert err.match(r"can't set a caching policy for .*MyObj\.non_getter; it's not a getter")

def test_unknown_policy_err():
    with pytest.raises(ValueError) as err:

        @autoprop(cache=True, policy='unknown')
        class MyObj:
            pass

    assert err.match(r"unknown policy 'unknown', expected one of")

    with pytest.raises(ValueError) as err:

        @autoprop
        class MyObj:

            @autoprop.cache(policy='unknown')
            def get_x(self):
                pass

    assert err.match(r"unknown policy 'unknown', expected one of")




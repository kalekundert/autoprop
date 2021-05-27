#!/usr/bin/env python3

import pytest
import autoprop
from functools import partial

def _test_policy(make_policy_test_cls, class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    MyObj = make_policy_test_cls(
            class_decorator,
            getter_decorator,
            inherit_perturbers,
    )

    o1 = MyObj(1)
    o2 = MyObj(2)

    assert o1.x == o1.get_x() == 1
    assert o2.x == o2.get_x() == 2

    # Indirectly modify the return value of `MyObj.get_x()` via a mutable 
    # dictionary.  This avoids triggering any of the conditions that would 
    # invalidate the cache.
    o1.d['x'] = 3

    perturb(o1)

    assert o1.x == o1.get_x() == (3 if recalculate else 1)
    assert o2.x == o2.get_x() == 2

def make_policy_test_cls(class_decorator, getter_decorator, inherit_perturbers, include_setters=True, include_refresh=True):

    if inherit_perturbers:
        @autoprop.dynamic
        class MyParent:

            if include_setters:
                def set_x(self, x):
                    pass

                def del_x(self):
                    pass

                def set_y(self, y):
                    pass

                def del_y(self):
                    pass

            if include_refresh:
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

            def method(self):
                pass

            @classmethod
            def method_cls(cls):
                pass

            @staticmethod
            def method_static():
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

            if include_setters:
                def set_x(self, x):
                    pass

                def del_x(self):
                    pass

                def set_y(self, y):
                    pass

                def del_y(self):
                    pass

            if include_refresh:
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

            def method(self):
                pass

            @classmethod
            def method_cls(cls):
                pass

            @staticmethod
            def method_static():
                pass

    return MyObj

def make_policy_decorators(policy):
    return [
            (
                autoprop.cache(policy=policy),
                noop,
            ), (
                autoprop.cache,
                autoprop.cache(policy=policy),
            ), (
                autoprop.cache(),
                autoprop.cache(policy=policy),
            ), (
                autoprop.cache,
                autoprop.policy(policy),
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

def method(obj):
    obj.method()

def method_cls(obj):
    obj.method_cls()

def method_static(obj):
    obj.method_static()

def noop(obj):
    return obj


@pytest.mark.parametrize(
        'class_decorator, getter_decorator', [
            *make_policy_decorators('immutable'),
            (autoprop.dynamic, autoprop.immutable),
            (autoprop.immutable, noop),
        ],
)
@pytest.mark.parametrize(
        'perturb, recalculate', [
            (autoprop.clear_cache, True),
            (set_z, False),
            (refresh, False),
            (refresh_cls, False),
            (refresh_static, False),
            (method, False),
            (method_cls, False),
            (method_static, False),
            (noop, False),
        ],
)
@pytest.mark.parametrize(
        'inherit_perturbers', [False, True],
)
def test_policy_immutable(class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    _test_policy(
            partial(make_policy_test_cls, include_setters=False),
            class_decorator,
            getter_decorator,
            perturb,
            recalculate,
            inherit_perturbers,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator', [
            *make_policy_decorators('property'),
            (autoprop.cache, noop),
            (autoprop.cache(), noop),
        ],
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
            (method, False),
            (method_cls, False),
            (method_static, False),
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
        'class_decorator, getter_decorator',
            make_policy_decorators('object'),
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
            (method, False),
            (method_cls, False),
            (method_static, False),
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
            (method, False),
            (method_cls, False),
            (method_static, False),
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
            *make_policy_decorators('dynamic'),
            (autoprop.cache, autoprop.dynamic),
            (autoprop.dynamic, noop),
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
            (method, True),
            (method_cls, True),
            (method_static, True),
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

@pytest.mark.parametrize(
        'class_decorator, getter_decorator', [
            (autoprop, noop)
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
            (method, True),
            (method_cls, True),
            (method_static, True),
            (noop, True),
        ],
)
@pytest.mark.parametrize(
        'inherit_perturbers', [False, True],
)
def test_policy_no_cache(class_decorator, getter_decorator, perturb, recalculate, inherit_perturbers):
    _test_policy(
            partial(make_policy_test_cls, include_refresh=False),
            class_decorator,
            getter_decorator,
            perturb,
            recalculate,
            inherit_perturbers,
    )


def test_cache_inheritance():
    # The child class determines whether or not the attribute is cached.

    @autoprop.dynamic
    class Parent:

        def __init__(self, x): #
            self.d = {'x': x}

        @autoprop.cache
        def get_super_cache(self): #
            return self.d['x']

        @autoprop.cache
        def get_parent_cache(self): #
            return self.d['x']

        def get_child_cache(self): #
            return self.d['x']

        @autoprop.cache
        def get_both_cache(self): #
            return self.d['x']

    @autoprop.dynamic
    class Child(Parent):

        def get_parent_cache(self): #
            return self.d['x']

        @autoprop.cache
        def get_child_cache(self): #
            return self.d['x']

        @autoprop.cache
        def get_both_cache(self): #
            return self.d['x']

    p = Parent(1)
    c = Child(2)

    assert p.super_cache == 1
    assert p.parent_cache == 1
    assert p.child_cache == 1
    assert p.both_cache == 1

    assert c.super_cache == 2
    assert c.parent_cache == 2
    assert c.child_cache == 2
    assert c.both_cache == 2

    p.d['x'] = 3
    c.d['x'] = 4

    assert p.super_cache == 1
    assert p.parent_cache == 1
    assert p.child_cache == 3
    assert p.both_cache == 1

    assert c.super_cache == 2
    assert c.parent_cache == 4
    assert c.child_cache == 2
    assert c.both_cache == 2

def test_inherit_uncached():
    # Note that `Child` defines `set_x()` but not `get_x()`.  This means that 
    # it will create an `x` property, but it will use `Parent.get_x()` when 
    # doing so.  Because `get_x()` is defined in a class without caching, that 
    # behavior should extend to the new property, even though getters defined 
    # in `Child` are cached by default.

    @autoprop
    class Parent:

        def __init__(self, x):
            self.d = {'x': x}

        def get_x(self):
            return self.d['x']


    @autoprop.cache
    class Child(Parent):

        def set_x(self, x):
            pass

        def get_y(self):
            return self.d['x']


    p = Parent(1)
    c = Child(2)

    assert p.x == 1
    assert c.x == 2
    assert c.y == 2

    p.d['x'] = 3
    c.d['x'] = 4

    assert p.x == 3  # not cached
    assert c.x == 4  # not cached
    assert c.y == 2  # cached

def test_dont_cache_getters_with_extra_args():
    # Normally the getter function and the property are both cached, but 
    # caching has to be disabled in the case where the getter is directly 
    # called with optional arguments.

    @autoprop.cache
    class MyObj:

        def get_x(self, i=0):
            return self.d['x'][i]

    obj = MyObj()
    obj.d = {'x': [1, 2]}

    assert obj.x == 1
    assert obj.get_x() == 1
    assert obj.get_x(0) == 1
    assert obj.get_x(1) == 2

    obj.d['x'] = [3, 4]

    assert obj.x == 1
    assert obj.get_x() == 1
    assert obj.get_x(0) == 3
    assert obj.get_x(1) == 4

def test_cache_disabled_getter_err():
    with pytest.raises(ValueError) as err:

        @autoprop
        class MyObj:

            @autoprop.cache
            def get_x(self):
                pass

    assert err.match(r"cache disabled: can't specify cache policies")
    assert err.match(r"class: .*MyObj")
    assert err.match(r"method: .*MyObj.get_x")

def test_cache_disabled_refresh_err():
    with pytest.raises(ValueError) as err:

        @autoprop
        class MyObj:

            @autoprop.refresh
            def method(self):
                pass

    assert err.match(r"cache disabled: can't use `@autoprop.refresh`")
    assert err.match(r"class: .*MyObj")
    assert err.match(r"method: .*MyObj.method")

def test_cache_disabled_refresh_cls_err():
    with pytest.raises(ValueError) as err:

        @autoprop
        class MyObj:

            @classmethod
            @autoprop.refresh
            def method(cls):
                pass

    assert err.match(r"cache disabled: can't use `@autoprop.refresh`")
    assert err.match(r"class: .*MyObj")
    assert err.match(r"method: .*MyObj.method")

def test_read_only_setter_err():
    with pytest.raises(ValueError) as err:

        @autoprop.cache
        class MyObj:

            @autoprop.cache(policy='immutable')
            def get_x(self):
                pass

            def set_x(self, x):
                pass

    assert err.match(r"can't specify setter for immutable property")
    assert err.match(r"property: .*MyObj\.x")
    assert err.match(r"immutable getter: .*MyObj\.get_x")
    assert err.match(r"setter: .*MyObj.set_x")

def test_read_only_deleter_err():
    with pytest.raises(ValueError) as err:

        @autoprop.cache
        class MyObj:

            @autoprop.cache(policy='immutable')
            def get_x(self):
                pass

            def del_x(self):
                pass

    assert err.match(r"can't specify deleter for immutable property")
    assert err.match(r"property: .*MyObj\.x")
    assert err.match(r"immutable getter: .*MyObj\.get_x")
    assert err.match(r"deleter: .*MyObj.del_x")

def test_cache_non_getter_err():
    with pytest.raises(ValueError) as err:

        @autoprop.cache
        class MyObj:

            @autoprop.cache
            def non_getter(self):
                pass

    assert err.match(r"can't cache .*MyObj\.non_getter; it's not a getter")

def test_unknown_policy_err():
    with pytest.raises(ValueError) as err:

        @autoprop.cache(policy='unknown')
        class MyObj:
            pass

    assert err.match(r"unknown policy 'unknown', expected one of")

    with pytest.raises(ValueError) as err:

        @autoprop.cache
        class MyObj:

            @autoprop.cache(policy='unknown')
            def get_x(self):
                pass

    assert err.match(r"unknown policy 'unknown', expected one of")


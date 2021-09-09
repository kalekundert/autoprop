#!/usr/bin/env python3

import pytest
import autoprop
from enum import Enum, auto
from contextlib import suppress as nullcontext

class Values(Enum):
    CACHE = auto()
    REFRESH = auto()
    PERTURB = auto()
    UNRELATED = auto()

def _test_policy(test_cls, perturb, expected):
    o1 = test_cls(Values.CACHE)
    o2 = test_cls(Values.UNRELATED)

    assert o1.x == o1.get_x() == Values.CACHE
    assert o2.x == o2.get_x() == Values.UNRELATED

    o1.secretly_update_x(Values.REFRESH)

    perturb(o1)

    assert o1.x == o1.get_x() == expected
    assert o2.x == o2.get_x() == Values.UNRELATED

    # The getter method might get overridden, so make sure features like 
    # docstrings aren't lost in the process.
    assert o1.get_x.__doc__ == "get x"
    assert o2.get_x.__doc__ == "get x"

def make_policy_test_cls(class_decorator, getter_decorator, inherit_methods, mutator_impl):

    if inherit_methods:
        @autoprop.dynamic
        class MyParent:

            def __init__(self, x):
                self._x = x
                self._y = None
                self.z = None

            @autoprop.dynamic
            def get_y(self):
                return self._y

            def set_y(self, y):
                self._y = y

            def del_y(self):
                del self._y

            if mutator_impl == 'internal':
                def set_x(self, x):
                    self._x = x

                def del_x(self):
                    del self._x

            if mutator_impl == 'cache':
                def set_x(self, x):
                    autoprop.set_cached_attr(self, 'x', x)

                def del_x(self):
                    autoprop.del_cached_attr(self, 'x')


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
                super().__init__(x)

            @getter_decorator
            def get_x(self):
                "get x"
                return self._x

            def secretly_update_x(self, x):
                self._x = x

    else:
        class MyParent:
            pass

        @class_decorator
        class MyObj(MyParent):

            def __init__(self, x):
                self._x = x
                self._y = None
                self.z = None

            @getter_decorator
            def get_x(self):
                "get x"
                return self._x

            def secretly_update_x(self, x):
                self._x = x

            if mutator_impl == 'internal':
                def set_x(self, x):
                    self._x = x

                def del_x(self):
                    del self._x

            if mutator_impl == 'cache':
                def set_x(self, x):
                    autoprop.set_cached_attr(self, 'x', x)

                def del_x(self):
                    autoprop.del_cached_attr(self, 'x')

            @autoprop.dynamic
            def get_y(self):
                return self._y

            def set_y(self, y):
                self._y = y

            def del_y(self):
                del self._y

            def method(self):
                pass

            @classmethod
            def method_cls(cls):
                pass

            @staticmethod
            def method_static():
                pass

    return MyObj

def make_policy_decorators(policy, **kwargs):
    if policy == 'dynamic':
        diff_default = autoprop.cache
    else:
        diff_default = autoprop

    return [
            (
                autoprop.cache(policy=policy, **kwargs),
                noop,
            ), (
                autoprop,
                autoprop.cache(policy=policy, **kwargs),
            ), (
                diff_default,
                autoprop.cache(policy=policy, **kwargs),
            ), (
                diff_default,
                autoprop.policy(policy, **kwargs),
            )
    ]

def set_x(obj):
    obj.x = Values.PERTURB

def del_x(obj):
    del obj.x

def set_y(obj):
    obj.y = Values.UNRELATED

def reset_y(obj):
    y = obj.y
    obj.y = Values.UNRELATED
    obj.y = y

def del_y(obj):
    del obj.y

def set_z(obj):
    obj.z = Values.UNRELATED

def reset_z(obj):
    z = obj.z
    obj.z = Values.UNRELATED
    obj.z = z

def del_z(obj):
    del obj.z

def set_attr_cls(obj):
    obj.__class__.attr_cls = Values.UNRELATED

def set_attr_parent_cls(obj):
    obj.__class__.__mro__[0].attr_parent_cls = Values.UNRELATED

def cache_clear(obj):
    autoprop.clear_cache(obj)

def cache_get(obj):
    autoprop.get_cached_attr(obj, 'x', None)

def cache_set(obj):
    autoprop.set_cached_attr(obj, 'x', Values.PERTURB)

def cache_del(obj):
    try:
        autoprop.del_cached_attr(obj, 'x')
    except AttributeError:
        pass

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
            *make_policy_decorators('dynamic'),
            (autoprop, noop),
            (autoprop, autoprop.dynamic),
            (autoprop.dynamic, noop),
        ],
)
@pytest.mark.parametrize(
        'perturb, expected', [
            (set_x, Values.PERTURB),
            (set_y, Values.REFRESH),
            (del_y, Values.REFRESH),
            (set_z, Values.REFRESH),
            (del_z, Values.REFRESH),
            (set_attr_cls, Values.REFRESH),
            (set_attr_parent_cls, Values.REFRESH),
            (cache_clear, Values.REFRESH),
            (cache_get, Values.REFRESH),
            (cache_set, Values.REFRESH),
            (cache_del, Values.REFRESH),
            (method, Values.REFRESH),
            (method_cls, Values.REFRESH),
            (method_static, Values.REFRESH),
            (noop, Values.REFRESH),
        ],
)
@pytest.mark.parametrize(
        'inherit_methods', [False, True],
)
def test_policy_dynamic(class_decorator, getter_decorator, inherit_methods, perturb, expected):
    _test_policy(
            make_policy_test_cls(
                class_decorator,
                getter_decorator,
                inherit_methods,
                mutator_impl='internal',
            ),
            perturb,
            expected,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator', [
            *make_policy_decorators('overwrite'),
            (autoprop.cache, noop),
            (autoprop.cache(), noop),
            (autoprop, autoprop.cache),
            (autoprop, autoprop.cache()),
        ],
)
@pytest.mark.parametrize(
        'perturb, expected', [
            (set_x, Values.PERTURB),
            (del_x, Values.REFRESH),
            (set_y, Values.CACHE),
            (del_y, Values.CACHE),
            (set_z, Values.CACHE),
            (del_z, Values.CACHE),
            (set_attr_cls, Values.CACHE),
            (set_attr_parent_cls, Values.CACHE),
            (cache_clear, Values.CACHE),
            (cache_get, Values.CACHE),
            (cache_set, Values.CACHE),
            (cache_del, Values.CACHE),
            (method, Values.CACHE),
            (method_cls, Values.CACHE),
            (method_static, Values.CACHE),
            (noop, Values.CACHE),
        ],
)
@pytest.mark.parametrize(
        'inherit_methods', [False, True],
)
def test_policy_overwrite(class_decorator, getter_decorator, inherit_methods, perturb, expected):
    _test_policy(
            make_policy_test_cls(
                class_decorator,
                getter_decorator,
                inherit_methods,
                mutator_impl=False,
            ),
            perturb,
            expected,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator',
            make_policy_decorators('manual', provide_mutators=True),
)
@pytest.mark.parametrize(
        'perturb, expected', [
            (set_x, Values.PERTURB),
            (del_x, Values.REFRESH),
            (set_y, Values.CACHE),
            (del_y, Values.CACHE),
            (set_z, Values.CACHE),
            (del_z, Values.CACHE),
            (set_attr_cls, Values.CACHE),
            (set_attr_parent_cls, Values.CACHE),
            (cache_clear, Values.REFRESH),
            (cache_get, Values.CACHE),
            (cache_set, Values.PERTURB),
            (cache_del, Values.REFRESH),
            (method, Values.CACHE),
            (method_cls, Values.CACHE),
            (method_static, Values.CACHE),
            (noop, Values.CACHE),
        ],
)
@pytest.mark.parametrize(
        'inherit_methods', [False, True],
)
@pytest.mark.parametrize(
        'mutator_impl', [False, 'cache'],
)
def test_policy_manual(class_decorator, getter_decorator, inherit_methods, mutator_impl, perturb, expected):
    _test_policy(
            make_policy_test_cls(
                class_decorator,
                getter_decorator,
                inherit_methods,
                mutator_impl,
            ),
            perturb,
            expected,
    )

@pytest.mark.parametrize(
        'watch, perturb, expected', [
            ([], set_x, Values.PERTURB),
            ([], del_x, Values.REFRESH),
            ([], set_y, Values.CACHE),
            ([], del_y, Values.CACHE),
            (['y'], set_y, Values.REFRESH),
            (['y'], reset_y, Values.CACHE),
            (['y'], del_y, Values.REFRESH),
            (['y'], noop, Values.CACHE),
            ([], set_z, Values.CACHE),
            ([], del_z, Values.CACHE),
            (['z'], set_z, Values.REFRESH),
            (['z'], reset_z, Values.CACHE),
            (['z'], del_z, Values.REFRESH),
            (['z'], noop, Values.CACHE),
            ([lambda obj: obj.z], set_z, Values.REFRESH),
            ([lambda obj: obj.z], reset_z, Values.CACHE),
            ([lambda obj: obj.z], del_z, Values.REFRESH),
            ([lambda obj: obj.z], noop, Values.CACHE),
            ([], set_attr_cls, Values.CACHE),
            (['attr_cls'], set_attr_cls, Values.REFRESH),
            (['attr_cls'], noop, Values.CACHE),
            ([], set_attr_parent_cls, Values.CACHE),
            (['attr_parent_cls'], set_attr_parent_cls, Values.REFRESH),
            (['attr_parent_cls'], noop, Values.CACHE),
            ([], cache_clear, Values.REFRESH),
            ([], cache_get, Values.CACHE),
            ([], cache_set, Values.PERTURB),
            ([], cache_del, Values.REFRESH),
            ([], method, Values.CACHE),
            ([], method_cls, Values.CACHE),
            ([], method_static, Values.CACHE),
            ([], noop, Values.CACHE),
            (['undefined'], noop, Values.CACHE),
        ],
)
@pytest.mark.parametrize(
        'inherit_methods', [False, True],
)
@pytest.mark.parametrize(
        'mutator_impl', [False, 'cache'],
)
def test_policy_automatic(inherit_methods, mutator_impl, watch, perturb, expected):
    _test_policy(
            make_policy_test_cls(
                autoprop,
                autoprop.cache(policy='automatic', watch=watch, provide_mutators=True),
                inherit_methods,
                mutator_impl=mutator_impl,
            ),
            perturb,
            expected,
    )

@pytest.mark.parametrize(
        'class_decorator, getter_decorator', [
            *make_policy_decorators('immutable'),
            (autoprop, autoprop.immutable),
            (autoprop.immutable, noop),
        ],
)
@pytest.mark.parametrize(
        'perturb, expected', [
            (set_y, Values.CACHE),
            (del_y, Values.CACHE),
            (set_z, Values.CACHE),
            (del_z, Values.CACHE),
            (set_attr_cls, Values.CACHE),
            (set_attr_parent_cls, Values.CACHE),
            (cache_clear, Values.REFRESH),
            (cache_get, Values.CACHE),
            (cache_set, Values.PERTURB),
            (cache_del, Values.REFRESH),
            (method, Values.CACHE),
            (method_cls, Values.CACHE),
            (method_static, Values.CACHE),
            (cache_clear, Values.REFRESH),
            (cache_get, Values.CACHE),
            (cache_set, Values.PERTURB),
            (cache_del, Values.REFRESH),
            (noop, Values.CACHE),
        ],
)
@pytest.mark.parametrize(
        'inherit_methods', [False, True],
)
def test_policy_immutable(class_decorator, getter_decorator, inherit_methods, perturb, expected):
    _test_policy(
            make_policy_test_cls(
                class_decorator,
                getter_decorator,
                inherit_methods,
                mutator_impl=False,
            ),
            perturb,
            expected,
    )


def test_cache_inheritance():
    # The child class determines whether or not the attribute is cached.

    @autoprop
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

    @autoprop
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


    @autoprop.cache(policy='manual')
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

@pytest.mark.parametrize(
        'class_decorator, getter_decorator, mutable', [
            (
                autoprop.cache(policy='manual'),
                noop,
                False
            ), (
                autoprop.cache(policy='manual', provide_mutators=False),
                noop,
                False
            ), (
                autoprop.cache(policy='manual', provide_mutators=True),
                noop,
                True,
            ), (
                autoprop,
                autoprop.cache(policy='manual'),
                False
            ), (
                autoprop,
                autoprop.cache(policy='manual', provide_mutators=False),
                False
            ), (
                autoprop,
                autoprop.cache(policy='manual', provide_mutators=True),
                True,
            ), (
                autoprop.cache(policy='manual', provide_mutators=True),
                autoprop.cache(policy='manual'),
                True,
            ), (
                autoprop.cache(policy='automatic', watch=[], provide_mutators=True),
                autoprop.cache(policy='manual'),
                True,
            ), (
                autoprop.cache(policy='automatic', watch=[]),
                noop,
                False
            ), (
                autoprop.cache(policy='automatic', watch=[], provide_mutators=False),
                noop,
                False
            ), (
                autoprop.cache(policy='automatic', watch=[], provide_mutators=True),
                noop,
                True,
            ), (
                autoprop,
                autoprop.cache(policy='automatic', watch=[]),
                False
            ), (
                autoprop,
                autoprop.cache(policy='automatic', watch=[], provide_mutators=False),
                False
            ), (
                autoprop,
                autoprop.cache(policy='automatic', watch=[], provide_mutators=True),
                True,
            ), (
                autoprop.cache(policy='automatic', watch=[], provide_mutators=True),
                autoprop.cache(policy='automatic', watch=[]),
                True,
            ), (
                autoprop.cache(policy='manual', provide_mutators=True),
                autoprop.cache(policy='automatic', watch=[]),
                True,
            ),
        ],
)
def test_provide_mutators(class_decorator, getter_decorator, mutable):

    @class_decorator
    class MyObj:

        @getter_decorator
        def get_x(self):
            pass

    obj = MyObj()

    with nullcontext() if mutable else pytest.raises(AttributeError):
        obj.x = 1

    with nullcontext() if mutable else pytest.raises(AttributeError):
        del obj.x

@pytest.mark.parametrize(
        'getter_decorator', [
            autoprop.cache(policy='manual', provide_mutators=False),
            autoprop.cache(policy='manual', provide_mutators=True),
            autoprop.cache(policy='automatic', provide_mutators=False, watch=[]),
            autoprop.cache(policy='automatic', provide_mutators=True, watch=[]),
        ]
)
def test_override_provided_mutators(getter_decorator):

    @autoprop
    class MyObj:

        def __init__(self, x):
            self.d = {'x': x}
        
        @getter_decorator
        def get_x(self):
            return ['get', self.d['x']]

        def set_x(self, x):
            autoprop.set_cached_attr(self, 'x', ['set', x])

        def del_x(self):
            autoprop.set_cached_attr(self, 'x', ['del'])


    obj = MyObj(1)
    assert obj.x == ['get', 1]

    obj.d['x'] = 2
    assert obj.x == ['get', 1]

    obj.x = 3
    assert obj.x == ['set', 3]

    del obj.x
    assert obj.x == ['del']

def test_manipulate_cached_attr():

    @autoprop.immutable
    class MyObj:

        def __init__(self, x):
            self.d = {'x': x}

        def get_x(self):
            return self.d['x']

    obj = MyObj(1)

    assert obj.x == 1

    obj.d['x'] = 2

    assert obj.x == 1
    assert autoprop.get_cached_attr(obj, 'x') == 1
    assert autoprop.get_cached_attr(obj, 'y', None) == None
    with pytest.raises(AttributeError):
        autoprop.get_cached_attr(obj, 'y')

    autoprop.set_cached_attr(obj, 'x', 3)

    assert obj.x == 3
    assert autoprop.get_cached_attr(obj, 'x') == 3

    autoprop.del_cached_attr(obj, 'x')

    assert obj.x == 2
    assert autoprop.get_cached_attr(obj, 'x') == 2

@pytest.mark.parametrize(
        'getter_decorator', [
            autoprop.cache,
            autoprop.immutable,
        ]
)
def test_read_only_setter_err(getter_decorator):
    with pytest.raises(ValueError) as err:

        @autoprop.cache
        class MyObj:

            @getter_decorator
            def get_x(self):
                pass

            def set_x(self, x):
                pass

    assert err.match(r"can't specify setter")
    assert err.match(r"property: .*MyObj\.x")
    assert err.match(r"getter: .*MyObj\.get_x")
    assert err.match(r"setter: .*MyObj.set_x")

@pytest.mark.parametrize(
        'getter_decorator', [
            autoprop.cache,
            autoprop.immutable,
        ]
)
def test_read_only_deleter_err(getter_decorator):
    with pytest.raises(ValueError) as err:

        @autoprop.cache
        class MyObj:

            @getter_decorator
            def get_x(self):
                pass

            def del_x(self):
                pass

    assert err.match(r"can't specify deleter")
    assert err.match(r"property: .*MyObj\.x")
    assert err.match(r"getter: .*MyObj\.get_x")
    assert err.match(r"deleter: .*MyObj.del_x")

def test_cache_non_getter_err():
    with pytest.raises(ValueError) as err:

        @autoprop
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

        @autoprop
        class MyObj:

            @autoprop.cache(policy='unknown')
            def get_x(self):
                pass

    assert err.match(r"unknown policy 'unknown', expected one of")

def test_automatic_no_watch_err():
    with pytest.raises(TypeError) as err:

        @autoprop
        class MyObj:

            @autoprop.cache(policy='automatic')
            def get_x(self):
                pass

def test_make_policy_extra_args_err():
    from autoprop.policies import ManualPolicy, _make_policy

    with pytest.raises(TypeError):
        _make_policy(ManualPolicy(), provide_mutators=True)


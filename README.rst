*******************************************************
``autoprop`` --- Infer properties from accessor methods
*******************************************************
.. image:: https://img.shields.io/pypi/v/autoprop.svg
   :alt: Last release
   :target: https://pypi.python.org/pypi/autoprop

.. image:: https://img.shields.io/pypi/pyversions/autoprop.svg
   :alt: Python version
   :target: https://pypi.python.org/pypi/autoprop

.. image:: 
   https://img.shields.io/github/workflow/status/kalekundert/autoprop/Test%20and%20release/master
   :alt: Test status
   :target: https://github.com/kalekundert/autoprop/actions

.. image:: https://img.shields.io/coveralls/kalekundert/autoprop.svg
   :alt: Test coverage
   :target: https://coveralls.io/github/kalekundert/autoprop?branch=master

.. image:: https://img.shields.io/github/last-commit/kalekundert/autoprop?logo=github
   :alt: GitHub last commit
   :target: https://github.com/kalekundert/autoprop

Properties are a feature in python that allow accessor functions (i.e. getters 
and setters) to masquerade as regular attributes.  This makes it possible to 
provide transparent APIs for classes that need to cache results, lazily load 
data, maintain invariants, or react in any other way to attribute access.

Unfortunately, making a property requires an annoying amount of boilerplate 
code.  There are a few ways to do it, but the most common and most succinct 
requires you to decorate two functions (with two different decorators) and to 
type the name of the attribute three times::

    >>> class RegularProperty:
    ...
    ...     @property
    ...     def attr(self):
    ...         print("getting attr")
    ...         return self._attr
    ...
    ...     @attr.setter
    ...     def attr(self, new_value):
    ...         print("setting attr")
    ...         self._attr = new_value
    ...
    >>> obj = RegularProperty()
    >>> obj.attr = 1
    setting attr
    >>> obj.attr
    getting attr
    1

The ``autoprop`` module simplifies this process by searching your class for 
accessor methods and adding properties corresponding to any such methods it 
finds.  For example, the code below defines the same property as the code 
above::

    >>> import autoprop
    >>> @autoprop
    ... class AutoProperty:
    ...
    ...     def get_attr(self):
    ...         print("getting attr")
    ...         return self._attr
    ...
    ...     def set_attr(self, new_value):
    ...         print("setting attr")
    ...         self._attr = new_value
    ...
    >>> obj = AutoProperty()
    >>> obj.attr = 1
    setting attr
    >>> obj.attr
    getting attr
    1

Installation
============
Install ``autoprop`` using ``pip``::

    $ pip install autoprop

Usage
=====
To use ``autoprop``, import the ``autoprop`` module and use it directly as a 
class decorator::

    >>> import autoprop
    >>>
    >>> @autoprop
    ... class Vector2D(object):
    ...    
    ...     def __init__(self, x, y):
    ...         self._x = x
    ...         self._y = y
    ...
    ...     def get_x(self):
    ...         return self._x
    ...
    ...     def set_x(self, x):
    ...         self._x = x
    ...
    ...     def get_y(self):
    ...         return self._y
    ...
    ...     def set_y(self, y):
    ...         self._y = y
    ...
    >>> v = Vector2D(1, 2)
    >>> v.x, v.y
    (1, 2)

The decorator searches your class for methods beginning with ``get_``, 
``set_``, or ``del_`` and uses them to create properties.  The names of the 
properties are taken from whatever comes after the underscore.  For example, 
the method ``get_x`` would be used to make a property called ``x``.  Any 
combination of getter, setter, and deleter methods is allowed for each 
property.

Caching
=======
If you have properties that are expensive to calculate, it's easy to cache 
them::

    >>> @autoprop.cache
    ... class Simulation(object):
    ...
    ...     def get_data(self):
    ...         print("some expensive calculation...")
    ...         return 42
    ...
    >>> s = Simulation()
    >>> s.data
    some expensive calculation...
    42
    >>> s.data
    42

It's also easy to cache some properties but not others::

    >>> @autoprop.dynamic
    ... class Simulation(object):
    ...
    ...     def get_cheap(self):
    ...         print("some cheap calculation...")
    ...         return 16
    ...
    ...     @autoprop.cache
    ...     def get_expensive(self):
    ...         print("some expensive calculation...")
    ...         return 42
    ...
    >>> s = Simulation()
    >>> s.cheap
    some cheap calculation...
    16
    >>> s.cheap
    some cheap calculation...
    16
    >>> s.expensive
    some expensive calculation...
    42
    >>> s.expensive
    42

In order to enable caching for a class, you must decorate it with 
``@autoprop.cache``.  This also sets the default caching behavior for any 
properties of that class.  You can then decorate the getter methods of that 
class in the same way, to override the default caching behavior for the 
corresponding property.  Note that it is an error to use the 
``@autoprop.cache`` decorator on non-getters, or in classes that have not 
enabled caching.

The ``@autoprop.cache()`` decorator accepts a ``policy`` keyword argument that 
determines when properties will need to be recalculated.  The following 
policies are understood:

- ``object``: This is the default policy.  Properties are recalculated when 
  first accessed after a change to the object is detected.  Changes are 
  detected in three ways:

  1. One of the setter or deleter methods identified by ``autoprop`` is called.  
     This includes if the method is indirectly called via a property.

  2. Any attribute of the object is set.  This is detected by applying a 
     decorator to the class's ``__setattr__()`` implementation, or providing an 
     implementation if one doesn't exist.  For classes that implement 
     ``__setattr__()`` and ``__getattr__()``, some care may be needed to avoid 
     infinite recursion (because ``autoprop`` may cause these methods to be 
     called earlier than you would normally expect).

  3. Any method decorated with ``@autoprop.refresh`` is called.

- ``class``: Similar to ``object``, but ``@autoprop.refresh`` will work even 
  when applied to class methods and static methods.  This is not the default 
  because it adds some overhead and is not often necessary.

- ``property``: Properties are recalculated when first accessed after their own 
  setter or deleter method has been called (whether directly or indirectly via 
  a parameter).  This is useful for properties that don't depend on any other 
  properties or object attributes.

- ``dynamic``: Properties are recalculated every time they are accessed.  Note 
  that ``@autoprop.dynamic`` is an alias for 
  ``@autoprop.cache(policy='dynamic')``.

- ``immutable``: Properties are never recalculated, and are furthermore not 
  allowed to have setter or deleter methods (an error will be raised if any 
  such methods are found).  As the name implies, this is for properties and 
  classes that are intended to be immutable.

Details
=======
Besides having the right prefix, there are two other criteria that methods must 
meet in order to be made into properties.  The first is that they must take the 
right number of required arguments.  Getters and deleters can't have any 
required arguments (other than self).  Setters must have exactly one required 
argument (other than self), which is the value to set.  Default, variable, and 
keyword arguments are all ignored; only the number of required arguments 
matters.

Any methods that have the right name but the wrong arguments are silently 
ignored.  This can be nice for getters that require, for example, an index.  
Even though such a getter can't be made into a property, ``autoprop`` allows it 
to follow the same naming conventions as any getters that can be::

    >>> @autoprop
    ... class Vector2D(Vector2D):
    ...     
    ...     def get_coord(self, i):
    ...         if i == 0: return self.x
    ...         if i == 1: return self.y
    ...
    ...     def set_coord(self, i, new_coord):
    ...         if i == 0: self.x = new_coord
    ...         if i == 1: self.y = new_coord
    ...
    >>> v = Vector2D(1, 2)
    >>> v.get_x()
    1
    >>> v.get_coord(0)
    1

In this way, users of your class can always expect to find accessors named 
``get_*`` and ``set_*``, and properties corresponding to those accessors for 
basic attributes that don't need any extra information.

The second criterion is that the property must have a name which is not already 
in use.  This guarantees that nothing you explicitly add to your class will be 
overwritten, and it gives you the ability to manually customize how certain 
properties are defined if you'd so like.  This criterion does not apply to 
superclasses, so it is possible for properties to shadow attributes defined in 
parent classes.


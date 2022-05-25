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

``autoprop`` is a library for automatically filling in classes with properties 
(e.g. ``obj.x``) corresponding to each accessor method (e.g. ``obj.get_x()``, 
``obj.set_x()``).  The biggest reasons to use ``autoprop`` are:

- Less boilerplate than defining properties manually.

- Sophisticated support for cached properties.

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
    ...         print("expensive calculation...")
    ...         return 42
    ...
    >>> s = Simulation()
    >>> s.data
    expensive calculation...
    42
    >>> s.data
    42

It's also easy to cache some properties but not others::

    >>> @autoprop
    ... class Simulation(object):
    ...
    ...     def get_cheap(self):
    ...         print("cheap calculation...")
    ...         return 16
    ...
    ...     @autoprop.cache
    ...     def get_expensive(self):
    ...         print("expensive calculation...")
    ...         return 42
    ...
    >>> s = Simulation()
    >>> s.cheap
    cheap calculation...
    16
    >>> s.cheap
    cheap calculation...
    16
    >>> s.expensive
    expensive calculation...
    42
    >>> s.expensive
    42

The ``@autoprop.cache()`` decorator accepts a ``policy`` keyword argument that 
determines how the cache will be managed.  The following policies are 
supported:

- ``overwrite``: This is the default policy.  Values are cached by overwriting 
  the property itself, such that future lookups will directly access the cached 
  value with no overhead.  This is exactly equivalent to using 
  `functools.cached_property`.  Unlike normal properties, there is no way to 
  customize what happens when setting or deleting these properties.  Setting 
  the property will update its value, and deleting it will cause its value to 
  be recalculated on the next access.

- ``manual``: Cached values are never recalculated automatically, but can be 
  recalculated and/or changed manually.  There are two ways to do this:
  
  1. Specify ``provide_mutators=True`` to ``@autoprop.cache()``.  This will 
     instruct autoprop to provide default setter and deleter implementations 
     for the property, which will allow the cached value to be changed or 
     dropped, respectively.  
    
  2. Call ``autoprop.set_cached_attr()`` and/or ``autoprop.del_cached_attr()``.  
     These functions allow you to implement your own setter and deleter 
     functions, which is often the entire purpose of using this policy.
  
  This policy has ≈10x more overhead than the ``overwrite`` policy, but allows 
  you to control what happens when the attribute is set or deleted (like a 
  regular property).  

- ``automatic``: Cached values are automatically recalculated if certain other 
  attributes of the object change.  In order to use this policy, you must 
  specify ``watch=<list of attributes>`` to ``@autoprop.cache()``.  The *watch* 
  argument must be iterable, and each item must either be the name of an 
  attribute (e.g. a string) or a callable that will accept the object in 
  question and return any value.  The cached value will be recalculated 
  whenever any of the "watched" values change.  The cache can also be 
  recalculated manually, in any of the ways described for the ``manual`` 
  policy.

  This policy has ≈25x more overhead than the ``overwrite`` policy, but allows 
  cached values to stay up to date when the attributes they depend on change.
  
- ``immutable``: Properties are never recalculated, and are furthermore not 
  allowed to have setter or deleter methods (an error will be raised if any 
  such methods are found).  As the name implies, this is for properties and 
  classes that are intended to be immutable.  
  
  Note that ``@autoprop.immutable`` is an alias for 
  ``@autoprop.cache(policy='immutable')``.

- ``dynamic``: Properties are recalculated every time they are accessed.  This 
  is exactly equivalent what ``autoprop`` does when caching is disabled, which 
  is exactly equivalent to using ``@property``.  Use this policy when you want 
  to specify ``@autoprop.cache`` at the class-level, but also need to prevent a 
  few properties from being cached.
  
  Note that ``@autoprop.dynamic`` is an alias for 
  ``@autoprop.cache(policy='dynamic')``.

Details
=======
Besides having the right prefix, there are two other criteria that methods must 
meet in order to be made into properties.  The first is that they must take the 
right number of arguments.  Getters and deleters must not require any arguments 
(other than self).  Setters must accept exactly one argument (other than self), 
which is the value to set.  Default, variable, and keyword arguments are all 
ignored; all that matters is that the function can be called with the expected 
number of arguments.

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

If you want to explicitly ignore a method which would otherwise be discovered 
by ``autoprop``, use the ``@autoprop.ignore`` decorator.

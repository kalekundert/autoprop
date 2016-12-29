``autoprop`` --- Infer properties from accessor methods
=======================================================
.. image:: https://img.shields.io/pypi/v/autoprop.svg
   :target: https://pypi.python.org/pypi/autoprop

.. image:: https://img.shields.io/pypi/pyversions/autoprop.svg
   :target: https://pypi.python.org/pypi/autoprop

.. image:: https://img.shields.io/travis/kalekundert/autoprop.svg
   :target: https://travis-ci.org/kalekundert/autoprop

.. image:: https://img.shields.io/coveralls/kalekundert/autoprop.svg
   :target: https://coveralls.io/github/kalekundert/autoprop?branch=master

Properties are a feature in python that allow accessor functions (i.e. getters 
and setters) to masquerade as regular attributes.  This makes it possible to 
provide transparent APIs for classes that need to cache results, lazily load 
data, maintain invariants, or react in any other way to attribute access.

Unfortunately, making a property requires a fair amount of boilerplate code.  
There are a few ways to do it, but the most common and most succinct requires 
you to decorate two functions (with two different decorators) and to type the 
name of the attribute three times::

    class RegularProperty:
        
        @property
        def attr(self):
            return self._attr

        @attr.setter
        def attr(self, new_value):
            self._attr = new_value

The ``autoprop`` module simplifies this process by searching your class for 
accessor methods and adding properties corresponding to any such methods it 
finds.  For example, the code below defines the same property as the code 
above::

    @autoprop
    class AutoProperty:
        
        def get_attr(self):
            return self._attr

        def set_attr(self, new_value):
            self._attr = new_value

Installation
------------
``autoprop`` is available on PyPI, so you can install it using ``pip``::

    pip install autoprop

Usage
-----
To use ``autoprop``, import the ``autoprop`` module and use it directly as a 
class decorator::

    import autoprop

    @autoprop
    class Vector2D:
       
        def __init__(self, x, y):
            self._x = x
            self._y = y

        def get_x(self):
            return self._x

        def set_x(self, x):
            self._x = x

        def get_y(self):
            return self._y

        def set_y(self, y):
            self._y = y

The decorator searches your class for methods beginning with ``get_``, 
``set_``, or ``del_`` and uses them to create properties.  The names of the 
properties are taken from whatever comes after the underscore.  For example, 
the method ``get_x`` would be used to make a property called ``x``.  Any 
combination of getter, setter, and deleter methods is allowed.

Besides having the right prefix, there are two other criteria methods must meet 
in order to be made into properties.  The first is that they must take the 
right number of required arguments.  Getters and deleters can't have any 
required arguments (other than self).  Setters must have exactly one required 
argument (other than self), which is the value to set.  Default, variable, and 
keyword arguments are all ok; only the number of required arguments matters.

Any methods that have the right name but the wrong arguments are silently 
ignored.  This can be nice for getters that require, for example, an index.  
Even though such a getter can't be made into a property, ``autoprop`` allows it 
to follow the same naming conventions as any getters that can be::

    @autoprop
    class Vector2D:
        
        ...

        def get_coord(self, i):
            if i == 0: return self._x
            if i == 1: return self._y

        def set_coord(self, i, new_coord):
            if i == 0: self.x = new_coord
            if i == 1: self.y = new_coord

In this way, users of your class can always expect to find accessors named 
``get_*`` and ``set_*``, and can always expect to find properties for basic 
attributes that don't need any extra information.

The second criterion is that the property must have a name which is not already 
in use.  This guarantees that nothing you explicitly add to your class will be 
overwritten, and it gives you the ability to customize how certain properties 
are defined if you'd so like.  Note that this criterion does not apply to names 
defined in any superclasses, so if you overwrite some accessors defined in a 
superclass, you'll get new properties that refer to the overridden accessors 
and not be left with stale references to the superclass accessors.


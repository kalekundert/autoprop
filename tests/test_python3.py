#!/usr/bin/env python3

import pytest
import autoprop

def test_keyword_only_arguments():
    # inspect.getargspec() chokes methods with keyword-only arguments.

    @autoprop   # (no fold)
    class Example(object):
        def get_attr(self, *, pos=None):
            return 'attr'
        def set_attr(self, *, new_value):
            pass

    ex = Example()
    assert ex.attr == 'attr'

    # Even though the setter has one required argument, it's a named argument, 
    # so it shouldn't count and 'attr' should be defined without a setter.
    with pytest.raises(AttributeError):
        ex.attr = 'setter'



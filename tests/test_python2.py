#!/usr/bin/env python2

import pytest
import autoprop

def test_complain_about_old_style_classes():
    with pytest.raises(TypeError) as err:
        @autoprop
        class Example:
            pass

    assert '@autoprop can only be used with new-style classes' in str(err)


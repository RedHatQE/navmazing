import pytest

import navmazing


@pytest.mark.parametrize('attribute', [
    x for x in dir(navmazing.Navigate()) if not x.startswith('__')])
def test_navmazing_navigate_deprecated(attribute):
    with pytest.warns(DeprecationWarning):
        res = getattr(navmazing.navigate, attribute)
        assert res == getattr(navmazing._navigate, attribute)


@pytest.mark.filterwarnings('error::DeprecationWarning')
def test_navmazing_navigate_attributeerror_nowarn():
    with pytest.raises(AttributeError):
        navmazing.navigate.this_is_not_here

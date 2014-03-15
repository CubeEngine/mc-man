""" Tests for mcman.py. """
from mcman import mcman


def test_negative():
    """ Test mcman.negative. """
    assert mcman.negative(42) == -42
    assert mcman.negative(-42) == -42
    assert mcman.negative('42') == -42
    assert mcman.negative('-42') == -42

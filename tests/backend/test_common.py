""" Tests for backend.common.py. """
from mcman.backend import common
from nose import with_setup
from unittest.mock import MagicMock


def test_levenshtein():
    """ Test common.levenshtein. """
    assert common.levenshtein('herp', 'herpderp') == 4
    assert common.levenshtein('herpderp', 'herp') == 4
    assert common.levenshtein('hederprp', 'herp') == 4
    assert common.levenshtein('herp', 'hederprp') == 4
    assert common.levenshtein('preherppost', 'preprehpost') == 4
    assert common.levenshtein('abcdef', 'abdce') == 3


def test_list_names():
    """ Test common.list_names. """
    assert common.list_names(['one']) == 'one'
    assert common.list_names(['one', 'two']) == 'one and two'
    assert common.list_names(['one', 'two'],
                             last_separator=' + ') == 'one + two'
    assert common.list_names(['one', 'two', 'three']) == 'one, two and three'
    assert common.list_names(['one', 'two', 'three'],
                             last_separator=' + ') == 'one, two + three'
    assert common.list_names(['one', 'two', 'three'],
                             separator='; ') == 'one; two and three'
    assert common.list_names(['one', 'two', 'three'],
                             separator='; ',
                             last_separator=' + ') == 'one; two + three'


def setup_test_checksum_file():
    """ Setup for test_checksum_file. """
    with open('/tmp/mcman-test-file.checksum', 'w') as file:
        file.write('Hello')
        file.flush()


def teardown_test_checksum_file():
    """ Teardown for test_checksum_file. """
    import os
    os.remove('/tmp/mcman-test-file.checksum')


@with_setup(setup_test_checksum_file, teardown_test_checksum_file)
def test_checksum_file():
    """ Test common.checksum_file. """
    fasit = '8b1a9953c4611296a827abf8c47804d7'
    with open('/tmp/mcman-test-file.checksum', 'rb') as file:
        checksum = common.checksum_file(file)

    assert checksum == fasit
    assert checksum == common.checksum_file('/tmp/mcman-test-file.checksum')


def test_replace_last():
    """ Test common.replace_last. """
    assert common.replace_last('aaa', 'a', 'b') == 'aab'


def test_ask():
    """ Test common.ask with yes or no as input. """
    common.print = MagicMock()

    common.input = MagicMock(return_value='Yes')
    assert common.ask('') is True

    common.input = MagicMock(return_value='No')
    assert common.ask('') is False

    common.input = MagicMock(return_value='')
    assert common.ask('') is True

    common.input = MagicMock(return_value='')
    assert common.ask('', default=False) is False

    assert common.ask('', skip=True) is True
    assert common.ask('', default=False, skip=True) is False

    common.input = input

# TODO - Unit tests for extract_file, download and create_progressbar

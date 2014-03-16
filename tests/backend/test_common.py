""" Tests for backend.common.py. """
from mcman.backend import common
from nose import with_setup
from unittest.mock import MagicMock, patch
from unittest import TestCase
from zipfile import ZipFile
import os
import shutil


class TestChecksumFile(TestCase):

    """ Test common.checksum_file. """

    def setUp(self):
        """ Setup. """
        self.path = 'test_data/random.txt'
        with open('test_data/random.md5', 'r') as file:
            md5 = file.readline()
            self.md5 = md5.strip()

    def test_file(self):
        """ Test with file object. """
        with open(self.path, 'rb') as file:
            md5 = common.checksum_file(file)
            assert md5 == self.md5

    def test_path(self):
        """ Test with file path. """
        md5 = common.checksum_file(self.path)
        assert md5 == self.md5


class TestExctractFile(TestCase):

    """ Test common.extract_file. """

    def setUp(self):
        """ Set up. """
        self.path = 'test_data/zipped.zip'
        self.test_folder = '/tmp/test_extract_file/'
        self.zipfile = ZipFile(self.path, 'r')
        os.makedirs(self.test_folder)

    def tearDown(self):
        """ Tear down. """
        self.zipfile.close()
        shutil.rmtree(self.test_folder)

    def test_extract_base_file(self):
        """ Test common.extract_file with file in base of zip. """
        common.extract_file(self.zipfile, 'foo.txt',
                            self.test_folder + 'foo.txt')
        with open(self.test_folder + 'foo.txt', 'r') as file:
            assert file.readline() == 'foo\n'

    def test_extract_base_folder(self):
        """ Test common.extract_file with folder in base of zip. """
        common.extract_file(self.zipfile, 'herp/', self.test_folder + 'herp/')
        assert os.path.isdir(self.test_folder + 'herp')

    def test_extract_sub_file(self):
        """ Test common.extract_file with file in subfolder. """
        common.extract_file(self.zipfile, 'herp/bar/baz.txt',
                            self.test_folder + 'herp/bar/baz.txt')
        assert os.path.isdir(self.test_folder + 'herp')
        assert os.path.isdir(self.test_folder + 'herp/bar')
        with open(self.test_folder + 'herp/bar/baz.txt', 'r') as file:
            assert file.readline() == 'baz\n'

    def test_extract_sub_folder(self):
        """ Test common.extract_file with folder in subfolder. """
        common.extract_file(self.zipfile, 'herp/bar/',
                            self.test_folder + 'herp/bar/')
        assert os.path.isdir(self.test_folder + 'herp')
        assert os.path.isdir(self.test_folder + 'herp/bar')


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


def test_replace_last():
    """ Test common.replace_last. """
    assert common.replace_last('aaa', 'a', 'b') == 'aab'
    assert common.replace_last('a', 'a', 'b') == 'b'


@patch('builtins.print', MagicMock())
@patch('builtins.input', MagicMock(return_value='Yes'))
def test_ask_yes():
    """ Test common.ask when user answers 'Yes'. """
    assert common.ask('') is True
    assert common.ask('', default=False) is True


@patch('builtins.print', MagicMock())
@patch('builtins.input', MagicMock(return_value='No'))
def test_ask_no():
    """ Test common.ask when user answers 'No'. """
    assert common.ask('') is False
    assert common.ask('', default=False) is False


@patch('builtins.print', MagicMock())
@patch('builtins.input', MagicMock(return_value=''))
def test_ask_empty():
    """ Test common.ask when user answers nothing. """
    assert common.ask('') is True
    assert common.ask('', default=False) is False
    assert common.ask('', skip=True) is True
    assert common.ask('', default=False, skip=True) is False

# TODO - Unit tests for download and create_progressbar

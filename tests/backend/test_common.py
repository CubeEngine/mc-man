""" Tests for mcman.backend.common. """
from mcman.backend import common
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


class TestDownload(TestCase):

    """ Test common.download. """

    def setUp(self):
        self.url = 'http://herp.derp.foo/bar.baz'
        self.filename = 'bar.baz'
        self.reporthook = 42
        self.prefix = 'Prefix'
        self.removed = False
        self.checksum = 'HerpDerpFooBarBaz'
        self.display_name = 'Displayed'

        @patch('mcman.backend.common.checksum_file', self.fake_checksum_file)
        @patch('mcman.backend.common.create_progress_bar',
               self.fake_create_progressbar)
        @patch('mcman.backend.common.get_term_width',
               MagicMock(return_value=80))
        @patch('builtins.print', self.fake_print)
        @patch('mcman.backend.common.urlretrieve', self.fake_urlretrieve)
        @patch('os.remove', self.fake_remove)
        def test(checksum, destination=self.filename, prefix=self.prefix,
                 display_name=self.display_name):
            common.download(self.url, destination=destination,
                            checksum=checksum, prefix=prefix,
                            display_name=display_name)

        self.test = test

    def fake_urlretrieve(self, url, filename=None, reporthook=None):
        assert url == self.url
        assert filename == self.filename
        assert reporthook == self.reporthook

    def fake_checksum_file(self, file):
        return self.checksum

    def fake_create_progressbar(self, prefix=None, width=80):
        assert self.prefix + self.display_name == prefix
        return self.reporthook

    def fake_print(self, *value, sep=' ', end='\n'):
        value = [str(v) for v in value]
        sep = str(sep)
        end = str(end)
        if hasattr(self, 'line'):
            if not self.line.endswith('\n'):
                self.line += sep.join(value) + end
                return
        self.line = sep.join(value) + end

    def fake_remove(self, file):
        self.removed = True

    def test_download_success(self):
        """ Test common.download with successful checksum. """
        self.test(self.checksum)
        assert self.line.endswith('Success\n')

    def test_download_fail(self):
        """ Test common.download with unsuccessful checksum. """
        self.test('SomethingFalse')
        assert self.removed

    def test_download_no_displayname(self):
        """ Test common.download without a display_name. """
        self.display_name = 'bar.baz'
        self.test(self.checksum, display_name=None)

    def test_download_no_destination(self):
        """ Test common.download without a destination. """
        self.display_name = 'bar.baz'
        self.destination = 'bar.baz'
        self.test(self.checksum, destination=None, display_name=None)


def test_levenshtein():
    """ Test common.levenshtein. """
    assert common.levenshtein('herp', 'herpderp') == 4
    assert common.levenshtein('herpderp', 'herp') == 4
    assert common.levenshtein('hederprp', 'herp') == 4
    assert common.levenshtein('herp', 'hederprp') == 4
    assert common.levenshtein('preherppost', 'preprehpost') == 4
    assert common.levenshtein('abcdef', 'abdce') == 3
    assert common.levenshtein('1234', '') == 4


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


@patch('struct.unpack', MagicMock(return_value=[127, 127]))
def test_get_term_width_success():
    """ Test common.get_term_width with (emulated) success. """
    returned = common.get_term_width()
    assert returned == 127 or returned == 80

@patch('struct.unpack', MagicMock(side_effect=OSError()))
def test_get_term_width_exception():
    """ Test common.get_term_width with (emulated) failure. """
    assert common.get_term_width() == 80

# TODO - Unit tests for create_progressbar

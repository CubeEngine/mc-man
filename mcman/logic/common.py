# "mcman" - An utility for managing Minecraft server jars and plugins.
# Copyright (C) 2014  Tobias Laundal <totokaka>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Common utilities for the plugin and server backends. """
import sys
import hashlib
import os
import os.path
import struct
import termios
import fcntl
from urllib.request import urlretrieve
from math import ceil


def levenshtein(first, second):
    """ Get the levenshtein edit distance between the strings.

    The Levenshtein distance is how many characters that need to be changed,
    deleted or inserted in the first string to form the second string. It is
    used to determine the equality of two strings.

    This function accepts to parameters:
        first     The first string.
        second    The second string.

    """
    if len(first) < len(second):
        return levenshtein(second, first)

    if len(second) == 0:
        return len(first)

    previous_row = range(len(second) + 1)

    for i, k in enumerate(first):
        current_row = [i + 1]

        for index, value in enumerate(second):
            insertions = previous_row[index + 1] + 1
            deletions = current_row[index] + 1
            substitutions = previous_row[index] + (k != value)

            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


def list_names(array, separator=', ', last_separator=' and '):
    """ Return a string with a listing of the elements.

    This function will basically first join the elements in the list by the
    parameter 'separator'(defaults to ', '), but the last field will be
    appended with the parameter 'last_separator'(defaults to ' and ') before
    it. This leads to a nice human readable representation of the list.

    Examples:
    >>> list_names(['Jane', 'Joe', 'Peter'])
    "Jane, Joe and Peter"
    >>> list_names(['Joe', 'Jane'])
    "Joe and Jane"
    >>> list_names(['Jane'])
    "Jane"

    The function accepts up to three parameters:
        array                    The list to represent.
        separator=', '           The separator between the first elements in
                                 the list.
        last_separator=' and '   The separator for the last element.

    """
    if len(array) > 1:
        return ''.join([separator.join([str(i) for i in array[:-1]]),
                        last_separator,
                        str(array[-1])])
    elif len(array) == 1:
        return array[0]


def download(url, destination=None, checksum=None, prefix='',
             display_name=None):
    """ Download with progressbar.

    Arguments:
        url             URL to download from.
        destination     Path to download the file to. Defaults to None. When it
                        is none the destination is based on the url, and the
                        folder is the CWD.
        checksum        MD5 checksum to check the file against. Defaults to
                        None. When it is none, no checksum validation is done.
        prefix          What to put before the file_name on the left side.
                        Defaults to an empty string.
        display_name    The name to display on the left side instead of the
                        destination. Defaults to None.

    True is returned if the checksum succeeds or is not done, False only if it
    fails.

    """
    if destination is None:
        destination = url.split('/')[-1]
    if display_name is None:
        display_name = destination

    # Create the folders if they don't exist
    if '/' in destination:
        makedirs(destination)

    term_width = get_term_width()
    pprefix = prefix + display_name
    progress = create_progress_bar(prefix=pprefix, width=term_width)
    urlretrieve(url, filename=destination, reporthook=progress)

    if checksum is not None and len(checksum) > 0:
        print('\n' + ' ' * len(prefix) + 'Checking checksum...', end=' ')
        actual_checksum = checksum_file(destination)
        if actual_checksum == checksum:
            print('Success')
        else:
            os.remove(destination)
            print('The checksums did not match! The file was deleted.')
            return False
    return True


def makedirs(file):
    """ Make the parent directories to a file. """
    folder = '/'.join(file.split('/')[:-1]) + '/'
    if not os.path.isdir(folder):
        os.makedirs(folder)


def create_progress_bar(width, prefix=None):
    """ Create a progress bar.

    This returns a function which can be used as the progress hook for
    urlretrieve. If you don't want to use the function of urlretrieve, the
    signature for the function is int, int, int: Count, count_size, max.

    Intended for the download function.

    """
    left = ceil(width/2)
    right = width-left
    net_bar_size = right-8
    char_size = net_bar_size/100
    frmt = '{{prefix:<{}}}[{{bar_left}}{{bar_right}}] {{prc}}%\r'.format(left)
    last_percent = -1

    def progress_hook(count, blocksize, totalsize):
        """ Progress hook. """
        percent = min(ceil(count*blocksize*100/totalsize), 100)
        nonlocal last_percent
        if percent == last_percent:
            return
        else:
            last_percent = percent
        fill_size = int(char_size*percent)
        empty_size = net_bar_size-fill_size
        text = frmt.format(prefix=prefix,
                           bar_left=('='*(fill_size-1)+'>' if percent < 100
                                     else '='*fill_size),
                           bar_right=' '*empty_size,
                           prc=percent)

        sys.stdout.write(text)
        sys.stdout.flush()

    progress_hook(0, 1, 100)
    return progress_hook


def checksum_file(file):
    """ MD5 Checksum of file.

    This function will return the MD5 checksum of the file.

    One parameter is accepted:
        file    The name of the file to checksum, or the (relative) path to it.

    """
    if type(file) is str:
        with open(file, 'rb') as file:
            return checksum_file(file)
    else:
        return hashlib.md5(file.read()).hexdigest()


def replace_last(string, old, new):
    """ Replace the last occurance of `old` in `string` with `new`. """
    return new.join(string.rsplit(old, 1))


def get_term_width(term=1):
    """ Get the width of the terminal.

    This tries to exctract the width with fcntl.ioctl. If that failes the
    standard width 80 is returned.

    This function is using the fcntl and ioctl system calls which are only
    available on Unix.

    """
    try:
        return struct.unpack('hh',
                             fcntl.ioctl(term, termios.TIOCGWINSZ, '1234')
                             )[1]
    except OSError:
        return 80


def extract_file(zipped, file, dest):
    """ Extract file from ZipFile archive to dest.

    This function will extract the file in `file` in the zip archive to the
    file in `dest` in the filesystem. Folders are handled correctly, too.

    This function takes three arguments:
        zipped    The ZipFile to extract the file from.
        file      The path in the ZipFile to the file to extract.
        dest      The path in the filesystem to the destination.

    """
    if '/' in dest:
        os.makedirs('/'.join(dest.split('/')[:-1]), exist_ok=True)
    if not file.endswith('/'):
        content = zipped.read(file)
        with open(dest, 'wb') as dest:
            dest.write(content)


def ask(question, default=True, skip=False):
    """ Ask user for confirmation.

    This function accepts up to three parameters:
        question    The question to ask the user.
        default    If Yes is the default alternative. Defaults to True.
        skip        If the confirmation should be skipped, and the question
                    printed just for illustration. Defaults to False.

    """
    print(question, end=' [Y/n]: ' if default else ' [y/N]: ')
    if skip:
        print('y')
        return default
    else:
        answer = input()
        if len(answer) == 0:
            return default
        else:
            return 'y' in answer.lower()


def type_fits(has, requires):
    """ Return whether the `has` version is compatible with the `requires`. """
    has = has.lower()
    requires = requires.lower()
    if requires == 'latest' or has == 'release':
        return True
    elif has == requires:
        return True
    elif requires == 'release':
        return False
    elif requires == 'alpha' and has == 'beta':
        return True
    return False


def format_name(name):
    """ Format the name.

    If the name consists of multiple words they will be capitalized and put
    together without spaces.

    """
    if ' ' in name:
        words = name.split(' ')
        name = ''.join([w.capitalize() for w in words])
    return name


def find_plugins_folder():
    """ Find the plugins folder.

    This will return the relative path to the plugins folder.
    Currently either '.' or 'plugins' is returend.

    """
    if 'plugins' in os.listdir('.'):
        return 'plugins'
    return '.'

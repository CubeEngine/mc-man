""" Utilities. """
import sys
import hashlib
import os
from urllib.request import urlretrieve


def levenshtein(x, y):
    """ Get the levenshtein edit distance between y strings. """
    if len(x) < len(y):
        return levenshtein(y, x)
    if len(y) == 0:
        return len(x)
    previous_row = range(len(y) + 1)
    for i, k in enumerate(x):
        current_row = [i + 1]
        for j, l in enumerate(y):
            insertions = previous_row[
                j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (k != l)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def remove_duplicates(plugins):
    """ Remove duplicate plugins from a list.

    This a list of Plugin objects as the argument.
    The Plugin objects only need to contain the slug.

    """
    new = list()
    for plugin in plugins:
        for qlugin in new:
            if plugin.slug == qlugin.slug:
                break
        else:
            new.append(plugin)
    return new


def list_names(array, word=', ', last_word=' and '):
    """ Human readable list of the names.

    This function displays the array in a human readable form. It will separate
    the first elements by the `word`, and the last element will have the
    `last_word` before it.

    Example returned string:
        one, two and three

    """
    if len(array) > 1:
        return (word.join([str(i) for i in array[:-1]]) + last_word +
                str(array[-1]))
    elif len(array) == 1:
        return array[0]


def download(url, file_name=None, checksum=None):
    """ Download with progressbar. """
    def progress(count, blocksize, totalsize):
        percent = int(count*blocksize*100/totalsize)
        sys.stdout.write('\r[{}{}] {:>3}%'.format(
            replace_last('=' * percent, '=', '>'),
            ' ' * (100-percent), percent))
        sys.stdout.flush()

    if file_name is None:
        file_name = url.split('/')[-1]
    print('Downloading to {}...'.format(file_name))
    urlretrieve(url, filename=file_name, reporthook=progress)
    print()

    if checksum is not None and len(checksum) > 0:
        print('Checking checksum...')
        actual_checksum = checksum_file(file_name)
        if actual_checksum == checksum:
            print('Sucess')
        else:
            os.remove(file_name)
            print('The checksums did not match! The file was deleted.')


def checksum_file(file_name):
    """ MD5 Checksum of file with name `file_name`. """
    return hashlib.md5(open(file_name, 'rb').read()).hexdigest()


def replace_last(string, old, new):
    """ Replace the last occurance of `old` in `string` with `new`. """
    string = string.rsplit(old, 1)
    return new.join(string)

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

""" Setup file for PlugMan. """
from setuptools import setup
import os
import mcman


def read(fname):
    """ Read a file. """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='mc-man',
    version=mcman.__version__,
    author=mcman.__author__,
    author_email='mail@totokaka.io',
    description=('The Minecraft server jar and plugin manager, downloader '
                 'and updater'),
    license='GPLv3+',
    long_description=read('README.rst'),
    url='https://github.com/CubeEngineDev/mc-man',
    packages=['mcman', 'mcman.commands', 'mcman.logic',
              'mcman.logic.plugins'],
    scripts=["bin/mcman"],
    install_requires=['PyYAML>=3.10',
                      'pyBukGet>=2.3',
                      'pySpaceGDN>=0.2'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        ('License :: OSI Approved :: GNU General Public License v3 or later '
         '(GPLv3+)'),
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
)

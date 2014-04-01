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

""" Backend utils for the mcman plugins command. """

from mcman.logic import common as utils


def select_newest_version(plugin, v_type="Release"):
    """ Return the newest version in plugin which is compatible `v_type`. """
    for version in plugin['versions']:
        if utils.type_fits(version['type'], v_type):
            return version


def select_installed_version(plugin):
    """ Return the installed version of the `plugin`.

    This function raises an AssertionError if the plugin is not installed.
    Eg. 'installed_version' is not in `plugin`.

    """
    assert 'installed_version' in plugin
    installed = plugin['installed_version']
    for version in plugin['versions']:
        if version['version'] == installed:
            return version


def remove_duplicate_plugins(plugins, field='slug'):
    """ Return a new list without duplicates.

    The `field` argument specifies what field to use as the unique.

    """
    result = list()
    for plugin in plugins:
        for in_result in result:
            if plugin[field] == in_result[field]:
                break
        else:
            result.append(plugin)
    return result


def extract_name_version(names):
    """ Extract names and versions for a list of names.

    A tuple of a list with the names and a dict which maps from name in lower
    to version.

    """
    versions = dict()
    results = list()

    for name in names:
        if '#' in name:
            name, version = name.split('#')
            versions[name.lower()] = version
        results.append(name)

    return results, versions


def extract_dependencies(plugins, v_type='Release'):
    """ Extract dependencies from the plugin.

    The `v_type` says what kind of version we want.

    """
    if not type(plugins) is list:
        plugins = [plugins]

    deps = list()

    for plugin in plugins:
        for version in plugin['versions']:
            if utils.type_fits(version['type'], v_type):
                deps.extend(version['hard_dependencies'])
                break

    return deps

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

""" The backend for the mcman command. """

import os
import threading
import bukget
import yaml
from queue import Queue
from zipfile import ZipFile
from mcman.backend.common import type_fits, format_name, find_plugins_folder
from mcman.backend import common as utils


def init(base, user_agent):
    """ Initialize the module.

    This function just sets the base url and user agent for BukGet.

    """
    bukget.BASE = base
    bukget.USER_AGENT = user_agent


def search(query, size):
    """ Search for plugins.

    This function will search for plugins on bukget by their slug and name.
    The results are ordered by a score calculated with their levenshtein edit
    distance from the search query and their popularity.

    Two parameters are required:
        query    The query to search for.
        size     The size of the returned results. It can be negative, and in
                 that case the bottom of the results are returned.

    A list with the plugin dicts from BukGet is returned. It is sorted by the
    score system mentioned earlier.

    """
    sorting = ('-' if size >= 0 else '')+'popularity.monthly'
    search_results = bukget.search(
        {
            'field': 'plugin_name',
            'action': 'like',
            'value': query
        },
        sort=sorting,
        fields='slug,plugin_name,description,popularity.monthly',
        size=abs(size))
    search_results += bukget.search(
        {
            'field': 'slug',
            'action': 'like',
            'value': query
        },
        sort=sorting,
        fields='slug,plugin_name,description,popularity.monthly',
        size=abs(size))

    search_results = remove_duplicate_plugins(search_results)

    # Calculate scores
    results = list()
    for plugin in search_results:
        score = plugin['popularity']['monthly']
        distance = utils.levenshtein(
            query, plugin['plugin_name'])
        score -= distance

        results.append((score, plugin))

    results.sort(key=lambda x: x[0], reverse=True)

    return [result[1] for result in results]


def info(server, name):
    """ Find the plugin by name, and return certain information.

    The returned information is the information that is needed for the info
    command.

    The plugin dictionary as returned by pyBukGet is returned, or None if the
    plugin was not found.

    """
    slug = bukget.find_by_name(server, name)
    if slug is None:
        return None

    plugin = bukget.plugin_details(server, slug,
                                   fields='website,dbo_page,'
                                          + 'description,'
                                          + 'versions.type,'
                                          + 'versions.game_versions,'
                                          + 'versions.version,'
                                          + 'plugin_name,server,'
                                          + 'authors,categories,'
                                          + 'stage,slug')

    return plugin


def dependencies(server, plugins, v_type='Latest', deps=True):
    """ Resolve dependencies.

    This function will return a list of plugin dictionaries of all plugins
    depending directly, or indirectly on the plugins in `plugins`. `plugins`
    may be a list of plugin slugs, or a single plugin slug.

    """
    fields = ('slug,plugin_name,versions.hard_dependencies,versions.type,'
              'versions.version,versions.download,versions.filename,'
              'versions.md5')
    if type(plugins) is not list:
        plugins = [plugins]

    plugins, versions = extract_name_version(plugins)

    plugins = bukget.search(
        {
            'field': 'plugin_name',
            'action': 'in',
            'value': plugins
        },
        fields=fields)

    for plugin in plugins:
        if not plugin['plugin_name'].lower() in versions:
            continue

        version = versions[plugin['plugin_name'].lower()]

        for ver in plugin['versions']:
            if ver['version'] == version:
                plugin['versions'] = [ver]
                break
        else:
            plugin['versions'] = None

    if deps:
        return _dependencies(server, plugins, v_type=v_type)
    else:
        return plugins


def _dependencies(server, plugins, stack=None, v_type='Latest'):
    """ Undocumented recursive, internal function. """
    fields = ('slug,plugin_name,versions.hard_dependencies,versions.type,'
              'versions.version,versions.download,versions.filename,'
              'versions.md5')

    # Sanitizing of parameters
    if stack is None:
        stack = plugins[:]
    v_type = v_type.capitalize()

    # Resolve all the dependencies of the plugins
    deps = extract_dependencies(plugins, v_type)

    # Filter out dependencies allready in the stack and
    # add all dependencies to the stack
    # From this point on the stack contains all dependencies resolved so far,
    # and dependencies contains all dependencies that are new of this level.
    for dependency in deps:
        for installed in stack:
            if installed['plugin_name'] == dependency:
                deps.remove(dependency)
                break

    # If there are any plugins whose dependencies are not in the stack
    if len(deps) > 0:
        search_results = bukget.search(
            {
                'field': 'plugin_name',
                'action': 'in',
                'value': deps
            },
            fields=fields)

        for plugin in search_results:
            for in_stack in stack:
                if in_stack['slug'] == plugin['slug']:
                    break
            else:
                stack.append(plugin)

        _dependencies(server, search_results, stack, v_type)

    return stack


def download(question, frmt, plugins, skip=False):
    """ Download plugins.

    This function does the questioning, and installing of each plugin.

    Parameters:
        question    The question to ask the user.
        frmt        The format to format the prefix with. Must support two
                    parameters: total and part.
        plugins     A list of the plugins to install.
        skip        Whether to skip the confirmation.

    """
    if utils.ask(question, skip=skip):
        for i in range(len(plugins)):
            plugin = plugins[i]
            prefix = frmt.format(total=len(plugins), part=i+1)
            download_plugin(plugin, prefix)


def download_plugin(plugin, prefix=''):
    """ Download plugin.

    This function takes two parameters. The first is the plugin. The plugin
    must be a dictionary returned by bukget with at least the following fields:
        versions.download, plugin_name, versions.md5, versions.filename
    The second parameter is a prefix to print before each output line,
    typically a counter on which download this it. Example:
        ( 5/20)

    """
    target_folder = find_plugins_folder() + '/'

    url = plugin['versions'][0]['download']
    filename = format_name(plugin['plugin_name'])
    md5 = plugin['versions'][0]['md5']
    suffix = plugin['versions'][0]['filename'].split('.')[-1]

    full_name = target_folder + filename + '.' + suffix

    utils.download(url, destination=full_name,
                   checksum=md5, prefix=prefix, display_name=filename)

    if suffix == 'zip':
        print(' '*len(prefix) + 'Unzipping...', end=' ')
        unzip_plugin(full_name, target_folder)
        os.remove(full_name)
        print('Success')


def unzip_plugin(target_file, target_folder):
    """ Unzip a plugin that is packaged in a zip. """
    with ZipFile(target_file, 'r') as zipped:
        folders = [x for x in zipped.namelist()
                   if x.endswith('/')]
        jars = [x for x in zipped.namelist()
                if x.endswith('.jar')]

        strip_folder = False
        if len(jars) == 0 and len(folders) > 0:
            folder = folders[0]
            # All jars in folder
            jars = [x for x in zipped.namelist()
                    if x.endswith('.jar')
                    and x.startswith(folder)]
            strip_folder = folder

        for jar in jars:
            destination = target_folder
            if strip_folder:
                destination += jar.split(strip_folder, 1)[1]
            else:
                destination += jar

            utils.extract_file(zipped, jar, destination)


def parse_installed_plugins_worker(jar_queue, result_queue):
    """ Worker function of list_plugins.

    This function takes jars in the `jar_queue`, calculates the checksum,
    and extracts the main class, name and version and push this data to the
    `result_queue`.

    """
    while not jar_queue.empty():
        jar = jar_queue.get()

        checksum = utils.checksum_file(jar)

        with ZipFile(jar, 'r') as zipped:
            if not 'plugin.yml' in zipped.namelist():
                continue

            yml = yaml.load(zipped.read('plugin.yml').decode())
            plugin_name = yml['name']
            main = yml['main']
            version = str(yml['version'])

            result_queue.put((checksum, main, plugin_name, version, jar))

        jar_queue.task_done()


def parse_installed_plugins(workers=4):
    """ Parse installed plugins for some information.

    The information is returned in a tuple like this:
        (jar checksum, main class, plugin name, plugin version, jar path)

    These tuples are put in a set.

    """
    folder = find_plugins_folder() + '/'
    jars = [folder + f for f in os.listdir(folder)
            if os.path.isfile(folder + f) and f.endswith('.jar')]

    jar_queue = Queue()
    for jar in jars:
        jar_queue.put(jar)

    result_queue = Queue(len(jars))

    threads = list()
    for _ in range(workers):
        thread = threading.Thread(target=parse_installed_plugins_worker,
                                  args=(jar_queue, result_queue))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Wait for all jars to be claimed
    jar_queue.join()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    plugins = set()
    while not result_queue.empty():
        plugins.add(result_queue.get())

    return plugins


def list_plugins(workers=4):
    """ List installed plugins.

    Returns a list of plugin dicts with basic information about the plugin and
    it's versions. Two additional fields exists in these dicts;
    installed_version and installed_file.

    """
    fields = ('slug,plugin_name,versions.hard_dependencies,versions.type,'
              'versions.version,versions.download,versions.filename,'
              'versions.md5')

    plugins = parse_installed_plugins(workers)

    results = bukget.search(
        {
            'field': 'versions.checksum',
            'action': 'in',
            'value': [plugin[0] for plugin in plugins]
        },
        fields=fields)

    results += bukget.search(
        {
            'field': 'main',
            'action': 'in',
            'value': [plugin[1] for plugin in plugins]
        }, {
            'field': 'plugin_name',
            'action': 'in',
            'value': [plugin[2] for plugin in plugins]
        },
        fields=fields)

    results = remove_duplicate_plugins(results)

    for plugin in results:
        i_plugin = None
        for installed in plugins:
            if installed[2] == plugin['plugin_name']:
                plugin['installed_version'] = installed[3]
                plugin['installed_file'] = installed[4]
                i_plugin = installed

        if i_plugin is not None:
            plugins.remove(i_plugin)

    return results


def select_newest_version(plugin, v_type="Release"):
    """ Return the newest version in plugin which is compatible `v_type`. """
    for version in plugin['versions']:
        if type_fits(version['type'], v_type):
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

    return results


def extract_dependencies(plugins, v_type='Release'):
    """ Extract dependencies from the plugin.

    The `v_type` says what kind of version we want.

    """
    if not type(plugins) is list:
        plugins = [plugins]

    deps = list()

    for plugin in plugins:
        for version in plugin['versions']:
            if type_fits(version['type'], v_type):
                deps.extend(version['hard_dependencies'])
                break

    return deps

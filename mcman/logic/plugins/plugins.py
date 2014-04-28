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

""" The backend for the mcman plugins command. """

import os
import threading
from queue import Queue
from zipfile import ZipFile, BadZipFile

import bukget
import yaml

from mcman.logic import common
from mcman.logic.plugins import utils


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

    search_results = utils.remove_duplicate_plugins(search_results)

    # Calculate scores
    results = list()
    for plugin in search_results:
        score = plugin['popularity']['monthly']
        distance = common.levenshtein(
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

    plugins, versions = utils.extract_name_version(plugins)

    results = bukget.search(
        {
            'field': 'plugin_name',
            'action': 'in',
            'value': plugins
        },
        fields=fields)
    results += bukget.search(
        {
            'field': 'slug',
            'action': 'in',
            'value': plugins
        },
        fields=fields)
    plugins = utils.remove_duplicate_plugins(results)

    for plugin in plugins:
        if not plugin['plugin_name'].lower() in versions:
            continue

        version = versions[plugin['plugin_name'].lower()]

        for ver in plugin['versions']:
            if ver['version'] == version:
                plugin['versions'] = [ver]
                break
        else:
            plugin['versions'] = []

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
    deps = utils.extract_dependencies(plugins, v_type)

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
    if common.ask(question, skip=skip):
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
    target_folder = common.find_plugins_folder() + '/'

    url = plugin['versions'][0]['download']
    filename = common.format_name(plugin['plugin_name'])
    md5 = plugin['versions'][0]['md5']
    suffix = plugin['versions'][0]['filename'].split('.')[-1]

    full_name = target_folder + filename + '.' + suffix

    common.download(url, destination=full_name,
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

            common.extract_file(zipped, jar, destination)


def parse_installed_plugins_worker(jar_queue, result_queue):
    """ Worker function of list_plugins.

    This function takes jars in the `jar_queue`, calculates the checksum,
    and extracts the main class, name and version and push this data to the
    `result_queue`.

    """
    while not jar_queue.empty():
        jar = jar_queue.get()

        checksum = common.checksum_file(jar)

        try:
            with ZipFile(jar, 'r') as zipped:
                if 'plugin.yml' not in zipped.namelist():
                    continue

                yml = yaml.load(zipped.read('plugin.yml').decode())
                plugin_name = yml['name']
                main = yml['main']
                version = str(yml['version'])

                result_queue.put((checksum, main, plugin_name, version, jar))
        except BadZipFile:
            print("    Could not read '{}'.".format(jar))

        jar_queue.task_done()


def parse_installed_plugins(workers=4):
    """ Parse installed plugins for some information.

    The information is returned in a tuple like this:
        (jar checksum, main class, plugin name, plugin version, jar path)

    These tuples are put in a set.

    """
    folder = common.find_plugins_folder() + '/'
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
              'versions.md5,versions.slug')

    plugins = parse_installed_plugins(workers)
    if plugins == []:
        return []

    results = bukget.search(
        {
            'field': 'versions.checksum',
            'action': 'in',
            'value': [plugin[0] for plugin in plugins]
        },
        fields=fields)

    if len(results) < len(plugins):
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

    results = utils.remove_duplicate_plugins(results)

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


def find_versions(plugins):
    """ Get plugin dictionaries from BukGet only with the version.

    This function takes a list of tuples containing plugin slugs in the first
    slot and version slugs in the second slot. Returned is a list of plugin
    dictionaries. Plugins which are not found, are just ignored.

    """
    fields = ('versions.slug,versions.md5,versions.download,versions.filename,'
              'plugin_name,slug')

    results = bukget.search(
        {
            'field': 'slug',
            'action': 'in',
            'value': [plugin[0] for plugin in plugins]
        },
        fields=fields)

    final = list()
    for plugin in results:
        target_version = None
        for slug, version in plugins:
            if slug == plugin['slug']:
                target_version = version
                break
        else:
            continue

        version = None
        for vers in plugin['versions']:
            if vers['slug'] == target_version:
                version = vers
                break
        else:
            continue

        plugin['versions'] = [version]
        final.append(plugin)

    return final

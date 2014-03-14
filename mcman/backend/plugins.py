""" The backend for the mcman command. """

import os
import bukget
import yaml
from zipfile import ZipFile
from mcman.backend import common as utils


VERSION = 'release'


def init(base, user_agent):
    """ Initialize the module.

    This function just sets the base url and user agent for BukGet, and it
    sets the default version type.

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

    new_results = list()
    for result in search_results:
        for result2 in new_results:
            if result2['slug'] == result['slug']:
                break
        else:
            new_results.append(result)
    search_results = new_results

    # Calculate scores
    results = list()
    for plugin in search_results:
        if len(plugin) == 0:
            continue

        score = plugin['popularity']['monthly'] - utils.levenshtein(
            query, plugin['plugin_name'])

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


def find_newest_versions(plugins, server):
    """ Find newest versions for the plugins.

    This is a generator. When a plugin in the plugins list has an update it is
    yielded as a tuple with the plugin slug and the newest version. If the
    plugin is not found at BukGet, the plugin name is yielded alone. If a
    plugin does not have any updates, nothing is yielded.

    Three parameters are required:
        plugins    A list of plugins, as returned by list_plugins()
        server     The server the plugins are for.

    """
    for plugin in plugins:
        slug, version, name = plugin[0], plugin[1], plugin[2]
        plugin = bukget.plugin_details(server, slug,
                                       VERSION,
                                       fields='versions.version')
        if plugin is None:
            yield name
            continue
        b_version = plugin['versions'][0]['version']
        if b_version > version:
            yield slug, b_version


def download_plugin(plugin, prefix=""):
    """ Download plugin.

    This function takes two parameters. The first is the plugin. The plugin
    must be a dictionary returned by bukget with at least the following fields:
        versions.download, plugin_name, versions.md5, versions.filename
    The second parameter is a prefix to print before each output line,
    typically a counter on which download this it:
        ( 5/20)

    """
    target_folder = find_plugins_folder() + '/'

    url = plugin['versions'][0]['download']
    if ' ' in plugin['plugin_name']:
        filename = ''.join([x.capitalize() for x
                            in plugin['plugin_name'].split(' ')])
    else:
        filename = plugin['plugin_name']
    md5 = plugin['versions'][0]['md5']
    suffix = plugin['versions'][0]['filename'].split('.')[-1:][0]
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
            jars = [x for x in zipped.namelist()
                    if x.endswith('.jar')
                    and x.startswith(folder)]
            strip_folder = folder

        for jar in jars:
            utils.extract_file(zipped, jar,
                               target_folder + (
                                   jar.split(strip_folder, 1)[1]
                                   if strip_folder else jar))


def list_plugins():
    """ List installed plugins.

    Returns a set of four-tuples containing the slug, version, plugin_name and
    path to the jar, in that order.

    """
    plugins = set()

    folder = find_plugins_folder()
    jars = [folder + '/' + f for f in os.listdir(folder)
            if os.path.isfile(folder + '/' + f) and f.endswith('.jar')]
    for jar in jars:
        # We first search for a plugin with a published version with matching
        # checksum to ours.
        slug = None
        plugin_name = None
        checksum = utils.checksum_file(jar)
        result = bukget.search({'field':  'versions.md5',
                                'action': '=',
                                'value':  checksum},
                               fields='slug,versions.version,plugin_name')
        if len(result) > 0:
            slug = result[0]['slug']
            plugin_name = result[0]['plugin_name']
        # Then we search by main class
        with ZipFile(jar, 'r') as zipped:
            # If there is no plugin.yml in it
            # we ignore it
            if not 'plugin.yml' in zipped.namelist():
                continue
            yml = yaml.load(zipped.read('plugin.yml').decode())
            if slug is None:
                plugin_name = yml['name']
                main = yml['main']
                result = bukget.search({'field':  'main',
                                        'action': '=',
                                        'value':  main},
                                       fields='slug,versions.version')
                if len(result) > 0:
                    slug = result[0]['slug']
                else:
                    continue
            version = str(yml['version'])
            plugins.add((slug, version, plugin_name, jar))

    return plugins


def find_plugins_folder():
    """ Find the plugins folder.

    This will return the relative path to the plugins folder.
    Currently either '.' or 'plugins' is returend.

    """
    if 'plugins' in os.listdir('.'):
        return 'plugins'
    return '.'


def dependencies(server, plugins, versions, status_hook):
    """ Get list of dependencies to install by list of plugins.

    This function will return a list containing all the plugins in the supplied
    list of plugins plus all their dependencies.

    Parameters:
        server         The server.
        plugins        A list of plugins.
        versions       A dictionary mapping from plugins to versions.
        status_hook    A status hook, see the docs on resolve_dependencies.

    """
    new_stack = list()
    for plugin in plugins:
        resolve_dependencies(server,
                             plugin,
                             status_hook,
                             versions[plugin] if plugin in versions else None,
                             new_stack)
    return new_stack


def resolve_dependencies(server, plugin_name, status_hook,
                         version=None, stack=None):
    """ Resolve all dependencies of plugin.

    This function will recursively get a list of all dependencies of the
    plugin and the plugin itself. This means that the returned list
    contains all the plugins needed to install.

    A ValueError will be raised if a plugin isn't found. This can either be
    the plugin itself, or any of it's dependencies.

    Parameters:
       server          The server the plugin is for.
       plugin_name     The name of the plugin.
       status_hook     A status hook, explained later.
       version         An optional specific version of the plugin.
       dependencies    plugins that will allready be installed.

    The status hook should be a function that accepts an integer and a tuple.
    The integer says what status it is, and the tuple contains the values.
    Here is a list of the statuses:
        1 - Plugin not found on BukGet. Values: plugin name
        2 - Version not found on BukGet. Values: plugin name, version that was
            tried.
        3 - Dependency not found on BukGet. Values: dependency name

    """
    if version is None:
        version = VERSION
    if stack is None:
        stack = list()

    plugin = bukget.find_by_name(server, plugin_name)
    if plugin is None:
        status_hook(1, plugin_name)
        return stack

    plugin = bukget.plugin_details(server, plugin, version,
                                   fields='slug,'
                                          + 'versions.hard_dependencies,'
                                          + 'versions.version')

    if plugin['slug'] in stack:
        return stack
    if len(plugin['versions']) < 1:
        status_hook(2, (plugin_name, version))
        return stack

    stack.append(plugin['slug'])

    for dep in plugin['versions'][0]['hard_dependencies']:
        slug = bukget.find_by_name(server, dep)
        if slug is None:
            status_hook(3, dep)
            continue
        if slug not in stack:
            resolve_dependencies(server, slug, status_hook, stack=stack)

    return stack


def find_plugins(server, queries, status_hook):
    """ Find plugins.

    Parameters:
        server         Server type the plugins are for
        queryies       Plugins to try and find.
        status_hook    A status hook, see below.

    One of the parameters is a status hook. It should be a function that
    accepts an integer and a tuple. The integer is the status id, the tuple
    contains the values.

    Statuses:
        1 - Plugin not found. Values: plugin

    A tuple of a list and dict is returned. the list contains the plugins to
    install, while the versions dict contains specific versions.

    """
    to_install = list()
    versions = dict()

    for query in queries:
        plugin_version = query.rsplit('#', 1)
        plugin = plugin_version[0]
        version = ''
        slug = bukget.find_by_name(server, plugin)
        if slug is None:
            status_hook(1, plugin)
            continue
        if len(plugin_version) > 1:
            version = plugin_version[1]
            versions[slug] = version
        to_install.append(slug)

    return to_install, versions


def download_details(server, plugin, version):
    """ Get details required for download.

    This function is just a wrapper around bukget, that will get the details
    about a plugin that is required when downloading it.

    """
    return bukget.plugin_details(server, plugin, version,
                                 fields='slug,plugin_name,versions.version,'
                                        + 'versions.md5,versions.download,'
                                        + 'versions.type,'
                                        + 'versions.filename,'
                                        + 'versions.hard_dependencies,'
                                        + 'versions.soft_dependencies')


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


def find_updates(server, to_install, versions, status_hook):
    """ Find updates for plugins.

    This function will also check if the plugins are allready installed.

    Parameters:
        server         The server
        to_install     A list over plugins that should be installed
        versions       A dict with optional specific versions for plugins
        status_hook    A status hook

    """
    plugins = list()
    installed = list_plugins()

    for slug in to_install:
        plugin = download_details(server, slug,
                                  versions[slug]
                                  if slug in versions
                                  else VERSION)

        if plugin is None:
            status_hook(1, slug)
            continue
        elif len(plugin['versions']) < 1:
            status_hook(2, slug)
            continue

        for i in installed:
            if i[0] == slug and i[1] >= plugin['versions'][0]['version']:
                status_hook(3, plugin['plugin_name'])
                break
            elif i[0] == slug:
                status_hook(4, plugin['plugin_name'])
        else:
            plugins.append(plugin)

    return plugins

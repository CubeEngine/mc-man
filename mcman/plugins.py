""" mcman plugins module. """

# Imports from the python library:
import zipfile
import os
from urllib.error import URLError
# Imports from dependencies:
import yaml
from bukget import api as bukget
# Imports from mcman:
from mcman import utils


class Plugins(object):

    """ The plugins command for mcman. """

    def __init__(self, args):
        """ Parse command, and execute tasks. """
        bukget.BASE = args.base_url
        bukget.USER_AGENT = args.user_agent
        self.server = args.server
        self.version = args.version

        self.args = args

        try:
            if args.subcommand is 'search':
                self.search()
            elif args.subcommand is 'info':
                self.info()
            elif args.subcommand is 'download':
                self.download()
            elif args.subcommand is 'update':
                self.update()
            elif args.subcommand is 'list':
                self.list()
            else:
                return
        except URLError as err:
            print('Error from BukGet: ' + str(err))

    def search(self):
        """ Search. """
        query = self.args.query
        print('Searching for `{}`'.format(query))

        search_results = bukget.search(
            {
                'field': 'plugin_name',
                'action': 'like',
                'value': query
            },
            {
                'field': 'server',
                'action': '=',
                'value': self.server
            }, sort=('-' if self.args.size >= 0 else '')+'popularity.monthly',
            fields=['slug',
                    'plugin_name',
                    'description',
                    'popularity.monthly'],
            size=abs(self.args.size))

        results = list()
        for plugin in search_results:
            if len(plugin) == 0:
                continue
            results.append((plugin['popularity']['monthly']
                            - utils.levenshtein(query, plugin['plugin_name']),
                            plugin))

        results.sort(key=lambda x: x[0], reverse=True)

        print()

        formatting = '{:<20} - {:<20} - {}'
        print(formatting.format('Unique identifier', 'Name', 'Description'))
        print('=' * 57)
        for i in range(min(len(results), abs(self.args.size))):
            plugin = results[i][1]
            print(formatting.format(plugin['slug'],
                                    plugin['plugin_name'].strip(),
                                    plugin['description'].strip()))

    def info(self):
        """ Info. """
        for query in self.args.plugins:
            print('Looking up `{}`'.format(query))
            slug = bukget.find_by_name(self.server, query)
            if slug is None:
                print('Could not find `{}`'.format(query))
                continue
            plugin = bukget.plugin_details(self.server, slug, fields=[
                'website', 'dbo_page', 'description', 'versions.type',
                'versions.game_versions', 'versions.version', 'plugin_name',
                'server', 'authors', 'categories', 'stage', 'slug'])
            print('Name:       {}'.format(plugin['plugin_name']))
            print('Authors:    {}'.format(utils.list_names(
                plugin['authors'])))
            print('Categories: {}'.format(utils.list_names(
                plugin['categories'])))
            if len(plugin['website']) > 0:
                print('Website:    {}'.format(plugin['website']))
            else:
                print('Website:    {}'.format(plugin['dbo_page']))
            print('Versions:')
            versions = plugin['versions']
            if self.args.size >= 0:
                versions = versions[
                    :min(self.args.size, len(versions))]
            else:
                versions = versions[
                    max(self.args.size, -len(versions)):]
            size = max([len(v['version']) for v in versions])
            for version in versions:
                print('    {}:{}    {}'.format(
                    version['version'], ' ' * (size-len(version['version'])),
                    utils.list_names(version['game_versions'])))
            print()

    def download(self):
        """ Download. """
        print('Resolving plugins and their dependencies...')
        to_install, versions = self.find_plugins(self.args.plugins)

        if len(to_install) < 1:
            print('Found no plugins!')
            return

        installed = list_plugins()
        plugins = list()
        for slug in to_install:
            plugin = bukget.plugin_details(
                self.server, slug, versions[slug] if slug in versions
                else self.version, fields=[
                    'slug', 'plugin_name', 'versions.version', 'versions.md5',
                    'versions.download', 'versions.type', 'versions.filename',
                    'versions.hard_dependencies', 'versions.soft_dependencies']
                )
            if plugin is None:
                print('    Could not find plugin {} again!'.format(slug))
            elif len(plugin['versions']) < 1:
                print('    Could not find version of {} again!'.format(slug))
            else:
                for installed_plugin in installed:
                    if installed_plugin[0] == slug:
                        if installed_plugin[1] == plugin['versions'][0][
                                'version']:
                            print('    {} was allready installed.'.format(
                                plugin['plugin_name']))
                            break
                        print('    {} is allready installed, but out of date'
                              .format(plugin['plugin_name']))
                else:
                    plugins.append(plugin)

        if len(plugins) < 1:
            print('No plugins left to install...')
            return

        print('Plugins to install:')
        print('    {}'.format(utils.list_names(
            [p['plugin_name'] + '#' + p['versions'][0]['version']
             for p in plugins])))

        print('Press enter to install the plugins. If you want to abort, '
              + 'press Ctrl+D or Ctrl+C')
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            return

        prefix_format = '({{part:>{}}}/{{total}}) '.format(
            len(str(len(plugins))))

        for i in range(len(plugins)):
            plugin = plugins[i]
            prefix = prefix_format.format(total=len(plugins), part=i+1)
            download_plugin(plugin, prefix)

    def update(self):
        """ Update. """
        print('Finding plugins to update...')
        to_update = list()
        for plugin, i_version in list_plugins():
            u_plugin = bukget.plugin_details(self.server, plugin, self.version,
                                             fields=['versions.version',
                                                     'versions.md5',
                                                     'versions.download',
                                                     'versions.filename',
                                                     'plugin_name'])
            if u_plugin is None or len(u_plugin['versions']) < 1:
                print('Could not find {} on BukGet!'.format(plugin))
                continue
            u_version = u_plugin['versions'][0]['version']
            if u_version > i_version:
                to_update.append(u_plugin)

        if len(to_update) < 1:
            print('All plugins are up to date!')
            return

        print('Plugins to update:')
        print('    {}'.format(utils.list_names(
            [p['plugin_name'] + '#' + p['versions'][0]['version']
             for p in to_update])))
        print('Press enter to install the plugins. If you want to abort, '
              + 'press Ctrl+D or Ctrl+C')
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            return

        prefix_format = '({{part:>{}}}/{{total}}) '.format(
            len(str(len(to_update))))

        for i in range(len(to_update)):
            plugin = to_update[i]
            prefix = prefix_format.format(total=len(to_update), part=i+1)
            download_plugin(plugin, prefix)

    def list(self):
        """ List. """
        print('Installed plugins:')
        plugins = list_plugins()
        plugins = [x[0] + '#' + x[1] for x in plugins]
        print('    {}'.format(utils.list_names(plugins)))

    def resolve_dependencies(self, plugin_name, version=None,
                             dependencies=None):
        """ Resolve all dependencies of plugin.

        This function will recursively get a list of all dependencies of the
        plugin and the plugin itself. This means that the returned list
        contains all the plugins needed to install.

        A ValueError will be raised if a plugin isn't found. This can either be
        the plugin itself, or any of it's dependencies.

        """
        if version is None:
            version = self.version
        if dependencies is None:
            dependencies = list()
        plugin = bukget.find_by_name(self.server, plugin_name)
        if plugin is None:
            raise ValueError('Could not find plugin {}'.format(plugin_name))
        plugin = bukget.plugin_details(self.server, plugin, version, fields=[
            'slug', 'versions.hard_dependencies', 'versions.version'])
        if plugin['slug'] in dependencies:
            return dependencies
        if len(plugin['versions']) < 1:
            raise ValueError('Could not find version {} of {}'.format(
                version, plugin_name))
        dependencies.append(plugin['slug'])
        for dep in plugin['versions'][0]['hard_dependencies']:
            slug = bukget.find_by_name(self.server, dep)
            if slug not in dependencies:
                self.resolve_dependencies(slug, dependencies=dependencies)
        return dependencies

    def find_plugins(self, queries):
        """ Find plugins. """
        to_install = list()
        versions = dict()

        for query in queries:
            plugin_version = query.rsplit('#', 1)
            plugin = plugin_version[0]
            version = ''
            if len(plugin_version) > 1:
                version = plugin_version[1]
                versions[plugin] = version
            try:
                if self.args.resolve_dependencies:
                    self.resolve_dependencies(plugin, version, to_install)
                else:
                    to_install.append(bukget.find_by_name(self.server, plugin))
            except ValueError as err:
                print('    {}'.format(err.args[0]))
        to_install = [p for p in to_install if p is not None]

        return to_install, versions


def download_plugin(plugin, prefix=""):
    """ Download plugin.

    This function takes two parameters. The first is the plugin. The plugin
    must be a dictionary returned by bukget with at least the following fields:
        versions.download, plugin_name, versions.md5, versions.filename
    The second parameter is a prefix to pring before each output line,
    typically a counter on which download this is:
        ( 5/20)

    """
    url = plugin['versions'][0]['download']
    filename = ''.join([x.capitalize() for x
                        in plugin['plugin_name'].split(' ')])
    md5 = plugin['versions'][0]['md5']
    suffix = plugin['versions'][0]['filename'].split('.')[-1:][0]
    full_name = filename + '.' + suffix

    utils.download(url, file_name=full_name,
                   checksum=md5, prefix=prefix, display_name=filename)

    if suffix == 'zip':
        print(' '*len(prefix) + 'Unzipping...', end=' ')
        with zipfile.ZipFile(full_name, 'r') as zipped:
            folders = [x for x in zipped.namelist()
                       if len(x.split('/')) == 2 and x.endswith('/')]
            jars = [x for x in zipped.namelist()
                    if len(x.split('/')) == 1 and x.endswith('.jar')]
            strip_folder = False
            if len(jars) == 0 and len(folders) > 0:
                folder = folders[0]
                folders = [x for x in zipped.namelist()
                           if len(x.split('/')) == 3 and x.endswith('/')
                           and x.startswith(folder)]
                jars = [x for x in zipped.namelist()
                        if len(x.split('/')) == 2 and x.endswith('.jar')
                        and x.startswith(folder)]
                strip_folder = folder

            for jar in jars:
                utils.extract_file(zipped, jar,
                                   (jar.split(strip_folder, 1)[1]
                                    if strip_folder else jar))
            for folder in folders:
                children = [x for x in zipped.namelist()
                            if x.startswith(folder)]
                for child in children:
                    utils.extract_file(zipped, child,
                                       (child.split(strip_folder, 1)[1]
                                        if strip_folder else child))
        os.remove(full_name)
        print('Success')


def list_plugins():
    """ List installed plugins.

    Returns a set of two-tuples with strings. The first value if the plugin
    slug, the second is the installed version.

    """
    plugins = set()

    jars = [f for f in os.listdir('.')
            if os.path.isfile(f) and f.endswith('.jar')]
    for jar in jars:
        # We first search for a plugin with a published version with matching
        # checksum to ours.
        slug = None
        checksum = utils.checksum_file(jar)
        result = bukget.search({'field':  'versions.md5',
                                'action': '=',
                                'value':  checksum},
                               fields=['slug', 'versions.version'])
        if len(result) > 0:
            slug = result[0]['slug']
        # Then we search by main class
        with zipfile.ZipFile(jar, 'r') as zipped:
            # If there is no plugin.yml in it
            # we ignore it
            if not 'plugin.yml' in zipped.namelist():
                continue
            info = yaml.load(zipped.read('plugin.yml').decode())
            if slug is None:
                main = info['main']
                result = bukget.search({'field':  'main',
                                        'action': '=',
                                        'value':  main},
                                       fields=['slug', 'versions.version'])
                if len(result) > 0:
                    slug = result[0]['slug']
                else:
                    continue
            version = str(info['version'])
            plugins.add((slug, version))

    return plugins

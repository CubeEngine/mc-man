""" mcman plugins module. """

# Imports from the python library:
import zipfile
import os
from urllib.error import URLError
# Imports from dependencies:
import yaml
import bukget
# Imports from mcman:
from mcman import utils


class Plugins(object):

    """ The plugins command for mcman. """

    prefix = ' :: '

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
        except (URLError, ValueError) as err:
            self.prnt('Error: {}'.format(str(err)), filled_prefix=False)

    def prnt(self, message, filled_prefix=True, prefix=True):
        """ Print general output. """
        if prefix:
            if filled_prefix:
                prefix = self.prefix
            else:
                prefix = ' ' * len(self.prefix)
        else:
            prefix = ''
        print(prefix + message)

    def error(self, error):
        """ Print error. """
        self.prnt('Error from SpaceGDN: {}'.format(error['message']),
                  filled_prefix=False)

    def search(self):
        """ Search. """
        query = self.args.query
        self.prnt('Searching for `{}` through BukGet'.format(query))

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
            fields='slug,plugin_name,description,popularity.monthly',
            size=abs(self.args.size))

        # Sort results
        results = list()
        for plugin in search_results:
            if len(plugin) == 0:
                continue
            score = plugin['popularity']['monthly'] \
                - utils.levenshtein(query, plugin['plugin_name'])
            results.append((score, plugin,
                            '[{}]{}'.format(plugin['slug'],
                                            plugin['plugin_name'])))
        results.sort(key=lambda x: x[0], reverse=True)

        max_len = max([len(p[2]) for p in results])
        frmt = '{{:<{}}} - {{}}'.format(max_len)

        self.prnt('Results:')
        self.prnt('', False, False)

        for i in range(min(len(results), abs(self.args.size))):
            plugin = results[i]
            self.prnt(frmt.format(plugin[2], plugin[1]['description'].strip()),
                      filled_prefix=False)

        self.prnt('', False, False)

    def info(self):
        """ Info. """
        query = self.args.plugins
        self.prnt('Finding `{}` on BukGet'.format(query))

        slug = bukget.find_by_name(self.server, query)
        if slug is None:
            self.prnt('Could not find `{}`'.format(query), filled_prefix=False)
            return

        plugin = bukget.plugin_details(self.server, slug,
                                       fields='website,dbo_page,'
                                              + 'description,'
                                              + 'versions.type,'
                                              + 'versions.game_versions,'
                                              + 'versions.version,'
                                              + 'plugin_name,server,'
                                              + 'authors,categories,'
                                              + 'stage,slug')

        self.prnt('Found {}'.format(plugin['plugin_name']))
        self.prnt('', False, False)

        website = plugin['website']
        if len(website) == 0:
            website = plugin['dbo_page']
        authors = utils.list_names(plugin['authors'])
        categories = utils.list_names(plugin['categories'])
        stage = plugin['stage']
        name = plugin['plugin_name']

        self.prnt('Name:       {}'.format(name), filled_prefix=False)
        self.prnt('Authors:    {}'.format(authors), filled_prefix=False)
        self.prnt('Website:    {}'.format(website), filled_prefix=False)
        self.prnt('Categories: {}'.format(categories), filled_prefix=False)
        self.prnt('Stage:      {}'.format(stage), filled_prefix=False)
        self.prnt('', False, False)
        self.prnt('Versions:', filled_prefix=False)

        versions = plugin['versions']
        # Sorting
        if self.args.size >= 0:
            versions = versions[
                :min(self.args.size, len(versions))]
        else:
            versions = versions[
                max(self.args.size, -len(versions)):]
        max_len = max([len(v['version']) for v in versions])
        frmt = '    {{:>{}}} - {{}}'.format(max_len)
        for version in versions:
            game_versions = utils.list_names(version['game_versions'])
            self.prnt(frmt.format(version['version'], game_versions),
                      filled_prefix=False)
        self.prnt('', False, False)

    def download(self):
        """ Download. """
        self.prnt('Finding plugins on BukGet')

        to_install, versions = self.find_plugins(self.args.plugins)

        self.prnt('Resolving dependencies')

        new_stack = list()
        for plugin in to_install:
            self.resolve_dependencies(plugin,
                                      versions[plugin] if plugin in versions
                                      else None,
                                      new_stack)
        to_install = new_stack

        if len(to_install) < 1:
            self.prnt('Found no plugins!', filled_prefix=False)
            return

        self.prnt(
            'Resolving versions, and checking allready installed plugins')

        installed = list_plugins()
        plugins = list()
        for slug in to_install:
            plugin = bukget.plugin_details(
                self.server, slug, versions[slug] if slug in versions
                else self.version, fields='slug,plugin_name,versions.version,'
                                          + 'versions.md5,versions.download,'
                                          + 'versions.type,'
                                          + 'versions.filename,'
                                          + 'versions.hard_dependencies,'
                                          + 'versions.soft_dependencies')

            if plugin is None:
                self.prnt('Could not find plugin `{}` again'.format(slug))
                continue
            elif len(plugin['versions']) < 1:
                self.prnt('Could not find version of `{}` again'.format(slug))
                continue

            for installed_plugin in installed:
                if installed_plugin[0] == slug:
                    if installed_plugin[1] >= plugin['versions'][0]['version']:
                        self.prnt('{} was allready installed.'
                                  .format(plugin['plugin_name']),
                                  filled_prefix=False)
                        break
                    self.prnt('{} is allready installed, but out of date'
                              .format(plugin['plugin_name']),
                              filled_prefix=False)
            else:
                plugins.append(plugin)

        if len(plugins) < 1:
            self.prnt('No plugins left to install')
            return

        self.prnt('Plugins to install:')
        self.prnt('', False, False)
        self.prnt(utils.list_names([p['plugin_name'] + '#'
                                    + p['versions'][0]['version']
                                    for p in plugins]),
                  filled_prefix=False)

        self.prnt('', False, False)
        if utils.ask('Continue to download?', skip=self.args.no_confirm):
            prefix_format = '({{part:>{}}}/{{total}}) '.format(
                len(str(len(plugins))))

            for i in range(len(plugins)):
                plugin = plugins[i]
                prefix = prefix_format.format(total=len(plugins), part=i+1)
                download_plugin(plugin, prefix)

        self.prnt('', False, False)
        self.prnt('Done!', False, False)

    def update(self):
        """ Update. """
        self.prnt('Finding installed plugins')

        installed = list_plugins()

        self.prnt('Looking up versions on BukGet')

        to_update = list()
        for plugin, i_version, name, ignored in installed:
            u_plugin = bukget.plugin_details(self.server, plugin, self.version,
                                             fields='versions.version,'
                                                    + 'versions.md5,'
                                                    + 'versions.download,'
                                                    + 'versions.filename,'
                                                    + 'plugin_name')
            if u_plugin is None or len(u_plugin['versions']) < 1:
                self.prnt('Could not find {} on BukGet!'.format(name),
                          filled_prefix=False)
                continue

            u_version = u_plugin['versions'][0]['version']
            if u_version > i_version:
                to_update.append(u_plugin)

        if len(to_update) < 1:
            self.prnt('All plugins are up to date!')
            return

        self.prnt('Plugins to update:')
        self.prnt('', False, False)
        self.prnt(utils.list_names([p['plugin_name'] + '#'
                                    + p['versions'][0]['version']
                                    for p in to_update]),
                  filled_prefix=False)
        self.prnt('', False, False)

        if utils.ask('Continue to update?', skip=self.args.no_confirm):
            prefix_format = '({{part:>{}}}/{{total}}) '.format(
                len(str(len(to_update))))

            for i in range(len(to_update)):
                plugin = to_update[i]
                prefix = prefix_format.format(total=len(to_update), part=i+1)
                download_plugin(plugin, prefix)
            self.prnt('', False, False)
            self.prnt('Done!', False, False)

    def list(self):
        """ List. """
        self.prnt('Finding installed plugins')

        plugins = list_plugins()

        if len(plugins) == 0:
            self.prnt('Found no plugins')
            return

        self.prnt('Looking up plugins on BukGet')

        new_versions = dict()
        for slug, version, name, jar in plugins:
            plugin = bukget.plugin_details(self.server, slug,
                                           self.version,
                                           fields='versions.version')
            if plugin is None:
                self.prnt('Could not find {} on BukGet'.format(name),
                          filled_prefix=False)
                continue
            b_version = plugin['versions'][0]['version']
            if b_version > version:
                new_versions[slug] = b_version

        self.prnt('Installed plugins:')
        self.prnt('', False, False)

        max_name_len = max([len('[{}]{}'.format(p[3], p[2])) for p in plugins])
        max_ver_len = max([len(p[1]) for p in plugins])
        frmt = '{{:<{}}} - {{:<{}}}'.format(max_name_len, max_ver_len)

        for slug, version, name, jar in plugins:
            line = frmt.format('[{}]{}'.format(jar, name), version)
            if slug in new_versions:
                new_version = new_versions[slug]
                line += '  -- Out of date, newest version: {}'.format(
                    new_version)
            self.prnt(line, filled_prefix=False)
        self.prnt('', False, False)

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
            self.prnt('Could not find `{}`'.format(plugin_name),
                      filled_prefix=False)
            return dependencies

        plugin = bukget.plugin_details(self.server, plugin, version,
                                       fields='slug,'
                                              + 'versions.hard_dependencies,'
                                              + 'versions.version')

        if plugin['slug'] in dependencies:
            return dependencies
        if len(plugin['versions']) < 1:
            self.prnt('Could not find version `{}` of `{}`'.format(
                version, plugin_name), filled_prefix=False)
            return dependencies

        dependencies.append(plugin['slug'])

        for dep in plugin['versions'][0]['hard_dependencies']:
            slug = bukget.find_by_name(self.server, dep)
            if slug is None:
                self.prnt('Could not find `{}`'.format(dep),
                          filled_prefix=False)
                continue
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
            slug = bukget.find_by_name(self.server, plugin)
            if slug is None:
                self.prnt('Could not find `{}`'.format(plugin),
                          filled_prefix=False)
                continue
            if len(plugin_version) > 1:
                version = plugin_version[1]
                versions[slug] = version
            to_install.append(slug)

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
    target_folder = find_plugins_folder() + '/'
    url = plugin['versions'][0]['download']
    if ' ' in plugin['plugin_name']:
        filename = ''.join([x.capitalize() for x
                            in plugin['plugin_name'].split(' ')])
    else:
        filename = plugin['plugin_name']
    md5 = plugin['versions'][0]['md5']
    suffix = plugin['versions'][0]['filename'].split('.')[-1:][0]
    full_name = filename + '.' + suffix

    utils.download(url, file_name=full_name,
                   checksum=md5, prefix=prefix, display_name=filename)

    if suffix == 'zip':
        print(' '*len(prefix) + 'Unzipping...', end=' ')
        with zipfile.ZipFile(full_name, 'r') as zipped:
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
        os.remove(full_name)
        print('Success')


def list_plugins():
    """ List installed plugins.

    Returns a set of two-tuples with strings. The first value if the plugin
    slug, the second is the installed version.

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
        with zipfile.ZipFile(jar, 'r') as zipped:
            # If there is no plugin.yml in it
            # we ignore it
            if not 'plugin.yml' in zipped.namelist():
                continue
            info = yaml.load(zipped.read('plugin.yml').decode())
            if slug is None:
                plugin_name = info['name']
                main = info['main']
                result = bukget.search({'field':  'main',
                                        'action': '=',
                                        'value':  main},
                                       fields='slug,versions.version')
                if len(result) > 0:
                    slug = result[0]['slug']
                else:
                    continue
            version = str(info['version'])
            plugins.add((slug, version, plugin_name, jar))

    return plugins


def find_plugins_folder():
    """ Find the plugins folder. """
    if 'plugins' in os.listdir('.'):
        return 'plugins'
    return '.'

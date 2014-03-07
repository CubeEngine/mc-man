""" mcman plugins module. """
from bukget import api as bukget
from mcman import utils


class Plugins(object):

    """ The plugins command for mcman. """

    def __init__(self, args):
        """ Parse command, and execute tasks. """
        bukget.BASE = args.base_url
        bukget.USER_AGENT = args.user_agent
        self.server = args.server
        self.version = args.version
        self.resolve_dependencies = args.resolve_dependencies

        self.args = args

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
                ['plugin.authors'])))
            print('Categories: {}'.format(utils.list_names(
                ['plugin.categories'])))
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
        to_install = list()
        versions = dict()
        for query in self.args.plugins:
            plugin_version = query.rsplit('#', 1)
            plugin = plugin_version[0]
            version = ''
            if len(plugin_version) > 1:
                version = plugin_version[1]
                versions[plugin] = version
            try:
                if self.resolve_dependencies:
                    self.resolve_dependencies(plugin, version, to_install)
                else:
                    to_install.append(bukget.find_by_name(self.server, plugin))
            except ValueError as err:
                print('    {}'.format(err.args[0]))
        to_install = [p for p in to_install if p is not None]
        if len(to_install) < 1:
            print('Found no plugins!')
            return
        plugins = list()
        for slug in to_install:
            plugin = bukget.plugin_details(
                self.server, slug, versions[slug] if slug in versions
                else self.version, fields=[
                    'slug', 'plugin_name', 'versions.version', 'versions.md5',
                    'versions.download', 'versions.type', 'versions.file_name',
                    'versions.hard_dependencies', 'versions.soft_dependencies']
                )
            if plugin is None:
                print('    Could not find plugin {} again!'.format(slug))
            if len(plugin['versions']) < 1:
                print('    Could not find version of {} again!'.format(slug))
            else:
                plugins.append(plugin)

        print('Plugins to install:')
        print('    {}'.format(utils.list_names(
            [p['plugin_name'] + '#' + p['versions'][0]['version']
             for p in plugins])))

    def update(self):
        """ Update. """
        print('update:', self.args)

    def list(self):
        """ List. """
        print('list:', self.args)

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

""" mcman plugins module. """
from bukget import orm as bukget
from bukget import api as bukgetapi
from mcman import utils

SERVER = 'bukkit'


class Plugins(object):

    """ The plugins command for mcman. """

    def __init__(self, args):
        """ Parse command, and execute tasks. """
        bukgetapi.BASE = args.base_url
        bukgetapi.USER_AGENT = args.user_agent
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
                'value': SERVER
            }, sort=('-' if self.args.size > 0 else '')+'popularity.monthly',
            fields=['slug',
                    'plugin_name',
                    'description',
                    'popularity.monthly'],
            size=abs(self.args.size))

        results = list()

        for plugin in search_results:
            results.append((plugin.popularity_monthly
                            - utils.levenshtein(query, plugin.plugin_name),
                            plugin))

        results.sort(key=lambda x: x[0], reverse=True)

        print()

        formatting = '{:<20} - {:<20} - {}'
        print(formatting.format('Unique identifier', 'Name', 'Description'))
        print('=' * 57)
        for i in range(min(len(results), abs(self.args.size))):
            plugin = results[i][1]
            print(formatting.format(plugin.slug,
                                    plugin.plugin_name.strip(),
                                    plugin.description.strip()))

    def info(self):
        """ Info. """
        print('info:', self.args)
        for query in self.args.plugins:
            print('Looking up `{}`'.format(query))
            plugin = bukget.find_by_name(SERVER, query)
            if plugin is None:
                print('Could not find `{}`'.format(query))
                continue
            print(repr(plugin))

    def download(self):
        """ Download. """
        print('download:', self.args)

    def update(self):
        """ Update. """
        print('update:', self.args)

    def list(self):
        """ List. """
        print('list:', self.args)

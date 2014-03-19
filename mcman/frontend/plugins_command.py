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

""" The plugin command of mcman.

This module is the home of the front end part of the command. This menas that
as little as possible logic should go here. The logic is placed the the plugins
module in the backend package.

"""

from urllib.error import URLError
from mcman.status_handler import StatusHandler
from mcman.backend import plugins as backend
from mcman.backend import common as utils
from mcman.frontend.common import Command


class PluginsCommand(Command):

    """ The plugin command of mcman. """

    def __init__(self, args):
        """ Parse command, and execute tasks. """
        Command.__init__(self)

        self.server = args.server
        self.args = args

        backend.init(args.base_url, args.user_agent)
        backend.VERSION = self.args.version

        self.register_subcommand('search', self.search)
        self.register_subcommand('info', self.info)
        self.register_subcommand('list', self.list)
        self.register_subcommand('download', self.download)
        self.register_subcommand('update', self.update)

        self.invoke_subcommand(args.subcommand, (ValueError, URLError))

    def search(self):
        """ Search for plugins. """
        query = self.args.query

        self.p_main('Searching for `{}` through BukGet'.format(query))

        results = [(result, '[{}]{}'.format(result['slug'],
                                            result['plugin_name']))
                   for result in backend.search(query, self.args.size)]

        # Find lenght of longest slug + name
        max_len = max([len(p[1]) for p in results])

        # Create the format
        frmt = '{{:<{}}} - {{}}'.format(max_len)

        self.p_main('Results:')
        self.p_blank()

        for i in range(min(len(results), abs(self.args.size))):
            plugin = results[i]
            line = frmt.format(plugin[1], plugin[0]['description'].strip())
            self.p_sub(line)

        self.p_blank()

    def info(self):
        """ Display info about a plugin. """
        query = self.args.plugins
        self.p_main('Finding `{}` on BukGet'.format(query))

        plugin = backend.info(self.server, query)
        if plugin is None:
            self.p_sub('Could not find `{}`'.format(query))
            return

        self.p_main('Found {}:'.format(plugin['plugin_name']))
        self.p_blank()

        website = plugin['website']
        if len(website) == 0:
            website = plugin['dbo_page']
        authors = utils.list_names(plugin['authors'])
        categories = utils.list_names(plugin['categories'])
        stage = plugin['stage']
        name = plugin['plugin_name']
        desciption = plugin['description'].strip()

        self.p_sub('Name:        {}', name)
        self.p_sub('Description: {}', desciption)
        self.p_sub('Authors:     {}', authors)
        self.p_sub('Website:     {}', website)
        self.p_sub('Categories:  {}', categories)
        self.p_sub('Stage:       {}', stage)

        self.p_blank()
        self.p_sub('Versions:')

        versions = plugin['versions']

        # Sorting
        if self.args.size >= 0:
            versions = versions[:min(self.args.size, len(versions))]
        else:
            versions = versions[max(self.args.size, -len(versions)):]

        # Formatting
        max_len = max([len(v['version']) for v in versions])
        frmt = '    {{:>{}}} - {{}}'.format(max_len)

        for version in versions:
            line = frmt.format(version['version'],
                               utils.list_names(version['game_versions']))
            self.p_sub(line)

        self.p_blank()

    def list(self):
        """ List installed plugins. """
        self.p_main('Finding installed plugins')

        plugins = backend.list_plugins()

        if len(plugins) == 0:
            self.p_sub('Found no plugins')
            return

        self.p_main('Looking up plugins on BukGet')

        new_versions = dict()
        for yielded in backend.find_newest_versions(plugins, self.server):
            if type(yielded) is tuple:
                slug, version = yielded
                new_versions[slug] = version
            elif type(yielded) is str:
                self.p_sub('Could not find {} on BukGet'.format(yielded))

        self.p_main('Installed plugins:')
        self.p_blank()

        max_name_len = max([len('[{}]{}'.format(p[3], p[2])) for p in plugins])
        max_ver_len = max([len(p[1]) for p in plugins])
        frmt = '{{:<{}}} - {{:<{}}}'.format(max_name_len, max_ver_len)

        for slug, version, name, jar in plugins:
            line = frmt.format('[{}]{}'.format(jar, name), version)
            if slug in new_versions:
                new_version = new_versions[slug]
                line += '  -- Out of date, newest version: {}'.format(
                    new_version)
            self.p_sub(line)

        self.p_blank()

    def download(self):
        """ Download plugins. """
        self.p_main('Finding plugins on BukGet')

        status_handler = StatusHandler()
        status_handler.register_handler(1, lambda arguments:
                                        self.p_sub('Could not find {}'.format(
                                            arguments[0])))
        to_install, versions = backend.find_plugins(self.args.server,
                                                    self.args.plugins,
                                                    status_handler.get_hook())

        self.p_main('Resolving dependencies')

        status_handler = StatusHandler()
        one_three = lambda arguments: \
            self.p_sub('Could not find `{}`'.format(arguments))
        two = lambda arguments: \
            self.p_sub('Could not find version `{}` of `{}`'.format(
                arguments[0], arguments[1]))
        status_handler.register_handler(1, one_three)
        status_handler.register_handler(2, two)
        status_handler.register_handler(3, one_three)
        to_install = backend.dependencies(self.args.server, to_install,
                                          versions, status_handler.get_hook())

        if len(to_install) < 1:
            self.p_main('Found no plugins!')
            return

        self.p_main(
            'Resolving versions, and checking allready installed plugins')

        status_handler = StatusHandler()
        one = lambda argument: \
            self.p_sub('Could not find plugin `{}` again'.format(argument))
        two = lambda argument: \
            self.p_sub('Could not find version of `{}` again'.format(
                argument))
        three = lambda argument: \
            self.p_sub('{} was allready installed.'.format(
                argument))
        four = lambda argument: \
            self.p_sub('{} is allready installed, but out of date'.format(
                argument))
        status_handler.register_handler(1, one)
        status_handler.register_handler(2, two)
        status_handler.register_handler(3, three)
        status_handler.register_handler(4, four)

        plugins = backend.find_updates(self.server, to_install, versions,
                                       status_handler.get_hook())

        if len(plugins) < 1:
            self.p_main('No plugins left to install')
            return

        self.p_main('Plugins to install:')
        self.p_blank()
        self.p_sub(utils.list_names([p['plugin_name'] + '#'
                                    + p['versions'][0]['version']
                                    for p in plugins]))
        self.p_blank()

        backend.download('Continue to download?',
                         '({{part:>{}}}/{{total}}) '.format(
                             len(str(len(plugins)))),
                         plugins, self.args.no_confirm)

        self.p_blank()
        self.p_raw('Done!')

    def update(self):
        """ Update installed plugins. """
        self.p_main('Finding installed plugins')

        installed = backend.list_plugins()

        self.p_main('Looking up versions on BukGet')

        to_update = list()
        for i in installed:
            plugin, i_version, name = i[0], i[1], i[2]
            u_plugin = backend.download_details(self.server, plugin,
                                                self.args.version)
            if u_plugin is None or len(u_plugin['versions']) < 1:
                self.p_sub('Could not find {} on BukGet!'.format(name))
                continue

            u_version = u_plugin['versions'][0]['version']
            if u_version > i_version:
                to_update.append(u_plugin)

        self.p_main('Plugins to update:')
        self.p_blank()

        if len(to_update) < 1:
            self.p_sub('All plugins are up to date!')
            self.p_blank()
            return

        self.p_sub(utils.list_names([p['plugin_name'] + '#'
                                     + p['versions'][0]['version']
                                     for p in to_update]))
        self.p_blank()

        if utils.ask('Continue to update?', skip=self.args.no_confirm):
            prefix_format = '({{part:>{}}}/{{total}}) '.format(
                len(str(len(to_update))))

            for i in range(len(to_update)):
                plugin = to_update[i]
                prefix = prefix_format.format(total=len(to_update), part=i+1)
                backend.download_plugin(plugin, prefix)
            self.p_blank()
            self.p_raw('Done!')

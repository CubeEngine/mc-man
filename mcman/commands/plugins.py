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

import os
from urllib.error import URLError

from mcman.logic.plugins import plugins as backend
from mcman.logic.plugins import utils
from mcman.logic import common
from mcman.command import Command


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

        self.p_main('Results:')
        self.p_blank()

        if len(results) < 1:
            self.p_sub('No results...')
            self.p_blank()
            return

        # Find lenght of longest slug + name
        max_len = max([len(p[1]) for p in results])

        # Create the format
        frmt = '{{:<{}}} - {{}}'.format(max_len)

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
        authors = common.list_names(plugin['authors'])
        categories = common.list_names(plugin['categories'])
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
        self.p_sub('    R - Release, B - Beta, A - Alpha')

        versions = plugin['versions']
        # Sorting
        if self.args.size >= 0:
            versions = versions[:min(self.args.size, len(versions))]
        else:
            versions = versions[max(self.args.size, -len(versions)):]

        # Formatting
        max_len = max([len(v['version']) for v in versions])
        frmt = '({{:1}})    {{:>{}}} - {{}}'.format(max_len)

        for version in versions:
            line = frmt.format(version['type'].upper()[0], version['version'],
                               common.list_names(version['game_versions']))
            self.p_sub(line)

        self.p_blank()

    def list(self):
        """ List installed plugins. """
        self.p_main('Finding installed plugins')

        plugins = backend.list_plugins()

        if len(plugins) == 0:
            self.p_sub('Found no plugins')
            return

        self.p_main('Installed plugins:')
        self.p_blank()

        max_name_len = max([len('[{}]{}'.format(p['installed_file'],
                                                p['plugin_name']))
                            for p in plugins])
        max_ver_len = max([len(p['installed_version']) for p in plugins])
        frmt = '{{:<{}}} - {{:<{}}}'.format(max_name_len, max_ver_len)

        for plugin in plugins:
            jar = plugin['installed_file']
            name = plugin['plugin_name']
            version = plugin['installed_version']

            line = frmt.format('[{}]{}'.format(jar, name), version)
            newest_version = utils.select_newest_version(plugin,
                                                         self.args.version)
            if newest_version is not None and \
                    newest_version['version'] > version:
                new_version = newest_version['version']
                line += '  -- Out of date, newest version: {}'.format(
                    new_version)
            self.p_sub(line)

        self.p_blank()

    def download(self):
        """ Download plugins. """
        self.args.ignored = [e.lower() for e in self.args.ignored]

        self.p_main('Finding installed plugins')
        installed = backend.list_plugins()

        self.p_main('Finding plugins on BukGet')
        plugins = backend.dependencies(self.args.server, self.args.plugins,
                                       self.args.version,
                                       deps=self.args.resolve_dependencies)

        to_install = list()
        for plugin in plugins:
            if plugin['plugin_name'].lower() in self.args.ignored:
                self.p_sub("Ignoring {}", plugin['plugin_name'])
                continue
            if len(plugin['versions']) < 1:
                self.p_sub("Could not find any versions for {}",
                           plugin['plugin_name'])
                continue
            for i_plugin in installed:
                if i_plugin['slug'] == plugin['slug'] \
                        and not i_plugin['versions'][0]['version'] > \
                        plugin['versions'][0]['version']:
                    self.p_sub("{} is allready installed, and up to date",
                               plugin['plugin_name'])
                    break
            else:
                to_install.append(plugin)
        plugins = to_install

        if len(plugins) < 1:
            self.p_main('No plugins left to install')
            return

        self.p_main('Plugins to install:')
        self.p_blank()
        self.p_sub(common.list_names([p['plugin_name'] + '#'
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
        self.args.ignored = [e.lower() for e in self.args.ignored]

        self.p_main('Finding installed plugins')

        installed = backend.list_plugins()

        self.p_main('Looking up versions on BukGet')

        to_update = list()
        for i in installed:
            if i['plugin_name'].lower() in self.args.ignored:
                self.p_sub('Ignoring {}',
                           i['plugin_name'])
                continue
            n_version = utils.select_newest_version(i, self.args.version)
            if n_version is None:
                continue
            i_version = utils.select_installed_version(i)
            if n_version['version'] > i_version['version']:
                to_update.append(i)

        self.p_main('Plugins to update:')
        self.p_blank()

        if len(to_update) < 1:
            self.p_sub('All plugins are up to date!')
            self.p_sub(('Maybe you want a pre-release? Try passing --beta, '
                        '--alpha or even --latest as command options'))
            self.p_blank()
            return

        self.p_sub(common.list_names([p['plugin_name'] + '#'
                                      + p['versions'][0]['version']
                                      for p in to_update]))
        self.p_blank()

        if common.ask('Continue to update?', skip=self.args.no_confirm):
            prefix_format = '({{part:>{}}}/{{total}}) '.format(
                len(str(len(to_update))))
            for i in range(len(to_update)):
                plugin = to_update[i]
                os.remove(plugin['installed_file'])
                prefix = prefix_format.format(total=len(to_update), part=i+1)
                backend.download_plugin(plugin, prefix)
            self.p_blank()
            self.p_raw('Done!')

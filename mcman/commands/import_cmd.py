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

""" The import command of mcman.

This module is the home of the front end part of the command. This means that
as little as possible logic should go here.

"""

import json

import os
from sys import stdin

import mcman.logic.servers as s_backend
from mcman.logic.plugins import plugins as p_backend
from mcman.logic import common
from mcman.command import Command


class ImportCommand(Command):

    """ The import command of mcman. """

    def __init__(self, args):
        """ Parse command and execute tasks. """
        Command.__init__(self)
        self.args = args

        self.to_download = list()

        self.run()

    def run(self):
        """ Run the command. """
        if self.args.input is not stdin:
            self.p_main('Parsing file and finding plugins and servers')

        document = json.loads('\n'.join(self.args.input))

        plugins = document['plugins']
        remote_plugins = p_backend.find_versions(
            [(e['slug'], e['version-slug'])
             for e in plugins])

        servers = document['servers']
        remote_servers = s_backend.find_servers([e['id'] for e in servers])

        self.parse_plugins(plugins, remote_plugins)
        self.parse_servers(servers, remote_servers)

        self.p_main('Files to download:')
        self.p_blank()
        self.p_sub(common.list_names([i[0] for i in self.to_download]))
        self.p_blank()

        if not common.ask('Do you want to continue?',
                          skip=self.args.no_confirm):
            return

        prefix = '({{part:>{}}}/{}) '.format(
            len(str(len(self.to_download))), len(self.to_download))
        for i in range(len(self.to_download)):
            jar = self.to_download[i]
            this_prefix = prefix.format(part=i+1)
            destination = self.args.destination + '/' + jar[0]
            if jar[1].endswith('.zip'):
                destination = jar[1].split('/')[-1]
            common.download(jar[1], destination=destination, checksum=jar[2],
                            prefix=this_prefix)
            if jar[1].endswith('.zip'):
                print(' ' * len(this_prefix) + "Unzipping...", end=' ')
                p_backend.unzip_plugin(destination,
                                       '/'.join(jar[0].split('/')[:-1]) + '/')
                os.remove(destination)
                print('Success')

    def parse_plugins(self, plugins, remote_plugins):
        """ Populate the to_download list with plugins to download. """
        for plugin in plugins:
            r_plugin = None
            for _plugin in remote_plugins:
                if _plugin['slug'] == plugin['slug']:
                    r_plugin = _plugin
                    break
            else:
                continue

            version = r_plugin['versions'][0]
            self.to_download.append((plugin['file'], version['download'],
                                     version['md5']))

    def parse_servers(self, servers, remote_servers):
        """ Populate the to_download list with servers to download. """
        for server in servers:
            r_server = None
            for _server in remote_servers:
                if _server['id'] == server['id']:
                    r_server = _server
                    break
            else:
                continue

            self.to_download.append((server['file'], r_server['url'],
                                     r_server['checksum']))

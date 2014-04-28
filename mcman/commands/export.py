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

""" The export command of mcman.

This module is the home of the front end part of the command. This means that
as little as possible logic should go here.

"""

import json

import mcman.logic.servers as s_backend
from mcman.logic.plugins import plugins as p_backend
from mcman.logic.plugins import utils as p_utils
from mcman.logic import common
from mcman.command import Command


class ExportCommand(Command):

    """ The export command of mcman. """

    def __init__(self, args):
        """ Parse command and execute tasks. """
        Command.__init__(self)
        self.args = args

        args.types = args.types.split(',')

        if args.quiet:
            self.printer = lambda *a, **b: None

        self.run()

    def run(self):
        """ Run the command. """
        self.p_main('Saving {} to {}'.format(
            common.list_names(self.args.types), self.args.output.name))

        plugins = dict()
        servers = dict()

        if 'plugins' in self.args.types:
            self.p_main('Finding plugins')
            for plugin in p_backend.list_plugins():
                version = p_utils.select_installed_version(plugin)
                plugins[plugin['installed_file']] = (plugin['slug'],
                                                     version['slug'])
        if 'servers' in self.args.types:
            self.p_main('Finding servers')
            servers = s_backend.list_servers()

        self.p_main('Writing file')
        document = dict()
        document['servers'] = list()
        for file, key in servers.items():
            server = dict()
            server['id'] = key
            server['file'] = file

            document['servers'].append(server)

        document['plugins'] = list()
        for file, (slug, version) in plugins.items():
            plugin = dict()
            plugin['file'] = file
            plugin['slug'] = slug
            plugin['version-slug'] = version

            document['plugins'].append(plugin)

        self.args.output.write(json.dumps(document))
        self.args.output.write('\n')

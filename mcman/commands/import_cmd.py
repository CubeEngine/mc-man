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

import mcman.logic.servers as s_backend
from mcman.logic.plugins import plugins as p_backend
from mcman.logic.plugins import utils as p_utils
from mcman.logic import common
from mcman.command import Command


class ImportCommand(Command):

    """ The import command of mcman. """

    # TODO - Handle zipped plugins
    # TODO - Handle folders not created

    def __init__(self, args):
        """ Parse command and execute tasks. """
        Command.__init__(self)
        self.args = args

        self.run()

    def run(self):
        """ Run the command. """
        self.p_main('Parsing file and finding plugins and servers')
        document = json.loads('\n'.join(self.args.input))

        plugins = document['plugins']
        plugins2 = p_backend.find_versions([(e['slug'], e['version-slug'])
                                           for e in plugins])

        servers = document['servers']
        servers2 = s_backend.find_servers([e['id'] for e in servers])

        to_download = list()
        for plugin in plugins:
            r_plugin = None
            for _plugin in plugins2:
                if _plugin['slug'] == plugin['slug']:
                    r_plugin = _plugin
                    break
            else:
                continue

            version = r_plugin['versions'][0]
            to_download.append((plugin['file'], version['download'],
                                version['md5']))
        for server in servers:
            r_server = None
            for _server in servers2:
                if _server['id'] == server['id']:
                    r_server = _server
                    break
            else:
                continue

            to_download.append((server['file'], r_server['url'],
                                r_server['checksum']))

        self.p_main('Downloading servers and plugins')
        prefix = '({{part:>{}}}/{}) '.format(
            len(str(len(to_download))), len(to_download))
        for i in range(len(to_download)):
            jar = to_download[i]
            common.download(jar[1], destination=jar[0], checksum=jar[2],
                            prefix=prefix.format(part=i+1))

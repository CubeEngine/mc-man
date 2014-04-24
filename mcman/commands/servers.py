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

""" The server command of mcman. """

from urllib.error import URLError

from mcman.logic import servers as backend
from mcman.logic import common as utils
from mcman.command import Command


class ServersCommand(Command):

    """ The server command of mcman. """

    def __init__(self, args):
        """ Parse command, and execute tasks. """
        Command.__init__(self)

        self.args = args

        backend.init(args.base_url, args.user_agent)

        self.register_subcommand('servers', self.servers)
        self.register_subcommand('channels', self.channels)
        self.register_subcommand('versions', self.versions)
        self.register_subcommand('builds', self.builds)
        self.register_subcommand('identify', self.identify)
        self.register_subcommand('download', self.download)

        self.invoke_subcommand(args.subcommand, (ValueError, URLError))

    def error(self, error):
        """ Print error from SpaceGDN. """
        self.p_sub('Error from SpaceGDN: {}'.format(error['message']))

    def result(self, head, results):
        """ Print results with head. """
        self.p_main(head)
        self.p_blank()
        if type(results) is str:
            self.p_sub(results)
        elif len(results) >= 1:
            self.p_sub(utils.list_names(results))
        else:
            self.p_sub('No results...')
        self.p_blank()

    def servers(self):
        """ List available servers. """
        self.p_main('Fetching server list from SpaceGDN')

        jars = backend.jars()

        if type(jars) is not list:
            self.error(jars)
        else:
            self.result('Available servers:', jars)

    def channels(self):
        """ List available channels for a server. """
        self.p_main('Fetching channel list from SpaceGDN')

        try:
            channels = backend.channels(self.args.server)

            if type(channels) is not list:
                self.error(channels)
            else:
                self.result('Available channels:', channels)
        except ValueError as error:
            self.p_sub(error.args[0])

    def versions(self):
        """ List available versions of a server. """
        self.p_main('Fetching version list from SpaceGDN')

        try:
            versions = backend.versions(self.args.server, self.args.channel,
                                        self.args.size)

            if type(versions) is not list:
                self.error(versions)
            else:
                self.result('Available channels:', versions)
        except ValueError as error:
            self.p_sub(error.args[0])

    def builds(self):
        """ List available builds for a server. """
        self.p_main('Fetching build list from SpaceGDN')

        try:
            builds = backend.builds(self.args.server, self.args.channel,
                                    self.args.version, self.args.size)

            if type(builds) is not list:
                self.error(builds)
            else:
                self.result('Available builds:', builds)
        except ValueError as error:
            self.p_sub(error.args[0])

    def identify(self):
        """ Identify what server a jar file is. """
        self.p_main('Calculating checksum of `{}`'.format(self.args.jar.name))

        checksum = utils.checksum_file(self.args.jar)
        self.args.jar.close()

        self.p_main('Finding build on SpaceGDN')

        build = backend.build_by_checksum(checksum)

        if build is None:
            self.p_main('Found no build on SpaceGDN with matching checksum')
            return

        server, channel, version, build_num = backend.get_roots(build)

        self.p_main('Checking for updates in channel')

        new_version, new_build = backend.find_newest(server, channel)
        appendix = ''
        if new_build > build_num:
            appendix = ' -- Out of date. Newest build: {} {}'.format(
                new_version, new_build)

        self.result('Found build:', '{} {} {} {}'.format(server, channel,
                                                         version, build_num)
                                    + appendix)

    def download(self):
        """ Download a server. """
        self.p_main('Finding build on SpaceGDN')

        try:
            result = backend.get_builds(self.args.server, self.args.channel,
                                        self.args.version, self.args.build)

            if type(result) is not list:
                self.error(result)
                return

            if len(result) < 1:
                self.p_sub('Could not find any build')
                return

            channel, version, build = backend.find_latest_build(result)

            self.result('Found build:', '{} {} {} {}'.format(self.args.server,
                                                             channel, version,
                                                             build['build']))

            if utils.ask('Continue to download?', skip=self.args.no_confirm):
                utils.download(build['url'], destination=self.args.output,
                               checksum=build['checksum'], prefix=' '*4)
                self.p_blank()
                self.p_raw('Done!')
        except ValueError as error:
            self.p_sub(error.args[0])

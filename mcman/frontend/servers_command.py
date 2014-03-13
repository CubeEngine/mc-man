""" The server command of mcman. """

from urllib.error import URLError
from mcman.backend import servers as backend
from mcman.backend import common as utils
from mcman.frontend.common import Command, UknownSubcommandException


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

        try:
            self.invoke_subcommand(args.subcommand)
        except UknownSubcommandException as err:
            self.p_main('Could not find subcommand {}'.format(err.subcommand))
        except (ValueError, URLError) as err:
            self.p_sub('Error: {}'.format(str(err)))

    def error(self, error):
        """ Print error from SpaceGDN. """
        self.p_sub('Error from SpaceGDN: {}'.format(error['message']))

    def servers(self):
        """ List available servers. """
        self.p_main('Fetching server list from SpaceGDN')

        jars = backend.jars()

        if type(jars) is not list:
            self.error(jars)
        else:
            self.p_main('Available servers:')
            self.p_blank()
            self.p_sub(utils.list_names(jars))
            self.p_blank()

    def channels(self):
        """ List available channels for a server. """
        self.p_main('Fetching channel list from SpaceGDN')

        channels = backend.channels(self.args.server)

        if type(channels) is not list:
            self.error(channels)
        else:
            self.p_main('Available channels:')
            self.p_blank()
            self.p_sub(utils.list_names(channels))
            self.p_blank()

    def versions(self):
        """ List available versions of a server. """
        self.p_main('Fetching version list from SpaceGDN')

        versions = backend.versions(self.args.server, self.args.channel,
                                    self.args.size)

        if type(versions) is not list:
            self.error(versions)
        else:
            self.p_main('Available channels:')
            self.p_blank()
            if len(versions) < 1:
                self.p_sub('No results...')
            else:
                self.p_sub(utils.list_names(versions))
            self.p_blank()

    def builds(self):
        """ List available builds for a server. """
        self.p_main('Fetching build list from SpaceGDN')

        builds = backend.builds(self.args.server, self.args.channel,
                                self.args.version, self.args.size)
        if type(builds) is not list:
            self.error(builds)
        else:
            self.p_main('Available channels:')
            self.p_blank()
            if len(builds) < 1:
                self.p_sub('No results...')
            else:
                self.p_sub(utils.list_names(builds))
            self.p_blank()

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

        server, channel, version, build = backend.get_roots(build)

        self.p_main('Found build:')
        self.p_blank()
        self.p_sub('{} {} {} {}'.format(server, channel, version, build))
        self.p_blank()

    def download(self):
        """ Download a server. """
        self.p_main('Finding build on SpaceGDN')

        result = backend.get_builds(self.args.server, self.args.channel,
                                    self.args.version, self.args.build)

        if type(result) is not list:
            self.error(result)
            return

        if len(result) < 1:
            self.p_sub('Could not find any build')
            return

        channel, version, build = backend.find_latest_build(result)

        self.p_main('Found build:')
        self.p_blank()
        self.p_sub('{} {} {} {}'.format(self.args.server, channel,
                                        version, build['build']))
        self.p_blank()

        if utils.ask('Continue to download?', skip=self.args.no_confirm):
            utils.download(build['url'], destination=self.args.output,
                           checksum=build['checksum'], prefix=' '*4)
            self.p_blank()
            self.p_raw('Done!')

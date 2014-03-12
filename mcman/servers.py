""" mcman servers module. """

# Imports from the python library:
from urllib.error import URLError
# Imports from dependencies:
import spacegdn
# Imports from mcman:
from mcman.utils import list_names, download, ask, checksum_file


class Servers(object):

    """ The servers command for mcman. """

    prefix = ' :: '

    def __init__(self, args):
        """ Parse commands, and execute tasks. """
        self.args = args

        spacegdn.BASE = args.base_url
        spacegdn.USER_AGENT = args.user_agent

        try:
            if args.subcommand is 'servers':
                self.servers()
            elif args.subcommand is 'channels':
                self.channels()
            elif args.subcommand is 'versions':
                self.versions()
            elif args.subcommand is 'builds':
                self.builds()
            elif args.subcommand is 'download':
                self.download()
            elif args.subcommand is 'identify':
                self.identify()
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

    def prnt_result(self, result):
        """ Print result. """
        self.prnt('Results:')
        if len(result) > 0:
            self.prnt('    {}'.format(list_names(result)), filled_prefix=False)
        else:
            self.prnt('    No results...', filled_prefix=False)

    def servers(self):
        """ List servers. """
        self.prnt('Fetching server list from SpaceGDN')

        result = spacegdn.jars()

        if type(result) is not list:
            self.error(result)
            return

        self.prnt_result([jar['name'] for jar in result])

    def channels(self):
        """ List channels. """
        self.prnt('Fetching channel list from SpaceGDN')

        server = spacegdn.get_id(jar=self.args.server)
        result = spacegdn.channels(jar=server)

        if type(result) is not list:
            self.error(result)
            return

        self.prnt_result([channel['name'] for channel in result])

    def versions(self):
        """ List versions. """
        self.prnt('Fetching version list from SpaceGDN')

        server = spacegdn.get_id(jar=self.args.server)
        channel = None
        if self.args.channel is not None:
            channel = spacegdn.get_id(jar=server, channel=self.args.channel)
        result = spacegdn.versions(jar=server, channel=channel)

        if type(result) is not list:
            self.error(result)
            return

        # Sort and limit the results
        versions = list(reversed(sorted(
            [version['version'] for version in result])))
        if self.args.size >= 0:
            versions = versions[:min(self.args.size, len(versions))]
        else:
            versions = versions[max(self.args.size, -len(versions)):]

        self.prnt_result(versions)

    def builds(self):
        """ List builds. """
        self.prnt('Fetching build list from SpaceGDN')

        server = spacegdn.get_id(jar=self.args.server)
        channel = None
        if self.args.channel is not None:
            channel = spacegdn.get_id(jar=server, channel=self.args.channel)
        version = None
        if self.args.version is not None:
            version = spacegdn.get_id(jar=server, channel=self.args.channel,
                                      version=self.args.version)
        result = spacegdn.builds(jar=server, channel=channel,
                                 version=version)

        if type(result) is not list:
            self.error(result)
            return

        # Sort and limit the results
        names = list(reversed(sorted(
            [build['build'] for build in result])))
        if self.args.size >= 0:
            names = names[
                :min(self.args.size, len(names))]
        else:
            names = names[
                max(self.args.size, -len(names)):]

        self.prnt_result(names)

    def download(self):
        """ Download a server. """
        self.prnt('Finding build on SpaceGDN')

        server = spacegdn.get_id(jar=self.args.server)
        channel = None
        if self.args.channel is not None:
            channel = spacegdn.get_id(jar=server, channel=self.args.channel)
        version = None
        if self.args.version is not None:
            version = spacegdn.get_id(jar=server, channel=self.args.channel,
                                      version=self.args.version)
        build = None
        if self.args.build is not None:
            build = spacegdn.get_id(jar=server, channel=self.args.channel,
                                    version=self.args.version,
                                    build=self.args.build)
        result = spacegdn.builds(jar=server, channel=channel,
                                 version=version, build=build)

        if type(result) is not list:
            self.error(result)
            return

        if len(result) < 1:
            self.prnt('Could not find any build', filled_prefix=False)
            return

        # Sort the builds
        result.sort(key=lambda build: build['build'], reverse=True)
        build = result[0]
        # Find the name of the channel and version
        channel = spacegdn.channels(channel=build['channel_id'])[0]['name']
        version = spacegdn.versions(version=build['version_id'])[0]['version']

        self.prnt('Found build:')
        self.prnt('', False, False)
        self.prnt('{} {} {} {}'.format(self.args.server, channel,
                                       version, build['build']),
                  filled_prefix=False)
        self.prnt('', False, False)

        if ask('Continue to download?'):
            download(build['url'], file_name=self.args.output,
                     checksum=build['checksum'], prefix=' '*4)
            self.prnt('', False, False)
            self.prnt('Done!', prefix=False)

    def identify(self):
        """ Identify what server a jar is. """
        self.prnt('Calculating checksum of `{}`'.format(self.args.jar.name))

        checksum = checksum_file(self.args.jar)
        self.args.jar.close()

        self.prnt('Finding build on SpaceGDN')

        builds = spacegdn.builds(where='build.checksum.eq.{}'.format(checksum))

        if len(builds) < 1:
            self.prnt('Found no build on SpaceGDN with matching checksum')
            return

        build = builds[0]
        server = spacegdn.jars(build['jar_id'])[0]['name']
        channel = spacegdn.channels(build['jar_id'],
                                    build['channel_id'])[0]['name']
        version = spacegdn.versions(build['jar_id'], build['channel_id'],
                                    build['version_id'])[0]['version']
        build = build['build']

        self.prnt('Found build:')
        self.prnt('', False, False)
        self.prnt('{} {} {} {}'.format(server, channel, version, build),
                  filled_prefix=False)
        self.prnt('', False, False)

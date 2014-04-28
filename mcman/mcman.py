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

""" mcman main module. """

import argparse
import sys

import mcman
from mcman.commands.plugins import PluginsCommand
from mcman.commands.servers import ServersCommand
from mcman.commands.import_cmd import ImportCommand
from mcman.commands.export import ExportCommand


def negative(argument):
    """ Turn a number negative. """
    return -abs(int(argument))


def setup_import_command(sub_parsers, parent):
    """ Setup the command for import. """
    # The server command parser
    parser = sub_parsers.add_parser(
        'import', aliases=['i'],
        help='import a server',
        description='Import a server - Its server jars and plugins',
        parents=[parent])
    parser.set_defaults(command=ImportCommand)

    parser.add_argument(
        'input', type=argparse.FileType('r'), default=sys.stdin,
        help=('the json file contating the server and plugin information. '
              '"-" may be used to mark stdin'))

    parser.add_argument(
        'destination', default='./', nargs='?',
        help='the destination folder. defaults to ./')

    return parser


def setup_export_command(sub_parsers, parent):
    """ Setup the command for export. """
    # The server command parser
    parser = sub_parsers.add_parser(
        'export', aliases=['e'],
        help='export the server',
        description='Export the server - Its server jars and plugins',
        parents=[parent])
    parser.set_defaults(command=ExportCommand)

    parser.add_argument(
        'output', type=argparse.FileType('w'),
        default=sys.stdout,
        help='the file to output the json to. "-" may be used to mark stdout')

    parser.add_argument(
        '--types', default='plugins,servers',
        help='what to save. A comma separated list of "servers" and "plugins"')

    parser.add_argument(
        '--quiet', action='store_true',
        help="don't print anything other than the result")

    return parser


def setup_server_commands(sub_parsers, parent):
    """ Setup the commands and subcommands for server. """
    # The parent parser for server and it's sub commands
    sub_parent = argparse.ArgumentParser(add_help=False, parents=[parent])

    # Base URL
    sub_parent.add_argument(
        '--base-url', metavar='base-url',
        default='http://spacegdn.totokaka.io/v1/',
        help='the base URL to use for SpaceGDN')

    # The server command parser
    parser = sub_parsers.add_parser(
        'server', aliases=['s'],
        help='manage server jars',
        description='Download, identify and list Minecraft server jars.',
        parents=[sub_parent])
    parser.set_defaults(command=ServersCommand)
    # The server sub commands
    sub_parsers = parser.add_subparsers(title='subcommands')
    # servers, sub command of server
    servers_parser = sub_parsers.add_parser(
        'servers', aliases=['s'],
        help='list available servers',
        description='List all server jars available for download.',
        parents=[sub_parent])
    servers_parser.set_defaults(subcommand='servers')
    # channels, sub command of server
    channels_parser = sub_parsers.add_parser(
        'channels', aliases=['c'],
        help='list channels for the specified server',
        description='List all available channels for the server specified.',
        parents=[sub_parent])
    channels_parser.set_defaults(subcommand='channels')
    channels_parser.add_argument(
        'server', help='the server to get channels for')
    # versions, sub command of server
    versions_parser = sub_parsers.add_parser(
        'versions', aliases=['v'],
        help='list versions for the specified server',
        description='List all available versions for the server specified, '
                    + 'or only the versions in the specified channel.',
        parents=[sub_parent])
    versions_parser.set_defaults(subcommand='versions')
    versions_parser.add_argument(
        'server', help='the server to get versions for')
    versions_parser.add_argument(
        'channel', nargs='?', help='the channel to get versions for')
    # builds, sub command of server
    builds_parser = sub_parsers.add_parser(
        'builds', aliases=['b'],
        help='list builds for the specified server',
        description='List all available builds for the server specified, '
                    + 'or only the ones in the specified channel, or version',
        parents=[sub_parent])
    builds_parser.set_defaults(subcommand='builds')
    builds_parser.add_argument(
        'server', help='the server to get builds for')
    builds_parser.add_argument(
        'channel', nargs='?', help='the channel to get builds for')
    builds_parser.add_argument(
        'version', nargs='?', help='the version to get builds for')
    # download, sub command of server
    download_parser = sub_parsers.add_parser(
        'download', aliases=['d'],
        help='download the newest version of the server',
        description='Download the newest, the newest in the channel, or the '
                    + 'specified version of the jar.',
        parents=[sub_parent])
    download_parser.set_defaults(subcommand='download')
    download_parser.add_argument(
        'server', help='the server to download')
    download_parser.add_argument(
        'channel', nargs='?', help='the channel to dowload from')
    download_parser.add_argument(
        'version', nargs='?', help='the specific version to download')
    download_parser.add_argument(
        'build', nargs='?', help='the specific build to download')
    download_parser.add_argument(
        '-o', '--output', help='filename to download to')
    # identify, sub command of server
    identify_parser = sub_parsers.add_parser(
        'identify', aliases=['i'],
        help='identify the server and version of the jar file',
        description='Identifies the server, version and possibly channel of '
                    + 'the jar file specified.',
        parents=[sub_parent])
    identify_parser.set_defaults(subcommand='identify')
    identify_parser.add_argument(
        'jar', type=argparse.FileType('rb', 0),
        help='the jar file to identify')

    return parser


def setup_plugin_commands(sub_parsers, parent):
    """ Setup the commands and subcommands for plugin. """
    # The parent parser for plugin and it's sub commands
    sub_parent = argparse.ArgumentParser(add_help=False, parents=[parent])

    # Base URL
    sub_parent.add_argument(
        '--base-url', default='http://api.bukget.org/3/',
        help='the base URL to use for BukGet')
    sub_parent.add_argument(
        '--server', default='bukkit',
        help='the server to get plugins for. This is sent to BukGet, '
             + 'and will affect what plugins you can download')
    sub_parent.add_argument(
        '--beta', action='store_const', dest='version', const='beta',
        help="find latest beta version, instead of latest release for "
             + "plugins where a version isn't specified.")
    sub_parent.add_argument(
        '--alpha', action='store_const', dest='version', const='alpha',
        help="find latest alpha version, instead of latest release for "
             + "plugins where a version isn't specified.")
    sub_parent.add_argument(
        '--latest', action='store_const', dest='version', const='latest',
        help="find latest version, no matter type, instead of latest release "
             + "for plugins where a version isn't specified.")
    sub_parent.add_argument(
        '--no-resolve-dependencies', action='store_false',
        dest='resolve_dependencies', help='do not resolve dependencies')
    sub_parent.set_defaults(version='release')

    # The plugin command parser
    parser = sub_parsers.add_parser(
        'plugin', aliases=['p'],
        help='manage plugins',
        description='Find, download and update plugins.',
        parents=[sub_parent])
    parser.set_defaults(command=PluginsCommand)

    # The plugin sub commands
    sub_parsers = parser.add_subparsers(title='subcommands')
    # search, sub command of plugin
    search_parser = sub_parsers.add_parser(
        'search', aliases=['s'],
        help='search for a plugin',
        description='Search for a plugin using partial matching of the name.',
        parents=[sub_parent])
    search_parser.set_defaults(subcommand='search')
    search_parser.add_argument(
        'query', help='search query')
    # info, sub command of plugin
    info_parser = sub_parsers.add_parser(
        'info', aliases=['i'],
        help='get info about a plugin(s)',
        description='Get info about one, or more plugins.',
        parents=[sub_parent])
    info_parser.set_defaults(subcommand='info')
    info_parser.add_argument(
        'plugins', metavar='plugin', type=str,
        help='plugin(s) to get info for')
    # download, sub command of plugin
    download_parser = sub_parsers.add_parser(
        'download', aliases=['d'],
        help='download a plugin(s)',
        description='Download the specified plugin(s). A version can be '
                    + 'specified by appending "#<version>" to the plugin name',
        parents=[sub_parent])
    download_parser.set_defaults(subcommand='download')
    download_parser.add_argument(
        'plugins', metavar='plugin', type=str, nargs='+',
        help='plugin(s) to download, and extract if they are zipped')
    download_parser.add_argument(
        '--ignore', metavar='plugin', type=str, nargs='+', dest='ignored',
        help='plugin(s) to ignore')
    # update, sub command of plugin
    update_parser = sub_parsers.add_parser(
        'update', aliases=['u'],
        help='update a plugin(s)',
        description='Update the specified plugins, or all.',
        parents=[sub_parent])
    update_parser.set_defaults(subcommand='update')
    update_parser.add_argument(
        'plugins', metavar='plugin', type=str, nargs='*',
        help='plugin(s) update')
    update_parser.add_argument(
        '--ignore', metavar='plugin', type=str, nargs='+', dest='ignored',
        help='plugin(s) to ignore')
    # list, sub command of plugin
    list_parser = sub_parsers.add_parser(
        'list', aliases=['l'],
        help='list installed plugins',
        description='List installed plugins, their versions, and the newest '
                    + 'version.',
        parents=[sub_parent])
    list_parser.set_defaults(subcommand='list')

    return parser


def setup_parse_command():
    """ Setup commands, and parse them. """
    # Parent parser
    parent = argparse.ArgumentParser(add_help=False)

    # Commands that can be used for all sub commands
    parent.add_argument(
        '--version',
        help='show the version of mcman, then quit',
        action='store_true', dest='show_version')
    parent.add_argument(
        '--user-agent',
        metavar='agent',
        type=str,
        default='mcman ' + mcman.__version__,
        help='alternative user agent to report to BukGet and SpaceGDN')
    # Head and tail, they are mutually exclusive
    group = parent.add_mutually_exclusive_group()
    group.add_argument(
        '--head', '--size',
        metavar='size',
        type=int,
        dest='size',
        nargs='?',
        default=10,
        const=5,
        help='how many entries that should be displayed, from the top')
    group.add_argument(
        '--tail',
        metavar='size',
        type=negative,
        dest='size',
        nargs='?',
        default=10,
        const=-5,
        help='how many entries that should be displayed, from the bottom')
    parent.add_argument(
        '--no-confirm',
        action='store_true',
        help='do not wait for confirmation, just continue')

    # The top level command
    parser = argparse.ArgumentParser(
        description='Manage Minecraft server jars and plugins',
        epilog='Powered by BukGet and SpaceGDN',
        parents=[parent])

    # The sub commands, plugin and server
    sub_parsers = parser.add_subparsers(title='subcommands')

    server_parser = setup_server_commands(sub_parsers, parent)
    plugin_parser = setup_plugin_commands(sub_parsers, parent)

    setup_import_command(sub_parsers, parent)
    setup_export_command(sub_parsers, parent)

    return server_parser, plugin_parser, parser


def main():
    """ Main function. """
    server_parser, plugin_parser, parser = setup_parse_command()

    args = parser.parse_args()

    if args.show_version:
        print('Version: {}'.format(mcman.__version__))
    elif 'command' not in args:
        parser.print_help()
    elif 'subcommand' not in args and not (args.command == ExportCommand
                                           or args.command == ImportCommand):
        if args.command is PluginsCommand:
            plugin_parser.print_help()
        elif args.command is ServersCommand:
            server_parser.print_help()
    else:
        if 'ignored' in args and args.ignored is None:
            args.ignored = []

        try:
            args.command(args)
        except KeyboardInterrupt:
            print()
            return

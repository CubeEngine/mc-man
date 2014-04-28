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

""" The backend for the mcman servers command. """

import os

import spacegdn

from mcman.logic import common


def init(base, user_agent):
    """ Initialize this module.

    This function will just set the base url and user agent for SpaceGDN.

    """
    spacegdn.BASE = base
    spacegdn.USER_AGENT = user_agent


def jars():
    """ List jars.

    A list of the jar names is returned if the query was successful, else the
    error dictionary from SpaceGDN is returned.

    """
    result = spacegdn.jars()

    if type(result) is not list:
        return result

    return [jar['name'] for jar in result]


def channels(server):
    """ List channels.

    A list of the channel names is returned if the query was successful, else
    the error dictionary from SpaceGDN is returned.

    """
    server = spacegdn.get_id(jar=server)
    if server == -1:
        raise ValueError('Could not find server')
    result = spacegdn.channels(jar=server)

    if type(result) is not list:
        return result

    return [channel['name'] for channel in result]


def versions(server, channel, size):
    """ List versions.

    A list of the version names is returned if the query was successful, else
    the error dictionary from SpaceGDN is returned.

    """
    server = spacegdn.get_id(jar=server)
    if server == -1:
        raise ValueError('Could not find server')
    if channel is not None:
        channel = spacegdn.get_id(jar=server, channel=channel)
        if channel == -1:
            raise ValueError('Could not find channel')
    result = spacegdn.versions(jar=server, channel=channel)

    if type(result) is not list:
        return result

    # Sort and limit the results
    result = list(reversed(sorted([version['version'] for version
                                   in result])))
    if size >= 0:
        result = result[:min(size, len(result))]
    else:
        result = result[max(size, -len(result)):]

    return result


def builds(server, channel, version, size):
    """ List builds.

    A list of the build numbers is returned if the query was successful, else
    the error dictionary from SpaceGDN is returned.

    """
    result = get_builds(server, channel, version, None)

    if type(result) is not list:
        return result

    # Sort and limit the results
    result = list(reversed(sorted([str(build['build']) for build
                                   in result])))
    if size >= 0:
        result = result[:min(size, len(result))]
    else:
        result = result[max(size, -len(result)):]

    return result


def get_id_raise_valueerror(name, jar=None, channel=None, version=None,
                            build=None):
    result = spacegdn.get_id(jar=jar, channel=channel, version=version,
                             build=build)
    if result == -1:
        raise ValueError('Could not find {}'.format(name))
    return result


def get_builds(server, channel, version, build):
    """ Get the build.

    Any argument might be None.

    A list of matching builds is returned on success, or the error dictionary
    as returned by SpaceGDN.

    """
    server = get_id_raise_valueerror('server', server)
    if channel is not None:
        channel = get_id_raise_valueerror('channel', server, channel)
    if version is not None:
        version = get_id_raise_valueerror('version', server, channel, version)
    if build is not None:
        build = get_id_raise_valueerror('build', server, channel, version,
                                        build)

    return spacegdn.builds(jar=server, channel=channel,
                           version=version, build=build)


def build_by_checksum(checksum):
    """ Find build by checksum.

    None is returned if the build was not found.

    """
    result = spacegdn.builds(where='build.checksum.eq.{}'.format(checksum))
    if len(result) < 1:
        return None
    return result[0]


def get_roots(build):
    """ Get the roots(server, channel, version and build) of this build.

    The returned value is a tuple of the server name, channel name, version
    name and build number.

    """
    server = spacegdn.jars(build['jar_id'])[0]['name']
    channel = spacegdn.channels(build['jar_id'],
                                build['channel_id'])[0]['name']
    version = spacegdn.versions(build['jar_id'], build['channel_id'],
                                build['version_id'])[0]['version']
    build = build['build']

    return server, channel, version, build


def find_latest_build(build_list):
    """ Find the latest build in a list of builds. """
    build_list.sort(key=lambda build: build['build'], reverse=True)
    build = build_list[0]

    channel = spacegdn.channels(channel=build['channel_id'])[0]['name']
    version = spacegdn.versions(version=build['version_id'])[0]['version']

    return channel, version, build


def find_newest(server, channel):
    """ Find the newest version and build in a channel.

    Returns a tuple with the version name and build number.

    """
    channel_id = spacegdn.get_id(jar=server, channel=channel)
    result = spacegdn.builds(channel=channel_id)

    channel, version, build = find_latest_build(result)

    return version, build['build']


def list_servers():
    """ List servers in the current dir.

    Returned is a dictionary from jar file(relative path) to id

    """
    files = dict()

    for file in os.listdir():
        if not file.endswith('.jar'):
            continue
        checksum = common.checksum_file(file)
        build = build_by_checksum(checksum)
        if build is not None:
            files[file] = build['id']

    return files


def find_servers(servers):
    """ Get builds by ids. """
    build_list = list()
    for build in servers:
        results = spacegdn.builds(build=build)
        if len(results) > 0:
            build_list.append(results[0])
    return build_list
